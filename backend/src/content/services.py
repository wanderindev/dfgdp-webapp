import json
from datetime import datetime, timezone
from typing import List, Optional

from flask import current_app
from sqlalchemy.exc import IntegrityError

from agents.clients import AnthropicClient, OpenAIClient
from agents.models import Agent, AgentType, Provider
from content.models import Article, ArticleSuggestion, Category
from extensions import db
from .constants import ARTICLE_LEVELS
from .models import ArticleLevel


# noinspection PyProtectedMember,PyArgumentList,PyTypeChecker
class ContentManagerService:
    """Service for generating article suggestions using AI"""

    def __init__(self) -> None:
        # Get the active content manager agent
        self.agent: Optional[Agent] = Agent.query.filter_by(
            type=AgentType.CONTENT_MANAGER, is_active=True
        ).first()

        if not self.agent:
            raise ValueError("No active content manager agent found")

        # Initialize the appropriate client based on the provider
        if self.agent.model.provider == Provider.ANTHROPIC:
            self.client = AnthropicClient(
                model=self.agent.model.model_id,
                temperature=self.agent.temperature,
                max_tokens=self.agent.max_tokens,
            )
        elif self.agent.model.provider == Provider.OPENAI:
            self.client = OpenAIClient(
                model=self.agent.model.model_id,
                temperature=self.agent.temperature,
                max_tokens=self.agent.max_tokens,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.agent.model.provider}")

        self.client._init_client()

    async def generate_suggestions(
        self,
        category_id: int,
        level: str,
        num_suggestions: int = 3,
    ) -> List[ArticleSuggestion]:
        """
        Generate article suggestions for a given category and level.

        Args:
            category_id: ID of the category
            level: Article level (elementary, middle_school, etc.)
            num_suggestions: Number of suggestions to generate

        Returns:
            List of created ArticleSuggestion objects

        Raises:
            ValueError: If parameters are invalid or API call fails
        """
        # Validate parameters
        category = Category.query.get(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        if level not in ARTICLE_LEVELS:
            raise ValueError(f"Invalid level: {level}")

        # Get existing articles in this category
        existing_articles = Article.query.filter_by(category_id=category_id).all()
        existing_summaries = "\n".join(
            f"- {article.title}: {article.ai_summary}"
            for article in existing_articles
            if article.ai_summary
        )

        # Prepare prompt variables
        prompt_vars = {
            "taxonomy": category.taxonomy.name,
            "taxonomy_description": category.taxonomy.description,
            "category": category.name,
            "category_description": category.description,
            "level": level,
            "level_description": ARTICLE_LEVELS[level].description,
            "num_suggestions": num_suggestions,
            "existing_summaries": existing_summaries or "No existing articles",
        }

        # Get and validate prompt template
        template = self.agent.get_template("content_suggestion")
        if not template:
            raise ValueError("Content suggestion template not found")

        # Generate suggestions
        try:
            prompt = template.render(**prompt_vars)

            # Generate content using the appropriate client
            generation_started_at = datetime.now(timezone.utc)
            response = self.client._generate_content(prompt)

            content = self.client._extract_content(response)

            # Track usage
            total_tokens = self.client._track_usage(response)

            # Parse response
            data = json.loads(content)
            if not isinstance(data, dict) or "suggestions" not in data:
                raise ValueError("Invalid response format")

            # Create suggestion objects
            suggestions = []
            for suggestion in data["suggestions"]:
                article_suggestion = ArticleSuggestion(
                    category_id=category_id,
                    title=suggestion["title"],
                    main_topic=suggestion["main_topic"],
                    sub_topics=suggestion["sub_topics"],
                    point_of_view=suggestion["point_of_view"],
                    level=ArticleLevel(level),
                    model_id=self.agent.model_id,
                    tokens_used=total_tokens // num_suggestions,
                    generation_started_at=generation_started_at,
                )
                db.session.add(article_suggestion)
                suggestions.append(article_suggestion)

            db.session.commit()
            return suggestions

        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse API response: {e}")
            raise ValueError("Invalid API response format")
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {e}")
            raise ValueError("Failed to save suggestions")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generating suggestions: {e}")
            raise
