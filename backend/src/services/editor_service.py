import json
from typing import Any, Dict, List, Optional

from flask import current_app

from agents.models import AgentType
from agents.prompts.editor_prompts import ARTICLE_SECTION_PROMPT, ARTICLE_SPLIT_PROMPT
from services.base_ai_service import BaseAIService


class EditorService(BaseAIService):
    """
    Service for editing and splitting long articles into a series.
    Also, edits articles to improve readability and engagement.
    """

    def __init__(self) -> None:
        super().__init__(AgentType.EDITOR)

    async def process_long_article(
        self,
        title: str,
        content: str,
        sources: Optional[str] = None,
        num_parts: int = 3,
    ) -> Dict[str, Any]:
        """
        Process a long article into multiple shorter articles.
        """
        try:
            # Get article structure
            structure = await self._get_article_structure(content, num_parts)

            # Process each article in the series
            processed_articles: List[Dict[str, Any]] = []
            for article_data in structure["articles"]:
                # Build "other articles" context by excluding current one
                other_articles = [
                    {k: v for k, v in a.items() if k not in ("ai_summary", "sections")}
                    for a in structure["articles"]
                    if a["title"] != article_data["title"]
                ]

                # Generate introduction & conclusion
                processed_content = await self._process_article_content(
                    series_title=title,
                    full_content=content,
                    article_data=article_data,
                    other_articles=other_articles,
                )

                processed_articles.append(
                    {
                        "title": article_data["title"],
                        "content": processed_content,
                        "excerpt": article_data["excerpt"],
                        "ai_summary": article_data["ai_summary"],
                    }
                )

            # Add sources if provided
            if sources and processed_articles:
                # Add to last article
                processed_articles[-1]["content"] += f"\n\n## Sources\n{sources}"

                # Optionally add a note in earlier articles referencing the last one
                last_title = processed_articles[-1]["title"]
                for i in range(len(processed_articles) - 1):
                    processed_articles[i]["content"] += (
                        "\n\n---\n*The sources consulted for this article series can be "
                        f"found in [{last_title}].*"
                    )

            return {"articles": processed_articles}

        except Exception as e:
            current_app.logger.error(f"Error processing article series: {e}")
            raise

    async def _get_article_structure(
        self, content: str, num_parts: int
    ) -> Dict[str, Any]:
        """
        Split a long article into a series of shorter articles. Returns the structure.
        """

        prompt_text = ARTICLE_SPLIT_PROMPT.format(content=content, num_parts=num_parts)

        try:
            structure_json = await self.generate_content(
                prompt=prompt_text, message_history=[]
            )
            if not structure_json:
                raise ValueError("Empty response from structure generation")

            # Parse JSON
            articles_data = json.loads(structure_json)

            if not isinstance(articles_data, list):
                raise ValueError("Invalid structure format: expected a JSON array")

            return {"articles": articles_data}

        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse structure response: {e}")
            raise ValueError("Invalid structure response format")
        except Exception as e:
            current_app.logger.error(f"Error generating article structure: {e}")
            raise

    async def _process_article_content(
        self,
        series_title: str,
        full_content: str,
        article_data: Dict[str, Any],
        other_articles: List[Dict[str, Any]],
    ) -> str:
        """
        Generate an introduction and conclusion that make this piece a standalone article.
        Returns the final markdown content for that piece.
        """
        # Collect relevant sections from the full content
        title = article_data["title"]
        excerpt = article_data["excerpt"]
        section_text = EditorService._extract_relevant_sections(
            full_content, article_data["sections"]
        )

        # Build the prompt
        prompt_text = ARTICLE_SECTION_PROMPT.format(
            series_title=series_title,
            excerpt=excerpt,
            title=title,
            section_text=section_text,
            other_articles=json.dumps(other_articles),
        )

        # Call the AI
        try:
            response_text = await self.generate_content(
                prompt=prompt_text, message_history=[]
            )
            if not response_text:
                raise ValueError("Empty response from content generation")

            # Extract introduction and conclusion from the JSON-like response
            intro_text, conclusion_text = EditorService._extract_intro_and_conclusion(
                response_text
            )

            # Combine everything
            final_article = (
                "## Introduction\n\n"
                + intro_text
                + "\n\n"
                + section_text
                + "\n\n## Conclusion\n\n"
                + conclusion_text
            )
            return final_article

        except Exception as e:
            current_app.logger.error(f"Error generating article content: {e}")
            raise

    @staticmethod
    def _extract_relevant_sections(full_text: str, sections: List[str]) -> str:
        """
        Extract the relevant section text from the original content, ignoring 'Introduction'/'Conclusion'.
        """
        content_accum = ""
        for section in sections:
            if section in ["Introduction", "Conclusion"]:
                continue

            # Try both "## " and "### "
            patterns = [f"## {section}", f"### {section}"]
            start_idx = -1
            for pat in patterns:
                idx = full_text.find(pat)
                if idx != -1:
                    start_idx = idx
                    break

            if start_idx != -1:
                # Find the next major "## " heading or end-of-content
                next_section_idx = full_text.find("\n## ", start_idx + 1)
                end_idx = next_section_idx if next_section_idx != -1 else len(full_text)
                content_accum += full_text[start_idx:end_idx].strip() + "\n\n"

        return content_accum.strip()

    @staticmethod
    def _extract_intro_and_conclusion(raw_response: str) -> tuple[str, str]:
        """Extract introduction and conclusion from JSON response."""
        data = json.loads(raw_response)
        return data["introduction"].strip(), data["conclusion"].strip()
