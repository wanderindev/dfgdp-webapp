import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import current_app
from sqlalchemy.exc import IntegrityError

from agents.models import AgentType
from content.models import Article, ContentStatus
from extensions import db
from services.base_ai_service import BaseAIService
from content.models import SocialMediaAccount, Platform, SocialMediaPost, PostType
from content.models import HashtagGroup  # if needed


class SocialMediaManagerService(BaseAIService):
    """
    Service for generating social media content using AI.
    Inherits from BaseAIService to automatically load the SOCIAL_MEDIA agent & client.
    """

    def __init__(self) -> None:
        super().__init__(AgentType.SOCIAL_MEDIA)

        # Also fetch an active Instagram account
        self.account: Optional[SocialMediaAccount] = (
            db.session.query(SocialMediaAccount)
            .filter_by(platform=Platform.INSTAGRAM, is_active=True)
            .first()
        )

        if not self.account:
            raise ValueError("No active Instagram account found")

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
        # Validate article
        article = db.session.query(Article).get(article_id)
        if not article:
            raise ValueError(f"Article {article_id} not found")

        # Prepare prompt variables
        # If you have a direct prompt, you might do something like:
        # from agents.prompts.social_media_instagram_story_article_promotion_prompt import SOCIAL_MEDIA_INSTAGRAM_STORY_ARTICLE_PROMOTION_PROMPT
        # and then do prompt = SOCIAL_MEDIA_INSTAGRAM_STORY_ARTICLE_PROMOTION_PROMPT.format(...)
        # For now, we'll assume you still have a DB-based template or some code-based approach.
        # We'll show the code-based approach for clarity:
        prompt_vars = {
            "article_title": article.title,
            "article_main_topic": article.research.suggestion.main_topic,
            "category_name": article.category.name,
            "category_description": article.category.description,
            "article_level": article.level.value,  # If still used
            "article_url": article.public_url,
            "hashtag_groups": self._format_hashtag_groups(),
        }

        # Build final prompt text. For example:
        # prompt = SOCIAL_MEDIA_INSTAGRAM_STORY_ARTICLE_PROMOTION_PROMPT.format(**prompt_vars)
        # Or if you still rely on a DB template, you can do:
        # template = self.agent.get_template("instagram_story_article_promotion")
        # prompt = template.render(**prompt_vars)
        # We'll assume a code-based prompt for clarity:

        template = self.agent.get_template("instagram_story_article_promotion")
        if not template:
            raise ValueError("Story promotion template not found")

        prompt = template.render(**prompt_vars)

        try:
            generation_started_at = datetime.now(timezone.utc)

            # AI call
            text = await self.generate_content(prompt=prompt, message_history=[])

            if not text:
                raise ValueError("Empty response from AI")

            # Parse JSON
            data = json.loads(text)

            # Combine hashtags
            group_hashtags = self._get_hashtags_from_groups(
                data.get("selected_hashtag_groups", [])
            )
            all_hashtags = (
                self._get_core_hashtags() + group_hashtags + data.get("hashtags", [])
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
                tokens_used=0,  # Or remove if you don't store tokens
                generation_started_at=generation_started_at,
            )

            db.session.add(post)
            db.session.commit()
            return post

        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse AI response: {e}")
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
            article_id: ID of the article
            num_posts: Number of "Did you know?" posts to generate

        Returns:
            List of created SocialMediaPost objects
        """
        article = db.session.query(Article).get(article_id)
        if not article or not article.research:
            raise ValueError(f"Article {article_id} or its research not found")

        research = article.research

        # Prepare prompt variables
        prompt_vars = {
            "research_title": article.title,
            "category_name": article.category.name,
            "category_description": article.category.description,
            "research_content": research.content,
            "hashtag_groups": self._format_hashtag_groups(),
            "num_posts": num_posts,
        }

        # If you have code-based prompts:
        # from agents.prompts.social_media_instagram_post_did_you_know_prompt import SOCIAL_MEDIA_INSTAGRAM_POST_DID_YOU_KNOW_PROMPT
        # prompt = SOCIAL_MEDIA_INSTAGRAM_POST_DID_YOU_KNOW_PROMPT.format(**prompt_vars)
        # Or from DB template:
        template = self.agent.get_template("instagram_post_did_you_know")
        if not template:
            raise ValueError("Did you know template not found")

        prompt = template.render(**prompt_vars)

        try:
            generation_started_at = datetime.now(timezone.utc)

            # AI call
            text = await self.generate_content(prompt=prompt, message_history=[])
            if not text:
                raise ValueError("Empty response from AI")

            data = json.loads(text)

            # Create posts
            created_posts = []
            for post_data in data["posts"]:
                group_hashtags = self._get_hashtags_from_groups(
                    post_data.get("selected_hashtag_groups", [])
                )
                all_hashtags = (
                    self._get_core_hashtags()
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
                    tokens_used=0,  # or remove if not storing tokens
                    generation_started_at=generation_started_at,
                )
                db.session.add(post)
                created_posts.append(post)

            db.session.commit()
            return created_posts

        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse AI response: {e}")
            raise ValueError("Invalid API response format")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generating did you know posts: {e}")
            raise

    # -------------------------------------------------------------------------
    # Helper Hashtag Methods
    # -------------------------------------------------------------------------
    @staticmethod
    def _format_hashtag_groups() -> str:
        """Format hashtag groups for prompt template"""
        groups = HashtagGroup.query.filter_by(is_core=False).all()
        return "\n".join(
            f"{group.name}:\n{', '.join(group.hashtags)}\n" for group in groups
        )

    @staticmethod
    def _get_core_hashtags() -> List[str]:
        """Get hashtags from core groups (take at most 3)"""
        core_groups = HashtagGroup.query.filter_by(is_core=True).all()
        core_hashtags = []
        for group in core_groups:
            core_hashtags.extend(group.hashtags[:3])
        return core_hashtags

    @staticmethod
    def _get_hashtags_from_groups(group_names: List[str]) -> List[str]:
        """
        Get hashtags from specified group(s).
        For simplicity, we only handle the first group in the list.
        """
        if group_names:
            group_name = group_names[0]
            group = HashtagGroup.query.filter_by(name=group_name).first()
            if group:
                return group.hashtags[:5]
        return []
