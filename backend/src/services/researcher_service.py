from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import current_app

from agents.models import AgentType
from agents.prompts.researcher_prompts import (
    RESEARCH_BIO_PROMPT,
    RESEARCH_LONG_FORM_CONTINUATION_PROMPT,
    RESEARCH_LONG_FORM_PROMPT,
    RESEARCH_SHORT_FORM_CONTINUATION_PROMPT,
    RESEARCH_SITE_PROMPT,
    RESEARCH_SUBTOPIC_STRUCTURE_PROMPT,
    SITES_SECTIONS_MAP,
)
from content.models import ArticleSuggestion, Category, Research, ContentStatus
from extensions import db
from services.base_ai_service import BaseAIService


class ResearcherService(BaseAIService):
    """
    Service for generating research content using the AI client.
    Inherits from BaseAIService to automatically load the RESEARCHER agent & client.
    """

    def __init__(self):
        super().__init__(AgentType.RESEARCHER)

    # noinspection PyArgumentList,PyTypeChecker
    async def generate_research(self, suggestion_id: int) -> Research:
        """
        Generate research content for an article suggestion.
        """

        suggestion: Optional[ArticleSuggestion] = db.session.query(
            ArticleSuggestion
        ).get(suggestion_id)
        if not suggestion:
            raise ValueError(f"ArticleSuggestion {suggestion_id} not found")

        category: Optional[Category] = db.session.query(Category).get(
            suggestion.category_id
        )
        if not category:
            raise ValueError(f"Category {suggestion.category_id} not found")

        taxonomy = category.taxonomy.name

        generation_started_at = datetime.now(timezone.utc)

        # Decide if we do short or long form:
        if taxonomy == "Notable Figures" or taxonomy == "Sites & Landmarks":
            content = await self._generate_short_form_research(suggestion, category)
        else:
            content = await self._generate_long_form_research(suggestion, category)

        # Create the new Research record
        research = Research(
            suggestion_id=suggestion_id,
            content=content,
            status=ContentStatus.PENDING,
            model_id=self.agent.model_id,
            generation_started_at=generation_started_at,
        )
        db.session.add(research)
        db.session.commit()
        return research

    async def _generate_long_form_research(self, suggestion, category) -> str:
        """
        Generate research content for a long-form article suggestion.
         - Abstract
         - Main Topic Development
         - Each sub-topic
         - Contemporary Relevance
         - Conclusion
         - Sources & Further Reading
        """

        # Prepare any dynamic parameters for our research prompt
        research_params = ResearcherService._prepare_research_params(
            suggestion, category
        )

        # Build the subtopics block
        sub_topics_formatted = "\n".join(
            f"- {topic}" for topic in suggestion.sub_topics
        )
        subtopics_structure = ""
        for subtopic in suggestion.sub_topics:
            subtopics_structure += RESEARCH_SUBTOPIC_STRUCTURE_PROMPT.format(
                subtopic=subtopic
            )

        # Insert the subtopics structure so the prompt covers them all
        research_params["dynamic_subtopics_structure"] = subtopics_structure

        # Final prompt text
        initial_prompt = RESEARCH_LONG_FORM_PROMPT.format(
            **research_params,
            sub_topics_list=sub_topics_formatted,
        )

        try:
            full_content: List[str] = []
            message_history: List[Dict[str, str]] = []

            # We'll generate multiple sections:
            sections = ["Abstract", "Main Topic Development"]
            sections.extend(suggestion.sub_topics)
            sections.extend(
                [
                    "Contemporary Relevance",
                    "Conclusion",
                    "Sources and Further Reading",
                ]
            )

            # Generate the Abstract --
            # AI call: abstract
            abstract_content = await self._generate_ai_section(
                prompt=initial_prompt,
                message_history=message_history,
            )
            if not abstract_content:
                raise ValueError(f"Empty response for abstract")

            cleaned_abstract_content = ResearcherService._clean_markdown(
                abstract_content
            )
            full_content.append(cleaned_abstract_content)

            # Update the message history with the last iteration
            message_history.append({"role": "user", "content": initial_prompt})
            message_history.append(
                {"role": "assistant", "content": cleaned_abstract_content}
            )

            # Generate Each Subsequent Section --
            # We'll iterate from section 1 onward (skipping the 0th index: "Abstract")
            for i in range(1, len(sections)):
                current_section = sections[i]
                previous_section = sections[i - 1]

                continuation_prompt = RESEARCH_LONG_FORM_CONTINUATION_PROMPT.format(
                    previous_section=previous_section, current_section=current_section
                )

                section_content = await self._generate_ai_section(
                    prompt=continuation_prompt,
                    message_history=message_history,
                )
                if not section_content:
                    raise ValueError(f"Empty response for section: {current_section}")

                clean_section_content = ResearcherService._clean_markdown(
                    section_content
                )
                full_content.append(clean_section_content)

                # Update the message history with the last iteration
                message_history.append({"role": "user", "content": continuation_prompt})
                message_history.append(
                    {"role": "assistant", "content": clean_section_content}
                )

            # Combine all the sections
            return "\n\n".join(full_content)

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generating research: {e}")
            raise

    async def _generate_short_form_research(self, suggestion, category) -> str:
        """
        New method to generate short-form articles in multiple steps.
        """
        short_content_pieces = []
        message_history = []

        # Build the correct initial prompt template
        taxonomy = category.taxonomy.name
        if taxonomy == "Notable Figures":
            initial_prompt_template = RESEARCH_BIO_PROMPT
            sections = [
                "Overview",
                "Biographical Data" "Detailed Life & Legacy",
                "Conclusion",
                "Sources and Further Reading",
            ]
        else:
            # Sites & Landmarks
            initial_prompt_template = RESEARCH_SITE_PROMPT
            sections = SITES_SECTIONS_MAP.get(
                category.name,
                [
                    "Introduction",
                    "Key Details",
                    "Conclusion",
                    "Sources and Further Reading",
                ],
            )

        # Prepare any dynamic parameters for our research prompt
        research_params = ResearcherService._prepare_research_params(
            suggestion, category
        )

        initial_prompt = initial_prompt_template.format(**research_params)

        # Generate the first section (Overview or Introduction)
        first_section_content = await self._generate_ai_section(
            prompt=initial_prompt,
            message_history=message_history,
        )
        cleaned_first_section = self._clean_markdown(first_section_content)
        short_content_pieces.append(cleaned_first_section)

        # Update the message history with the last iteration
        message_history.append({"role": "user", "content": initial_prompt})
        message_history.append({"role": "assistant", "content": first_section_content})

        # Generate subsequent sections
        for i in range(1, len(sections)):
            previous_section = sections[i - 1]
            current_section = sections[i]

            # build a short-form continuation prompt
            continuation_prompt = RESEARCH_SHORT_FORM_CONTINUATION_PROMPT.format(
                previous_section=previous_section,
                current_section=current_section,
                title=suggestion.title,
            )

            section_content = await self._generate_ai_section(
                prompt=continuation_prompt,
                message_history=message_history,
            )
            cleaned_section = self._clean_markdown(section_content)
            short_content_pieces.append(cleaned_section)

            # Update the message history with the last iteration
            message_history.append({"role": "user", "content": continuation_prompt})
            message_history.append({"role": "assistant", "content": cleaned_section})

        # Combine all short sections into final content
        return "\n\n".join(short_content_pieces)

    @staticmethod
    def _clean_markdown(content: str) -> str:
        """
        Clean markdown wrapper if present.
        For example, if the AI returns content wrapped in triple backticks.
        """
        if content.startswith("```markdown\n") and content.endswith("```"):
            return content[12:-3]
        elif content.startswith("```\n") and content.endswith("```"):
            return content[4:-3]
        return content

    @staticmethod
    def _prepare_research_params(
        suggestion: ArticleSuggestion,
        category: Category,
    ) -> Dict[str, Any]:
        """
        Prepare parameters for the main research prompt.
        """
        research_params = {
            "suggestion": {
                "title": suggestion.title,
                "point_of_view": suggestion.point_of_view,
            },
            "context": {
                "taxonomy": category.taxonomy.name,
                "taxonomy_description": category.taxonomy.description,
                "category": category.name,
                "category_description": category.description,
            },
        }

        if category.taxonomy.name not in ["Notable Figures", "Sites & Landmarks"]:
            research_params["suggestion"]["main_topic"] = suggestion.main_topic
            research_params["suggestion"]["sub_topics"] = suggestion.sub_topics

        return research_params

    async def _generate_ai_section(
        self,
        prompt: str,
        message_history: List[Dict[str, str]],
    ) -> (str, int):
        """
        Helper function to generate a single AI "section."
        """
        content = await self.generate_content(
            prompt=prompt, message_history=message_history
        )
        return content
