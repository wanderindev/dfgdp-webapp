import asyncio
import json
from datetime import datetime, timezone
from html import unescape
from typing import Any, Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup
from flask import current_app
from sqlalchemy.exc import IntegrityError
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.clients import AnthropicClient, OpenAIClient
from agents.clients.base import RateLimiter
from agents.models import Agent, AgentType, Provider
from content.models import (
    Article,
    ArticleLevel,
    ArticleSuggestion,
    Category,
    ContentStatus,
    HashtagGroup,
    MediaCandidate,
    MediaSuggestion,
    Platform,
    PostType,
    Research,
    SocialMediaAccount,
    SocialMediaPost,
)
from extensions import db
from .constants import ARTICLE_LEVELS


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
            level: Article level (ELEMENTARY, MIDDLE_SCHOOL, etc.)
            num_suggestions: Number of suggestions to generate

        Returns:
            List of created ArticleSuggestion objects

        Raises:
            ValueError: If parameters are invalid or API call fails
        """
        # Validate parameters
        if num_suggestions < 1:
            raise ValueError("Number of suggestions must be at least 1")

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


# noinspection PyArgumentList,PyProtectedMember
class ResearcherService:
    """Service for generating research content using AI"""

    def __init__(self) -> None:
        # Get the active researcher agent
        self.agent: Optional[Agent] = Agent.query.filter_by(
            type=AgentType.RESEARCHER, is_active=True
        ).first()

        if not self.agent:
            raise ValueError("No active researcher agent found")

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

    async def generate_research(self, suggestion_id: int) -> Research:
        """
        Generate research content for an article suggestion.

        Args:
            suggestion_id: ID of the ArticleSuggestion to research

        Returns:
            Created Research object

        Raises:
            ValueError: If parameters are invalid or API call fails
        """
        suggestion = ArticleSuggestion.query.get(suggestion_id)
        if not suggestion:
            raise ValueError(f"ArticleSuggestion {suggestion_id} not found")

        category = Category.query.get(suggestion.category_id)
        if not category:
            raise ValueError(f"Category {suggestion.category_id} not found")

        research_params = ResearcherService._prepare_research_params(
            suggestion, category
        )
        template = self.agent.get_template("research")
        if not template:
            raise ValueError("Research template not found")

        try:
            full_content = []
            message_history = []
            generation_started_at = datetime.now(timezone.utc)
            total_tokens = 0

            # Build section order
            sections = ["Abstract", "Main Topic Development"]
            sections.extend(suggestion.sub_topics)
            sections.extend(
                [
                    "Contemporary Relevance",
                    "Conclusion",
                    "Sources and Further Reading",
                ]
            )

            # Generate initial abstract
            sub_topics_formatted = "\n".join(
                f"- {topic}" for topic in suggestion.sub_topics
            )

            # Create dynamic subtopics structure for the prompt
            subtopics_structure = ""
            for subtopic in suggestion.sub_topics:
                subtopics_structure += f"""
## {subtopic}
6 detailed paragraphs exploring:
- Key concepts and principles
- Supporting evidence
- Critical analysis
- Practical applications
- Regional variations
- Historical development

