from .initial_prompts import INITIAL_PROMPTS
from .models import Provider, AgentType

INITIAL_AI_MODELS = [
    {
        "name": "GPT-4o",
        "provider": Provider.OPENAI,
        "model_id": "gpt-4o",
        "description": "GPT-4o is the most advanced GPT from openAI",
        "is_active": True,
        "input_rate": 2.50,
        "output_rate": 10.00,
        "batch_input_rate": 1.25,  # 50% of input_rate
        "batch_output_rate": 5.00,  # 50% of output_rate
    },
    {
        "name": "Claude 3.5 Sonnet",
        "provider": Provider.ANTHROPIC,
        "model_id": "claude-3-5-sonnet-latest",
        "description": "Claude 3.5 Sonnet has the highest level of intelligence and capability from Anthropic",
        "is_active": True,
        "input_rate": 3.00,
        "output_rate": 15.00,
        "batch_input_rate": 1.50,  # 50% of input_rate
        "batch_output_rate": 7.50,  # 50% of output_rate
    },
]

INITIAL_AGENTS = [
    {
        "name": "Content Manager",
        "type": AgentType.CONTENT_MANAGER,
        "description": "Suggests new articles based on existing content",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.85,
        "max_tokens": 4096,
        "prompts": [
            {
                "name": "content_suggestion",
                "description": "Template for generating new article suggestions",
                "template": INITIAL_PROMPTS["content_manager_prompt"],
            }
        ],
    },
    {
        "name": "Researcher",
        "type": AgentType.RESEARCHER,
        "description": "Conducts in-depth research for articles",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.8,
        "max_tokens": 8192,
        "prompts": [
            {
                "name": "research",
                "description": "Template for conducting article research",
                "template": INITIAL_PROMPTS["researcher_prompt"],
            }
        ],
    },
    {
        "name": "Writer",
        "type": AgentType.WRITER,
        "description": "Writes articles based on research",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.95,
        "max_tokens": 4096,
        "prompts": [
            {
                "name": "article_writing",
                "description": "Template for writing articles",
                "template": INITIAL_PROMPTS["writer_prompt"],
            }
        ],
    },
    {
        "name": "Social Media Manager",
        "type": AgentType.SOCIAL_MEDIA,
        "description": "Generates social media content from articles",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.95,
        "max_tokens": 2048,
        "prompts": [
            {
                "name": "instagram_post_did_you_know",
                "description": "Template for generating Instagram 'Did you know?' posts",
                "template": INITIAL_PROMPTS["instagram_post_did_you_know"],
            },
            {
                "name": "instagram_story_article_promotion",
                "description": "Template for generating Instagram article promotion story",
                "template": INITIAL_PROMPTS["instagram_story_article_promotion"],
            },
        ],
    },
    {
        "name": "Translator",
        "type": AgentType.TRANSLATOR,
        "description": "Translates content while preserving formatting and special tokens",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.3,
        "max_tokens": 8092,
        "prompts": [
            {
                "name": "translate_content",
                "description": "Template for translating content while preserving format",
                "template": "",  # We'll add the template content later
            }
        ],
    },
]
