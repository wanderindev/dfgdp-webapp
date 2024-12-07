from .models import Provider, AgentType

INITIAL_AI_MODELS = [
    {
        "name": "GPT-4o",
        "provider": Provider.OPENAI,
        "model_id": "gpt-4o",
        "description": "GPT-4o is the most advanced GPT from openAI",
        "is_active": True,
    },
    {
        "name": "Claude 3.5 Sonnet",
        "provider": Provider.ANTHROPIC,
        "model_id": "claude-3-5-sonnet-latest",
        "description": "Claude 3.5 Sonnet has the highest level of intelligence and capability from Anthropic",
        "is_active": True,
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
                "template": "",
            }
        ],
    },
    {
        "name": "Researcher",
        "type": AgentType.RESEARCHER,
        "description": "Conducts in-depth research for articles",
        "model": "GPT-4o",
        "temperature": 0.4,
        "max_tokens": 4096,
        "prompts": [
            {
                "name": "research",
                "description": "Template for conducting article research",
                "template": "",  # We'll add the template content later
            }
        ],
    },
    {
        "name": "Writer",
        "type": AgentType.WRITER,
        "description": "Writes articles based on research",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.7,
        "max_tokens": 4096,
        "prompts": [
            {
                "name": "article_writing",
                "description": "Template for writing articles",
                "template": "",  # We'll add the template content later
            }
        ],
    },
    {
        "name": "Social Media Manager",
        "type": AgentType.SOCIAL_MEDIA,
        "description": "Generates social media content from articles",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.85,
        "max_tokens": 2048,
        "prompts": [
            {
                "name": "instagram_post",
                "description": "Template for generating Instagram posts",
                "template": "",  # We'll add the template content later
            }
        ],
    },
]
