import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import current_app
from sqlalchemy.exc import IntegrityError

from agents.clients import AnthropicClient, OpenAIClient
from agents.models import Agent, AgentType, Provider
from content.models import (
    Article,
    ArticleLevel,
    ArticleSuggestion,
    Category,
    ContentStatus,
    HashtagGroup,
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

        # Verify agent uses Anthropic
        if self.agent.model.provider != Provider.ANTHROPIC:
            raise ValueError("Researcher agent must use Anthropic model")

        # Initialize Anthropic client
        self.client = AnthropicClient(
            model=self.agent.model.model_id,
            temperature=self.agent.temperature,
            max_tokens=self.agent.max_tokens,
        )

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

        # Initialize Anthropic client
        self.client = AnthropicClient(
            model=self.agent.model.model_id,
            temperature=self.agent.temperature,
            max_tokens=self.agent.max_tokens,
        )

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

        # Initialize Anthropic client
        self.client = AnthropicClient(
            model=self.agent.model.model_id,
            temperature=self.agent.temperature,
            max_tokens=self.agent.max_tokens,
        )

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
