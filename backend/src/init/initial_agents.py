from agents.models import Provider, AgentType

INITIAL_AI_MODELS = [
    {
        "name": "Claude 3.5 Sonnet",
        "provider": Provider.ANTHROPIC,
        "model_id": "claude-3-5-sonnet-20241022",
        "description": "Context: 200K; Max Output: 8192; Vision: Yes; Multilingual: Yes",
        "is_active": True,
        "input_rate": 3.00,
        "output_rate": 15.00,
        "batch_input_rate": 1.50,
        "batch_output_rate": 7.50,
    },
]

INITIAL_AGENTS = [
    {
        "name": "Content Manager",
        "type": AgentType.CONTENT_MANAGER,
        "description": "Suggests new articles based on existing content",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.90,
        "max_tokens": 8192,
    },
    {
        "name": "Researcher",
        "type": AgentType.RESEARCHER,
        "description": "Conducts in-depth research for articles",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.8,
        "max_tokens": 8192,
    },
    {
        "name": "Writer",
        "type": AgentType.WRITER,
        "description": "Writes articles based on research",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.90,
        "max_tokens": 8192,
    },
    {
        "name": "Editor",
        "type": AgentType.EDITOR,
        "description": "Edit articles for clarity and readability",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.90,
        "max_tokens": 8192,
    },
    {
        "name": "Social Media Manager",
        "type": AgentType.SOCIAL_MEDIA,
        "description": "Generates social media content from articles",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.90,
        "max_tokens": 8192,
    },
    {
        "name": "Translator",
        "type": AgentType.TRANSLATOR,
        "description": "Translates content and metadata while preserving formatting and special tokens",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.8,
        "max_tokens": 8192,
    },
    {
        "name": "Media Manager",
        "type": AgentType.MEDIA_MANAGER,
        "description": "Analyzes research content to suggest relevant images and media",
        "model": "Claude 3.5 Sonnet",
        "temperature": 0.90,
        "max_tokens": 8192,
    },
]
