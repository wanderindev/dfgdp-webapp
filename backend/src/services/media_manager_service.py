import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import current_app

from agents.models import AgentType
from agents.prompts.media_manager_prompts import MEDIA_MANAGER_SUGGESTIONS_PROMPT
from content.models import Research, MediaSuggestion
from extensions import db
from services.base_ai_service import BaseAIService


class MediaManagerService(BaseAIService):
    """
    Service for generating media suggestions using AI.
    """

    def __init__(self) -> None:
        super().__init__(AgentType.MEDIA_MANAGER)

    # noinspection PyArgumentList
    async def generate_suggestions(self, research_id: int) -> MediaSuggestion:
        """
        Generate media suggestions for research content.
        """

        research: Optional[Research] = db.session.query(Research).get(research_id)
        if not research:
            raise ValueError(f"Research {research_id} not found")

        suggestion = research.suggestion
        if not suggestion:
            raise ValueError(f"No suggestion found for research {research_id}")

        category = suggestion.category
        if not category:
            raise ValueError(f"No category found for suggestion {suggestion.id}")

        try:
            # Prepare the prompt
            prompt_vars = {
                "research_title": suggestion.title,
                "taxonomy_name": category.taxonomy.name,
                "taxonomy_description": category.taxonomy.description,
                "category_name": category.name,
                "category_description": category.description,
                "research_content": research.content,
            }
            prompt_text = MEDIA_MANAGER_SUGGESTIONS_PROMPT.format(**prompt_vars)

            # Call the AI
            generation_started_at = datetime.now(timezone.utc)
            response_text = await self.generate_content(
                prompt=prompt_text, message_history=[]
            )
            if not response_text:
                raise ValueError("Empty response from AI")

            # Parse the JSON
            data = self._parse_response(response_text)

            # Create the MediaSuggestion record
            media_suggestion = MediaSuggestion(
                research_id=research_id,
                commons_categories=data["commons_categories"],
                search_queries=data["search_queries"],
                illustration_topics=data["illustration_topics"],
                reasoning=data["reasoning"],
                model_id=self.agent.model_id,
                generation_started_at=generation_started_at,
            )
            db.session.add(media_suggestion)
            db.session.commit()
            return media_suggestion

        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse API response: {e}")
            raise ValueError("Invalid API response format")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generating media suggestions: {e}")
            raise

    @staticmethod
    def _parse_response(content: str) -> Dict[str, Any]:
        """
        Parse the AI's JSON response, with fallback cleanup.
        """
        try:
            # First try direct JSON parse
            return json.loads(content)
        except json.JSONDecodeError as e:
            current_app.logger.warning(f"Initial JSON parsing failed: {e}")

        # Attempt to clean "reasoning" field by removing newlines, etc.
        try:
            pattern = r'"reasoning"\s*:\s*"([^"]*)"'
            match = re.search(pattern, content)
            if match:
                reasoning = match.group(1)
                cleaned_reasoning = " ".join(reasoning.replace("\n", " ").split())
                content = re.sub(pattern, f'"reasoning":"{cleaned_reasoning}"', content)

            return json.loads(content)
        except (json.JSONDecodeError, re.error) as cleanup_err:
            current_app.logger.error(
                f"Failed to parse JSON even after cleanup: {cleanup_err}"
            )
            raise ValueError("Invalid API response format")
