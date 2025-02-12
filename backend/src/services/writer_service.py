import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import current_app
from sqlalchemy.exc import IntegrityError

from agents.models import AgentType
from agents.prompts.writer_prompts import (
    LONG_ARTICLE_CONTINUATION_PROMPT,
    EXCERPT_PROMPT,
    LONG_ARTICLE_SUBSECTION_PROMPT,
    SUMMARY_PROMPT,
    WRITE_LONG_ARTICLE_PROMPT,
    SOURCES_CLEANUP_PROMPT,
    SHORT_BIO_PROMPT,
    SHORT_SITE_PROMPT,
)
from content.models import Article, Research, ArticleSuggestion, Category, ContentStatus
from extensions import db
from services.base_ai_service import BaseAIService
from services.editor_service import EditorService


class WriterService(BaseAIService):
    """
    Service for generating articles from research using AI.
    Inherits from BaseAIService to automatically load the WRITER agent & client.
    """

    def __init__(self) -> None:
        super().__init__(AgentType.WRITER)

    async def generate_article(self, research_id: int) -> Union[Article, List[Article]]:
        """
        Generate one or more articles based on research content.
        """

        research: Optional[Research] = db.session.query(Research).get(research_id)
        if not research:
            raise ValueError(f"Research {research_id} not found")

        if research.status != ContentStatus.APPROVED:
            raise ValueError(f"Research {research_id} is not approved")

        suggestion: Optional[ArticleSuggestion] = research.suggestion
        if not suggestion:
            raise ValueError(f"No suggestion found for research {research_id}")

        category: Optional[Category] = suggestion.category
        if not category:
            raise ValueError(f"No category found for suggestion {suggestion.id}")

        taxonomy = category.taxonomy.name

        try:
            if taxonomy in ["Notable Figures", "Sites & Landmarks"]:
                # short-form path
                return await self._generate_short_form_article(
                    research=research, suggestion=suggestion, category=category
                )
            else:
                # long-form path
                return await self._generate_long_form_article(
                    research=research, suggestion=suggestion, category=category
                )

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generating article: {e}")
            raise

    async def _generate_long_form_article(
        self, research: Research, suggestion: ArticleSuggestion, category: Category
    ) -> Union[Article, List[Article]]:
        """
        Multistep approach for generating articles.
        """

        generation_started_at = datetime.now(timezone.utc)
        message_history: List[Dict[str, str]] = []

        template_vars = {
            "context": {
                "taxonomy": category.taxonomy.name,
                "taxonomy_description": category.taxonomy.description,
                "category": category.name,
                "category_description": category.description,
            },
            "title": suggestion.title,
            "research_content": research.content,
        }

        # -- Step 1: Generate Outline --
        initial_prompt = WRITE_LONG_ARTICLE_PROMPT.format(**template_vars)

        outline = await self._generate_ai_section(
            prompt=initial_prompt,
            message_history=[],
        )
        if not outline:
            raise ValueError("Empty outline response from AI")

        message_history.append({"role": "user", "content": initial_prompt})
        message_history.append({"role": "assistant", "content": outline})

        # -- Step 2: Extract sections from outline & generate each
        sections = WriterService._extract_sections_from_outline(outline)
        sections_content: List[str] = []

        for section_title, subsections in sections:
            continuation_prompt = LONG_ARTICLE_CONTINUATION_PROMPT.format(
                section_title=section_title
            )
            if subsections:
                continuation_prompt += LONG_ARTICLE_SUBSECTION_PROMPT.format(
                    subsections=", ".join(subsections)
                )

            section_text = await self._generate_ai_section(
                prompt=continuation_prompt,
                message_history=message_history,
            )
            if not section_text:
                raise ValueError(f"Empty response for section: {section_title}")

            sections_content.append(section_text)

            # Update the message history with the last iteration
            message_history.append({"role": "user", "content": continuation_prompt})
            message_history.append({"role": "assistant", "content": section_text})

        # Step 3: Handle sources from research
        sources_section = WriterService._extract_sources_section(research.content)

        if sources_section:
            cleaned_sources = await self._clean_sources_section(sources_section)
        else:
            cleaned_sources = {"content": ""}

        # Combine
        complete_content = "\n\n".join(sections_content)
        word_count = len(complete_content.split())

        # Step 4: Single or multipart
        if word_count > 3600:
            return await self._create_article_series(
                research_id=research.id,
                category_id=category.id,
                suggestion=suggestion,
                complete_content=complete_content,
                cleaned_sources=cleaned_sources,
                generation_started_at=generation_started_at,
            )
        else:
            return await self._create_single_article(
                research_id=research.id,
                category_id=category.id,
                suggestion=suggestion,
                complete_content=complete_content,
                cleaned_sources=cleaned_sources,
                generation_started_at=generation_started_at,
            )

    async def _generate_short_form_article(
        self, research: Research, suggestion: ArticleSuggestion, category: Category
    ) -> Union[Article, List[Article]]:
        """
        Generate a short-form article (one shot) for:
         - Notable Figures
         - Sites & Landmarks
        """

        generation_started_at = datetime.now(timezone.utc)
        message_history: List[Dict[str, str]] = []

        # Choose which short prompt to use
        if category.taxonomy.name == "Notable Figures":
            short_prompt_template = SHORT_BIO_PROMPT
        else:
            # Sites & Landmarks
            short_prompt_template = SHORT_SITE_PROMPT

        # Fill in the prompt
        prompt_vars = {
            "taxonomy": category.taxonomy.name,
            "taxonomy_description": category.taxonomy.description,
            "category": category.name,
            "category_description": category.description,
            "title": suggestion.title,
            "research_content": research.content,
        }
        short_prompt = short_prompt_template.format(**prompt_vars)

        # Generate the entire article in one shot
        short_article_content = await self._generate_ai_section(
            prompt=short_prompt,
            message_history=message_history,
        )
        if not short_article_content:
            raise ValueError("Empty response from short-form article generation")

        # Clean or handle sources from the research
        sources_section = WriterService._extract_sources_section(research.content)

        if sources_section:
            cleaned_sources = await self._clean_sources_section(sources_section)
        else:
            cleaned_sources = {"content": ""}

        # Combine final content
        complete_content = short_article_content

        return await self._create_single_article(
            research_id=research.id,
            category_id=category.id,
            suggestion=suggestion,
            complete_content=complete_content,
            cleaned_sources=cleaned_sources,
            generation_started_at=generation_started_at,
        )

    async def _generate_ai_section(
        self,
        prompt: str,
        message_history: List[Dict[str, str]],
    ) -> str:
        """
        Helper to call the base class's generate_content(...) for a single step in the conversation.
        """
        content = await self.generate_content(
            prompt=prompt, message_history=message_history
        )
        return content

    @staticmethod
    def _extract_sections_from_outline(outline: str) -> List[Tuple[str, List[str]]]:
        """
        Parse the AI-generated outline to get a list of (section_title, [subsections]).
        """
        sections: List[Tuple[str, List[str]]] = []
        current_section: Optional[str] = None
        current_subsections: List[str] = []

        for line in outline.split("\n"):
            if line.startswith("## "):
                # store the previous section first
                if current_section:
                    sections.append((current_section, current_subsections))
                current_section = line[3:].strip()
                current_subsections = []
            elif line.startswith("### ") and current_section:
                current_subsections.append(line[4:].strip())

        if current_section:
            sections.append((current_section, current_subsections))

        return sections

    @staticmethod
    def _extract_sources_section(research_content: str) -> Optional[str]:
        """
        Extract a "Sources" or "Further Reading" section from the research content if present.
        """
        pattern = r"## Sources and Further Reading\n([\s\S]*$)"
        match = re.search(pattern, research_content, re.DOTALL)
        return match.group(1).strip() if match else None

    async def _clean_sources_section(self, sources: str) -> Dict[str, str]:
        """
        Calls an AI prompt to clean or format the sources section.
        If it fails, returns original sources.
        """
        try:
            prompt_text = SOURCES_CLEANUP_PROMPT.format(sources=sources)
            cleaned_text = await self.generate_content(
                prompt=prompt_text, message_history=[]
            )

            if not cleaned_text:
                raise ValueError("Empty response from sources cleanup")

            return {"content": cleaned_text}
        except Exception as e:
            current_app.logger.error(f"Error cleaning sources: {e}")
            return {"content": sources}

    # noinspection PyArgumentList
    async def _create_single_article(
        self,
        research_id: int,
        category_id: int,
        suggestion: ArticleSuggestion,
        complete_content: str,
        cleaned_sources: Dict[str, str],
        generation_started_at: datetime,
    ) -> Article:
        """
        Create a single Article record from the generated content, excerpt, and AI summary.
        """
        # Improve readability
        editor = EditorService()
        improved_article = await editor.improve_readability(complete_content)

        message_history = []
        # Generate excerpt
        excerpt_data = await self._generate_excerpt(message_history, improved_article)
        # Generate AI summary
        summary_data = await self._generate_ai_summary(message_history)

        if cleaned_sources.get("content"):
            improved_article += f"\n\n## Sources\n{cleaned_sources['content']}"

        # Create and save
        article = Article(
            research_id=research_id,
            category_id=category_id,
            title=suggestion.title,
            content=improved_article,
            excerpt=excerpt_data["excerpt"],
            ai_summary=summary_data["summary"],
            status=ContentStatus.PENDING,
            model_id=self.agent.model_id,
            generation_started_at=generation_started_at,
        )

        db.session.add(article)
        try:
            db.session.commit()
            return article
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(f"Failed to save article: {str(e)}")

    # noinspection PyArgumentList
    async def _create_article_series(
        self,
        research_id: int,
        category_id: int,
        suggestion: ArticleSuggestion,
        complete_content: str,
        cleaned_sources: Dict[str, str],
        generation_started_at: datetime,
    ) -> List[Article]:
        """
        For very long content, call ArticleEditorService to break it into a multipart series.
        Then create multiple Article records.
        """
        editor = EditorService()

        word_count = len(complete_content.split())
        editor_response = await editor.process_long_article(
            title=suggestion.title,
            content=complete_content,
            sources=cleaned_sources["content"]
            if cleaned_sources.get("content")
            else None,
            num_parts=word_count // 1800,
        )

        articles_data = editor_response["articles"]
        articles: List[Article] = []
        first_article: Optional[Article] = None

        for i, article_dict in enumerate(articles_data, start=1):
            improved_article = await editor.improve_readability(article_dict["content"])

            article = Article(
                research_id=research_id,
                category_id=category_id,
                title=article_dict["title"],
                content=improved_article,
                excerpt=article_dict["excerpt"],
                ai_summary=article_dict["ai_summary"],
                status=ContentStatus.PENDING,
                model_id=self.agent.model_id,
                generation_started_at=generation_started_at,
                series_order=i if i > 1 else None,
            )

            if i == 1:
                first_article = article
            else:
                article.series_parent = first_article

            articles.append(article)

        db.session.add_all(articles)
        db.session.flush()  # Get the article id

        # Add "About" and "Continue Reading" sections
        for article in articles:
            about_section = WriterService._generate_about_section(
                articles, article, suggestion.title
            )
            article.content = f"{about_section}\n\n{article.content}"

            continue_reading_section = WriterService._generate_continue_reading_section(
                articles, article
            )
            if continue_reading_section:
                article.content += f"\n\n{continue_reading_section}"

        try:
            db.session.commit()
            return articles
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(f"Failed to save article series: {str(e)}")

    async def _generate_excerpt(
        self, message_history: List[Dict[str, str]], article_content: str
    ) -> Dict[str, Any]:
        """
        Generate an excerpt from the final article content.
        """
        excerpt_prompt = EXCERPT_PROMPT.format(article_content=article_content)

        excerpt_text = await self.generate_content(
            prompt=excerpt_prompt, message_history=message_history
        )
        if not excerpt_text:
            raise ValueError("Empty excerpt response")

        excerpt = WriterService._clean_excerpt(excerpt_text)

        message_history.append({"role": "user", "content": excerpt_prompt})
        message_history.append({"role": "assistant", "content": excerpt})

        return {"excerpt": excerpt}

    async def _generate_ai_summary(
        self, message_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Generate a short technical summary.
        """
        summary_prompt = SUMMARY_PROMPT
        summary_text = await self.generate_content(
            prompt=summary_prompt, message_history=message_history
        )
        if not summary_text:
            raise ValueError("Empty summary response")

        summary = WriterService._clean_summary(summary_text)
        return {"summary": summary}

    @staticmethod
    def _clean_summary(summary: str) -> str:
        """
        Clean up AI summary by removing any known prefixes (if relevant).
        """
        summary = summary.strip()
        prefixes = [
            "TECHNICAL SUMMARY [100 words]:",
            "TECHNICAL SUMMARY:",
            "AI SUMMARY:",
            "SUMMARY:",
        ]
        for prefix in prefixes:
            if summary.startswith(prefix):
                summary = summary[len(prefix) :].strip()
        return summary

    @staticmethod
    def _clean_excerpt(excerpt: str) -> str:
        """
        Clean up excerpt text by removing wrapping quotes, etc.
        """
        excerpt = excerpt.strip()
        if excerpt.startswith('"') and excerpt.endswith('"'):
            excerpt = excerpt[1:-1]
        elif excerpt.startswith('"'):
            excerpt = excerpt[1:]
        elif excerpt.endswith('"'):
            excerpt = excerpt[:-1]
        return excerpt.strip()

    @staticmethod
    def _generate_about_section(
        articles: List[Article], current_article: Article, suggestion_title: str
    ) -> str:
        """
        Generate About section for a multipart series.
        """
        total_articles = len(articles)
        current_index = articles.index(current_article)
        about = (
            "*About this Article*\n\n"
            f"This article is part {current_index + 1} of a {total_articles}-part series "
            f"about {suggestion_title}.\n\nArticles in this series:\n"
        )

        for article in articles:
            if article.id == current_article.id:
                about += f"\n- {article.title} (You are here)"
            else:
                about += f"\n- [{article.title}]({article.public_url})"

        about += "\n\n---\n"
        return about

    @staticmethod
    def _generate_continue_reading_section(
        articles: List[Article], current_article: Article
    ) -> Optional[str]:
        """
        Creates a link to the next article in the series, if any.
        """
        current_index = articles.index(current_article)
        if current_index == len(articles) - 1:
            return None  # last article

        next_article = articles[current_index + 1]
        continue_reading = (
            "\n\n---\n\n"
            "*Continue Reading*\n\n"
            "Ready for the next part? Continue to "
            f"[Part {current_index + 2}: {next_article.title}]({next_article.public_url})"
        )
        return continue_reading
