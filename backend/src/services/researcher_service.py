from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import current_app

from agents.models import AgentType
from agents.prompts.researcher_prompts import (
    CONTINUATION_PROMPT,
    RESEARCHER_RESEARCH_PROMPT,
    SUBTOPIC_STRUCTURE,
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

    # noinspection PyArgumentList
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
            subtopics_structure += SUBTOPIC_STRUCTURE.format(subtopic=subtopic)

        # Insert the subtopics structure so the prompt covers them all
        research_params["dynamic_subtopics_structure"] = subtopics_structure

        # Final prompt text
        initial_prompt = RESEARCHER_RESEARCH_PROMPT.format(
            **research_params,
            sub_topics_list=sub_topics_formatted,
        )

        try:
            full_content: List[str] = []
            message_history: List[Dict[str, str]] = []
            generation_started_at = datetime.now(timezone.utc)

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

            # -- Step 1: Generate the Abstract --
            # The abstract call does not rely on previous content, so we pass an empty message history
            # We'll store only the user message for reference
            message_history.append({"role": "user", "content": initial_prompt})

            # AI call: abstract
            abstract_content = await self._generate_ai_section(
                prompt=initial_prompt,
                message_history=[],
            )

            # Clean and store
            full_content.append(ResearcherService._clean_markdown(abstract_content))

            # Also append the abstract to the conversation (assistant role)
            message_history.append({"role": "assistant", "content": abstract_content})

            # -- Step 2: Generate Each Subsequent Section --
            # We'll iterate from section 1 onward (skipping the 0th index: "Abstract")
            for i in range(1, len(sections)):
                current_section = sections[i]
                previous_section = sections[i - 1]

                continuation_prompt = CONTINUATION_PROMPT.format(
                    previous_section=previous_section, current_section=current_section
                )

                # Add a user prompt for this new section
                message_history.append({"role": "user", "content": continuation_prompt})

                # We only include the initial user prompt + the abstract response in the message history
                # so the AI focuses on that context
                partial_history = message_history[:2]  # [initial user, abstract]

                section_content = await self._generate_ai_section(
                    prompt=continuation_prompt,
                    message_history=partial_history,
                )
                if not section_content:
                    raise ValueError(f"Empty response for section: {current_section}")

                full_content.append(ResearcherService._clean_markdown(section_content))

            # Combine all the sections
            complete_content = "\n\n".join(full_content)

            # Create the new Research record
            research = Research(
                suggestion_id=suggestion_id,
                content=complete_content,
                status=ContentStatus.PENDING,
                model_id=self.agent.model_id,
                generation_started_at=generation_started_at,
            )
            db.session.add(research)
            db.session.commit()
            return research

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generating research: {e}")
            raise

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

        return {
            "suggestion": {
                "title": suggestion.title,
                "main_topic": suggestion.main_topic,
                "sub_topics": suggestion.sub_topics,
                "point_of_view": suggestion.point_of_view,
            },
            "context": {
                "taxonomy": category.taxonomy.name,
                "taxonomy_description": category.taxonomy.description,
                "category": category.name,
                "category_description": category.description,
            },
        }

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