"""
            research_params["dynamic_subtopics_structure"] = subtopics_structure

            initial_prompt = template.render(
                **research_params,
                sub_topics_list=sub_topics_formatted,
            )

            # Generate abstract
            message_history.append({"role": "user", "content": initial_prompt})
            abstract_response = self.client._generate_content(
                prompt=initial_prompt,
                message_history=[],  # Empty for initial prompt
            )

            abstract_content = self.client._extract_content(abstract_response)
            total_tokens += self.client._track_usage(abstract_response)

            # Add abstract to full content and message history
            full_content.append(self._clean_markdown(abstract_content))
            message_history.append({"role": "assistant", "content": abstract_content})

            # Generate each section
            for i in range(1, len(sections)):
                current_section = sections[i]
                previous_section = sections[i - 1]

                continuation_prompt = (
                    f"You just completed the full development of the {previous_section} section. "
                    f"Now continue with the {current_section} section. This section should be based on "
                    f"the specifications set in my initial message and the contents of the Abstract "
                    f"you generated."
                )

                # Add continuation prompt to message history
                message_history.append({"role": "user", "content": continuation_prompt})

                # Generate section content
                section_response = self.client._generate_content(
                    prompt=continuation_prompt,
                    message_history=message_history[
                        :2
                    ],  # Only initial prompt and abstract
                )

                if not section_response:
                    raise ValueError(f"Empty response for section: {current_section}")

                section_content = self.client._extract_content(section_response)
                total_tokens += self.client._track_usage(section_response)

                # Add clean content to full document
                full_content.append(self._clean_markdown(section_content))

                # Small delay between sections
                await asyncio.sleep(5)

            # Create final research document
            complete_content = "\n\n".join(full_content)
            research = Research(
                suggestion_id=suggestion_id,
                content=complete_content,
                status=ContentStatus.PENDING,
                model_id=self.agent.model_id,
                tokens_used=total_tokens,
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
        """Clean markdown wrapper if present."""
        if content.startswith("```markdown\n") and content.endswith("```"):
            return content[12:-3]
        elif content.startswith("```\n") and content.endswith("```"):
            return content[4:-3]
        return content

    @staticmethod
    def _prepare_research_params(
        suggestion: ArticleSuggestion, category: Category
    ) -> Dict[str, Any]:
        """
        Prepare parameters for research prompt template.

        Args:
            suggestion: ArticleSuggestion object
            category: Category object

        Returns:
            Dictionary of parameters for template
        """
        # Get maximum words for the level
        level_specs = ARTICLE_LEVELS.get(suggestion.level.value)
        if not level_specs:
            raise ValueError(f"Invalid article level: {suggestion.level}")

        return {
            "suggestion": {
                "title": suggestion.title,
                "main_topic": suggestion.main_topic,
                "sub_topics": suggestion.sub_topics,
                "point_of_view": suggestion.point_of_view,
                "level": "COLLEGE",
            },
            "context": {
                "taxonomy": category.taxonomy.name,
                "taxonomy_description": category.taxonomy.description,
                "category": category.name,
                "category_description": category.description,
            },
            "constraints": {
                "format": "markdown",
            },
        }


# noinspection PyArgumentList,PyProtectedMember
class WriterService:
    """Service for generating articles from research using AI"""

    def __init__(self) -> None:
        # Get the active writer agent
        self.agent: Optional[Agent] = Agent.query.filter_by(
            type=AgentType.WRITER, is_active=True
        ).first()

        if not self.agent:
            raise ValueError("No active writer agent found")

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

    async def generate_article(self, research_id: int) -> Article:
        """
        Generate an article based on research content.

        Args:
            research_id: ID of the Research to use as source

        Returns:
            Created Article object

        Raises:
            ValueError: If parameters are invalid or API call fails
        """
        # Get research and validate
        research = Research.query.get(research_id)
        if not research:
            raise ValueError(f"Research {research_id} not found")

        if research.status != ContentStatus.APPROVED:
            raise ValueError(f"Research {research_id} is not approved")

        # Get suggestion and category information
        suggestion = research.suggestion
        if not suggestion:
            raise ValueError(f"No suggestion found for research {research_id}")

        category = suggestion.category
        if not category:
            raise ValueError(f"No category found for suggestion {suggestion.id}")

        # Get level specifications
        level_specs = ARTICLE_LEVELS.get(suggestion.level.value)
        if not level_specs:
            raise ValueError(f"Invalid article level: {suggestion.level}")

        try:
            generation_started_at = datetime.now(timezone.utc)
            message_history = []

            # Prepare template variables
            template_vars = {
                "context": {
                    "taxonomy": category.taxonomy.name,
                    "taxonomy_description": category.taxonomy.description,
                    "category": category.name,
                    "category_description": category.description,
                },
                "title": suggestion.title,
                "level": suggestion.level.value,
                "level_description": level_specs.description,
                "min_words": level_specs.min_words,
                "max_words": level_specs.max_words,
                "research_content": research.content,
            }

            # Get and validate prompt template
            template = self.agent.get_template("article_writing")
            if not template:
                raise ValueError("Article writing template not found")

            # Generate article content
            initial_prompt = template.render(**template_vars)
            message_history.append({"role": "user", "content": initial_prompt})

            content_response = self.client._generate_content(
                prompt=initial_prompt,
                message_history=[],
            )

            if not content_response:
                raise ValueError("Empty response from API")

            article_content = WriterService._clean_article_content(
                self.client._extract_content(content_response)
            )
            total_tokens = self.client._track_usage(content_response)

            # Add article content to message history
            message_history.append({"role": "assistant", "content": article_content})

            # Generate excerpt
            excerpt_prompt = (
                "Based on the article content you just generated and keeping in mind "
                "the blog's focus on Panama's cultural identity, generate an engaging "
                "excerpt of maximum 480 characters that will make readers want to read "
                "the full article. Write the excerpt as plain text without quotes."
            )

            message_history.append({"role": "user", "content": excerpt_prompt})
            excerpt_response = self.client._generate_content(
                prompt=excerpt_prompt,
                message_history=message_history[:2],  # Initial prompt and article only
            )

            if not excerpt_response:
                raise ValueError("Empty excerpt response")

            excerpt = WriterService._clean_excerpt(
                self.client._extract_content(excerpt_response)
            )
            total_tokens += self.client._track_usage(excerpt_response)

            # Generate AI summary
            summary_prompt = (
                "Generate a brief technical summary of the article content "
                "(maximum 100 words) that captures its key topics and arguments. "
                "This summary will be used by the content management system to "
                "track article coverage and suggest new topics. Write the summary "
                "as plain text without any prefix or keywords section."
            )

            message_history.append({"role": "user", "content": summary_prompt})
            summary_response = self.client._generate_content(
                prompt=summary_prompt,
                message_history=message_history[:2],
            )

            if not summary_response:
                raise ValueError("Empty summary response")

            ai_summary = WriterService._clean_summary(
                self.client._extract_content(summary_response)
            )
            total_tokens += self.client._track_usage(summary_response)

            # Create article
            article = Article(
                research_id=research_id,
                category_id=category.id,
                title=suggestion.title,
                content=article_content,
                excerpt=excerpt,
                ai_summary=ai_summary,
                level=suggestion.level,
                status=ContentStatus.PENDING,
                model_id=self.agent.model_id,
                tokens_used=total_tokens,
                generation_started_at=generation_started_at,
            )

            db.session.add(article)
            db.session.commit()
            return article

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generating article: {e}")
            raise

    @staticmethod
    def _clean_article_content(content: str) -> str:
        """Clean up article content by removing anything after the end marker."""
        if "[END_ARTICLE]" in content:
            content = content.split("[END_ARTICLE]")[0].strip()
        return content

    @staticmethod
    def _clean_summary(summary: str) -> str:
        """Clean up AI summary by removing technical prefix."""
        summary = summary.strip()
        # Remove various possible prefixes
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
        """Clean up excerpt text."""
        excerpt = excerpt.strip()
        # Remove quotes if they're the first/last characters
        if excerpt.startswith('"') and excerpt.endswith('"'):
            excerpt = excerpt[1:-1]
        elif excerpt.startswith('"'):
            excerpt = excerpt[1:]
        elif excerpt.endswith('"'):
            excerpt = excerpt[:-1]
        return excerpt.strip()


# noinspection PyProtectedMember,PyArgumentList
class SocialMediaManagerService:
    """Service for generating social media content using AI"""

    def __init__(self) -> None:
        # Get the active social media manager agent
        self.agent: Optional[Agent] = Agent.query.filter_by(
            type=AgentType.SOCIAL_MEDIA, is_active=True
        ).first()

        if not self.agent:
            raise ValueError("No active social media manager agent found")

        # Get active Instagram account
        self.account: Optional[SocialMediaAccount] = SocialMediaAccount.query.filter_by(
            platform=Platform.INSTAGRAM, is_active=True
        ).first()

        if not self.account:
            raise ValueError("No active Instagram account found")

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

    async def generate_story_promotion(
        self, article_id: int
    ) -> Optional[SocialMediaPost]:
        """
        Generate an Instagram Story post to promote a new article.

        Args:
            article_id: ID of the article to promote

        Returns:
            Created SocialMediaPost object or None if generation fails
        """
        # Get article and validate
        article = Article.query.get(article_id)
        if not article:
            raise ValueError(f"Article {article_id} not found")

        # Get hashtag groups data
        hashtag_groups = SocialMediaManagerService._format_hashtag_groups()

        # Prepare prompt variables
        prompt_vars = {
            "article_title": article.title,
            "article_main_topic": article.research.suggestion.main_topic,
            "category_name": article.category.name,
            "category_description": article.category.description,
            "article_level": article.level.value,
            "article_url": article.public_url,
            "hashtag_groups": hashtag_groups,
        }

        # Get and validate prompt template
        template = self.agent.get_template("instagram_story_article_promotion")
        if not template:
            raise ValueError("Story promotion template not found")

        try:
            # Generate content
            generation_started_at = datetime.now(timezone.utc)
            prompt = template.render(**prompt_vars)

            response = self.client._generate_content(prompt)
            if not response:
                raise ValueError("Empty response from API")

            content = self.client._extract_content(response)
            data = json.loads(content)

            # Get hashtags from selected groups
            group_hashtags = SocialMediaManagerService._get_hashtags_from_groups(
                data.get("selected_hashtag_groups", [])
            )

            # Combine with specific hashtags and core hashtags
            all_hashtags = (
                SocialMediaManagerService._get_core_hashtags()
                + group_hashtags
                + data.get("hashtags", [])
            )

            # Create post
            post = SocialMediaPost(
                article_id=article_id,
                account_id=self.account.id,
                post_type=PostType.STORY,
                content=data["content"],
                hashtags=all_hashtags,
                status=ContentStatus.PENDING,
                model_id=self.agent.model_id,
                tokens_used=self.client._track_usage(response),
                generation_started_at=generation_started_at,
            )

            db.session.add(post)
            db.session.commit()
            return post

        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse API response: {e}")
            raise ValueError("Invalid API response format")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generating story promotion: {e}")
            raise

    async def generate_did_you_know_posts(
        self, article_id: int, num_posts: int = 3
    ) -> List[SocialMediaPost]:
        """
        Generate Instagram feed posts with interesting facts from the article's research.

        Args:
            article_id: ID of the article whose research to use
            num_posts: Number of posts to generate (default: 3)

        Returns:
            List of created SocialMediaPost objects
        """
        # Get article and validate
        article = Article.query.get(article_id)
        if not article or not article.research:
            raise ValueError(f"Article {article_id} or its research not found")

        research = article.research

        # Get hashtag groups data
        hashtag_groups = SocialMediaManagerService._format_hashtag_groups()

        # Prepare prompt variables
        prompt_vars = {
            "research_title": article.title,
            "category_name": article.category.name,
            "category_description": article.category.description,
            "research_content": research.content,
            "hashtag_groups": hashtag_groups,
            "num_posts": num_posts,
        }

        # Get and validate prompt template
        template = self.agent.get_template("instagram_post_did_you_know")
        if not template:
            raise ValueError("Did you know template not found")

        try:
            # Generate content
            generation_started_at = datetime.now(timezone.utc)
            prompt = template.render(**prompt_vars)

            response = self.client._generate_content(prompt)
            if not response:
                raise ValueError("Empty response from API")

            content = self.client._extract_content(response)
            data = json.loads(content)

            total_tokens = self.client._track_usage(response)
            tokens_per_post = total_tokens // len(data["posts"])

            # Create posts
            created_posts = []
            for post_data in data["posts"]:
                # Get hashtags from selected groups
                group_hashtags = SocialMediaManagerService._get_hashtags_from_groups(
                    post_data.get("selected_hashtag_groups", [])
                )

                # Combine with specific hashtags and core hashtags
                all_hashtags = (
                    SocialMediaManagerService._get_core_hashtags()
                    + group_hashtags
                    + post_data.get("hashtags", [])
                )

                post = SocialMediaPost(
                    article_id=article_id,
                    account_id=self.account.id,
                    post_type=PostType.FEED,
                    content=post_data["content"],
                    hashtags=all_hashtags,
                    status=ContentStatus.PENDING,
                    model_id=self.agent.model_id,
                    tokens_used=tokens_per_post,
                    generation_started_at=generation_started_at,
                )

                db.session.add(post)
                created_posts.append(post)

            db.session.commit()
            return created_posts

        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse API response: {e}")
            raise ValueError("Invalid API response format")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generating did you know posts: {e}")
            raise

    @staticmethod
    def _format_hashtag_groups() -> str:
        """Format hashtag groups for prompt template"""
        groups = HashtagGroup.query.filter_by(is_core=False).all()
        return "\n".join(
            f"{group.name}:\n{', '.join(group.hashtags)}\n" for group in groups
        )

    @staticmethod
    def _get_core_hashtags() -> List[str]:
        """Get hashtags from core groups"""
        core_groups = HashtagGroup.query.filter_by(is_core=True).all()
        core_hashtags = []
        for group in core_groups:
            # Take at most 3 hashtags from each core group
            core_hashtags.extend(group.hashtags[:3])
        return core_hashtags

    @staticmethod
    def _get_hashtags_from_groups(group_names: List[str]) -> List[str]:
        """Get hashtags from specified groups"""
        if group_names:
            group_name = group_names[0]
            group = HashtagGroup.query.filter_by(name=group_name).first()
            if group:
                # Take at most 5 hashtags from the group
                return group.hashtags[:5]
        return []


# noinspection PyArgumentList,PyProtectedMember,PyUnboundLocalVariable
class MediaManagerService:
    """Service for generating media suggestions using AI"""

    def __init__(self) -> None:
        # Get the active media manager agent
        self.agent: Optional[Agent] = Agent.query.filter_by(
            type=AgentType.MEDIA_MANAGER, is_active=True
        ).first()

        if not self.agent:
            raise ValueError("No active media manager agent found")

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

    async def generate_suggestions(self, research_id: int) -> MediaSuggestion:
        """
        Generate media suggestions for research content.

        Args:
            research_id: ID of the Research to analyze

        Returns:
            Created MediaSuggestion object

        Raises:
            ValueError: If parameters are invalid or API call fails
        """
        # Get research and validate
        research = Research.query.get(research_id)
        if not research:
            raise ValueError(f"Research {research_id} not found")

        suggestion = research.suggestion
        if not suggestion:
            raise ValueError(f"No suggestion found for research {research_id}")

        category = suggestion.category
        if not category:
            raise ValueError(f"No category found for suggestion {suggestion.id}")

        try:
            # Prepare template variables
            template_vars = {
                "research_title": suggestion.title,
                "taxonomy_name": category.taxonomy.name,
                "taxonomy_description": category.taxonomy.description,
                "category_name": category.name,
                "category_description": category.description,
                "research_content": research.content,
            }

            # Get and validate prompt template
            template = self.agent.get_template("media_suggestions")
            if not template:
                raise ValueError("Media suggestions template not found")

            # Generate suggestions
            generation_started_at = datetime.now(timezone.utc)
            prompt = template.render(**template_vars)

            response = self.client._generate_content(prompt)
            if not response:
                raise ValueError("Empty response from API")

            content = self.client._extract_content(response)
            data = MediaManagerService._parse_response(content)

            # Create suggestion
            media_suggestion = MediaSuggestion(
                research_id=research_id,
                commons_categories=data["commons_categories"],
                search_queries=data["search_queries"],
                illustration_topics=data["illustration_topics"],
                reasoning=data["reasoning"],
                model_id=self.agent.model_id,
                tokens_used=self.client._track_usage(response),
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
    def _parse_response(content: str) -> dict:
        """
        Parse API response with fallback cleanup

        Args:
            content: Raw response content

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If parsing fails after cleanup attempts
        """
        try:
            # First try direct parsing
            return json.loads(content)
        except json.JSONDecodeError as e:
            current_app.logger.warning(f"Initial JSON parsing failed: {e}")

            try:
                # Clean up newlines in reasoning field
                import re

                # Find the reasoning field and clean it up
                pattern = r'"reasoning"\s*:\s*"([^"]*)"'
                match = re.search(pattern, content)
                if match:
                    reasoning = match.group(1)
                    # Replace newlines and normalize spaces
                    cleaned_reasoning = " ".join(reasoning.replace("\n", " ").split())
                    # Replace the reasoning in the content
                    content = re.sub(
                        pattern, f'"reasoning":"{cleaned_reasoning}"', content
                    )

                return json.loads(content)

            except (json.JSONDecodeError, re.error) as e:
                current_app.logger.error(
                    f"Failed to parse JSON even after cleanup: {e}"
                )
                raise ValueError("Invalid API response format")


# noinspection PyArgumentList
class WikimediaService:
    """Service for interacting with Wikimedia Commons API"""

    API_ENDPOINT = "https://commons.wikimedia.org/w/api.php"

    def __init__(self) -> None:
        self.session = None
        self.rate_limiter = RateLimiter(
            calls_per_minute=30
        )  # Respect Wikimedia's limits

    async def __aenter__(self) -> "WikimediaService":
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def search_images(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for images using the Wikimedia API

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of image metadata dictionaries
        """
        await self.rate_limiter.wait_if_needed()

        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": "6",
            "gsrsearch": f"filetype:bitmap|drawing {query}",
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiextmetadatafilter": "License|LicenseUrl|Attribution|Artist|ImageDescription|ObjectName|Title",
        }

        async with self.session.get(self.API_ENDPOINT, params=params) as response:
            data = await response.json()

            if "query" not in data or "pages" not in data["query"]:
                return []

            results = []
            for page in data["query"]["pages"].values():
                metadata = WikimediaService._extract_image_metadata(page)
                if metadata:
                    results.append(metadata)

            return results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def search_category(
        self, category: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for images in a specific Commons category

        Args:
            category: Category name (without "Category:" prefix)
            limit: Maximum number of results

        Returns:
            List of image metadata dictionaries
        """
        # Step 1: Get category members
        category = category.replace("Category:", "")
        titles = await self._get_category_members(category, limit)

        if not titles:
            return []

        # Step 2: Fetch metadata in batches
        return await self._fetch_files_metadata(titles)

    async def process_suggestion(
        self, suggestion_id: int, max_per_query: int = 10
    ) -> List[MediaCandidate]:
        """
        Process a MediaSuggestion and create MediaCandidate entries

        Args:
            suggestion_id: ID of MediaSuggestion to process
            max_per_query: Maximum images to fetch per query/category

        Returns:
            List of created MediaCandidate objects
        """
        suggestion = MediaSuggestion.query.get(suggestion_id)
        if not suggestion:
            raise ValueError(f"MediaSuggestion {suggestion_id} not found")

        candidates = []

        # Process categories
        for category in suggestion.commons_categories:
            try:
                results = await self.search_category(category, limit=max_per_query)
                candidates.extend(
                    await WikimediaService._create_candidates(suggestion, results)
                )
            except Exception as e:
                current_app.logger.error(f"Error processing category {category}: {e}")

        # Process search queries
        for query in suggestion.search_queries:
            try:
                results = await self.search_images(query, limit=max_per_query)
                candidates.extend(
                    await WikimediaService._create_candidates(suggestion, results)
                )
            except Exception as e:
                current_app.logger.error(f"Error processing query {query}: {e}")

        return candidates

    @staticmethod
    async def _create_candidates(
        suggestion: MediaSuggestion, results: List[Dict[str, Any]]
    ) -> List[MediaCandidate]:
        """Create MediaCandidate entries from search results"""
        candidates = []

        for result in results:
            try:
                candidate = MediaCandidate(suggestion_id=suggestion.id, **result)
                db.session.add(candidate)
                candidates.append(candidate)

            except Exception as e:
                current_app.logger.error(f"Error creating candidate: {e}")
                continue

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            current_app.logger.error("Duplicate candidates found, skipping")

        return candidates

    @staticmethod
    def _extract_image_metadata(page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract standardized image metadata from a Commons API response page

        Args:
            page: Dictionary containing page data from Commons API

        Returns:
            Dictionary containing standardized metadata or None if invalid
        """
        if "imageinfo" not in page:
            return None

        try:
            info = page["imageinfo"][0]
            metadata = info.get("extmetadata", {})

            # Clean HTML from metadata fields
            description = WikimediaService._clean_html_content(
                metadata.get("ImageDescription", {}).get("value")
            )
            author = WikimediaService._clean_html_content(
                metadata.get("Artist", {}).get("value")
            )

            # For title, prefer ObjectName over filename
            title = metadata.get("ObjectName", {}).get("value") or page[
                "title"
            ].replace("File:", "")
            title = WikimediaService._clean_html_content(title)

            return {
                "commons_id": page["title"],
                "commons_url": info["url"],
                "title": title,
                "description": description,
                "author": author,
                "license": metadata.get("License", {}).get("value"),
                "license_url": metadata.get("LicenseUrl", {}).get("value"),
                "width": info["width"],
                "height": info["height"],
                "mime_type": info["mime"],
                "file_size": info["size"],
            }
        except (KeyError, IndexError) as e:
            current_app.logger.warning(f"Error extracting image metadata: {e}")
            return None

    async def _get_category_members(self, category: str, limit: int) -> List[str]:
        """Get list of file titles from category"""
        params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtype": "file",
            "cmtitle": f"Category:{category}",
            "cmlimit": limit,
        }

        async with self.session.get(self.API_ENDPOINT, params=params) as response:
            data = await response.json()

            if "query" not in data or "categorymembers" not in data["query"]:
                return []

            return [member["title"] for member in data["query"]["categorymembers"]]

    async def _fetch_files_metadata(
        self, titles: List[str], batch_size: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch metadata for multiple files in batches

        Args:
            titles: List of file titles
            batch_size: Number of files to fetch per request

        Returns:
            List of metadata dictionaries
        """
        results = []

        # Process titles in batches
        for i in range(0, len(titles), batch_size):
            batch = titles[i : i + batch_size]

            # Wait for rate limiting
            await self.rate_limiter.wait_if_needed()

            params = {
                "action": "query",
                "format": "json",
                "prop": "imageinfo",
                "titles": "|".join(batch),
                "iiprop": "url|size|mime|extmetadata",
                "iiextmetadatafilter": "License|LicenseUrl|Attribution|Artist|ImageDescription|ObjectName|Title",
            }

            try:
                async with self.session.get(
                    self.API_ENDPOINT, params=params
                ) as response:
                    data = await response.json()

                    if "query" in data and "pages" in data["query"]:
                        for page in data["query"]["pages"].values():
                            metadata = WikimediaService._extract_image_metadata(page)
                            if metadata:
                                results.append(metadata)

            except Exception as e:
                current_app.logger.error(
                    f"Error fetching batch {i}-{i + batch_size}: {str(e)}"
                )
                continue

            # Small delay between batches
            await asyncio.sleep(1)

        return results

    @staticmethod
    def _clean_html_content(html_content: Optional[str]) -> Optional[str]:
        """
        Clean HTML content from metadata

        Args:
            html_content: String that might contain HTML

        Returns:
            Cleaned string without HTML tags
        """
        if not html_content:
            return None

        # First unescape HTML entities
        unescaped = unescape(html_content)

        # Parse with BeautifulSoup to extract text
        soup = BeautifulSoup(unescaped, "html.parser")

        # Get text and clean up whitespace
        text = soup.get_text(separator=" ")
        text = " ".join(text.split())

        return text.strip() or None
