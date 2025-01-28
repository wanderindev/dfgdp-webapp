import json
import re
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app

from agents.models import AgentType
from agents.prompts.editor_prompts import (
    ARTICLE_SECTION_PROMPT,
    ARTICLE_SPLIT_PROMPT,
    IMPROVE_READABILITY_INITIAL_PROMPT,
    IMPROVE_READABILITY_CONTINUATION_PROMPT,
)
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
        # Find the index of the double quotes
        quote_positions = [m.start() for m in re.finditer('"', raw_response)]

        # Extract the introduction and conclusion
        introduction = raw_response[quote_positions[2] + 1 : quote_positions[3]]
        conclusion = raw_response[quote_positions[6] + 1 : quote_positions[7]]

        return introduction, conclusion

    async def improve_readability(self, article_content: str) -> str:
        """
        Proofread the given article content to improve readability. Specifically:
         - Reduce excessive passive voice
         - Fix common punctuation errors
         - Improve sentence structure to increase readability
        """

        # Break the article into chunks (paragraphs vs. headings/lists/etc.)
        chunks = EditorService._parse_markdown_chunks(article_content)

        prompt = None
        message_history = []

        # Iterate over chunks, sending paragraph chunks to the AI for improvement
        improved_chunks: List[str] = []
        for chunk_text, chunk_type in chunks:
            if chunk_type == "paragraph":
                if prompt is None:
                    # Create the initial prompt
                    prompt = IMPROVE_READABILITY_INITIAL_PROMPT.format(
                        chunk_text=chunk_text
                    )
                else:
                    prompt = IMPROVE_READABILITY_CONTINUATION_PROMPT.format(
                        chunk_text=chunk_text
                    )

                # Generate the improved paragraph
                improved_paragraph = await self.generate_content(
                    prompt=prompt, message_history=message_history
                )

                # Update the message history with the last iteration
                message_history.append({"role": "user", "content": prompt})
                message_history.append(
                    {"role": "assistant", "content": improved_paragraph}
                )

                # Save the improved paragraph
                improved_chunks.append(improved_paragraph.strip())
            else:
                # For headings, bullet points, etc., just keep them as is
                improved_chunks.append(chunk_text)

        # Reassemble everything into one final string
        improved_article = "\n\n".join(improved_chunks)

        return improved_article

    @staticmethod
    def _parse_markdown_chunks(content: str) -> List[Tuple[str, str]]:
        """
        Splits the article into a list of (chunk_text, chunk_type).
        chunk_type can be 'paragraph', 'heading', 'list', or 'other'.

        The goal is to only run AI proofreading on normal paragraphs, and skip
        headings (##, ###), bullet lists (*, -), numeric lists, code blocks, etc.
        """
        lines = content.split("\n")
        chunks: List[Tuple[str, str]] = []

        current_paragraph = []

        def flush_paragraph():
            """Helper to flush any accumulated paragraph lines into chunks."""
            if current_paragraph:
                paragraph_text = "\n".join(current_paragraph).strip()
                if paragraph_text:
                    chunks.append((paragraph_text, "paragraph"))
                current_paragraph.clear()

        for line in lines:
            stripped = line.strip()

            # Check for headings
            if stripped.startswith("#"):
                # Flush any paragraph we accumulated so far
                flush_paragraph()
                # This line is a heading
                chunks.append((line, "heading"))
            # Check for bulleted or numbered lists
            elif re.match(r"^(\*|-|\d+\.)\s", stripped):
                # Flush any paragraph we accumulated so far
                flush_paragraph()
                # This line is a list item
                chunks.append((line, "list"))
            # Check for code block fences (``` or ~~~)
            elif stripped.startswith("```") or stripped.startswith("~~~"):
                # Flush any paragraph we accumulated so far
                flush_paragraph()
                # We'll treat these lines as 'other' so we don't transform them
                chunks.append((line, "other"))
            else:
                # It's presumably a normal text line, accumulate for paragraph
                # If the line is empty, flush the paragraph
                if not stripped:
                    flush_paragraph()
                else:
                    current_paragraph.append(line)

        # Flush any leftover paragraph at the end
        flush_paragraph()

        return chunks
