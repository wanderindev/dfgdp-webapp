import json
from datetime import datetime, timezone
from typing import List, Optional

from flask import current_app
from sqlalchemy.exc import IntegrityError

from agents.models import AgentType
from agents.prompts.content_manager_prompts import (
    CONTENT_SUGGESTION_DEFAULT_PROMPT,
    CONTENT_SUGGESTION_HISTORICAL_PROMPT,
    CONTENT_SUGGESTION_NOTABLE_FIGURES_PROMPT,
    CONTENT_SUGGESTION_SITES_LANDMARKS_PROMPT,
)
from content.models import Article, ArticleSuggestion, Category
from extensions import db
from services.base_ai_service import BaseAIService


class ContentManagerService(BaseAIService):
    def __init__(self):
        super().__init__(AgentType.CONTENT_MANAGER)

    # noinspection PyArgumentList
    async def generate_suggestions(
        self, category_id: int, num_suggestions: int = 3
    ) -> List[ArticleSuggestion]:
        if num_suggestions < 1:
            raise ValueError("Number of suggestions must be at least 1")

        category: Optional[Category] = db.session.query(Category).get(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        existing_articles = (
            db.session.query(Article).filter_by(category_id=category.id).all()
        )
        existing_summaries = (
            "\n".join(
                f"- {article.title}: {article.ai_summary}"
                for article in existing_articles
                if article.ai_summary
            )
            or "No existing articles"
        )

        # Select the prompt based on taxonomy:
        taxonomy_name = category.taxonomy.name

        if taxonomy_name == "Notable Figures":
            prompt_template = CONTENT_SUGGESTION_NOTABLE_FIGURES_PROMPT
        elif taxonomy_name == "Sites & Landmarks":
            prompt_template = CONTENT_SUGGESTION_SITES_LANDMARKS_PROMPT
        elif taxonomy_name == "Historical Panama":
            prompt_template = CONTENT_SUGGESTION_HISTORICAL_PROMPT
        else:
            # Default prompt for Cultural Mosaic, Indigenous Heritage, Geographic Identity, etc.
            prompt_template = CONTENT_SUGGESTION_DEFAULT_PROMPT

        prompt_vars = {
            "taxonomy": category.taxonomy.name,
            "taxonomy_description": category.taxonomy.description,
            "category": category.name,
            "category_description": category.description,
            "num_suggestions": num_suggestions,
            "existing_summaries": existing_summaries,
        }
        prompt = prompt_template.format(**prompt_vars)

        try:
            generation_started_at = datetime.now(timezone.utc)

            content = await self.generate_content(prompt)

            # Parse the AI's JSON
            data = json.loads(content)
            if not isinstance(data, dict) or "suggestions" not in data:
                raise ValueError("Invalid response format (no 'suggestions' field)")

            suggestions = []
            for item in data["suggestions"]:
                article_suggestion = ArticleSuggestion(
                    category_id=category.id,
                    title=item.get("title"),
                    main_topic=item.get("main_topic"),
                    sub_topics=item.get("sub_topics"),
                    point_of_view=item.get("point_of_view"),
                    model_id=self.agent.model_id,
                    generation_started_at=generation_started_at,
                )
                db.session.add(article_suggestion)
                suggestions.append(article_suggestion)

            db.session.commit()
            return suggestions

        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse AI response: {e}")
            raise ValueError("Invalid API response format")
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {e}")
            raise ValueError("Failed to save suggestions")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generating suggestions: {e}")
            raise
