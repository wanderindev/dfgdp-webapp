from typing import Dict, NamedTuple


class ArticleStructure(NamedTuple):
    """Define the common structure for all articles"""

    min_sections: int = 3
    max_sections: int = 5
    required_elements: tuple = (
        "introduction",
        "main_points",
        "conclusion",
        "related_articles",
        "further_reading",
    )
    max_related_articles: int = 5


class ArticleLevelSpecs(NamedTuple):
    """Specifications for each article level"""

    min_words: int
    max_words: int
    description: str
    characteristics: tuple
    audience: str


# Article level specifications
ARTICLE_LEVELS: Dict[str, ArticleLevelSpecs] = {
    "elementary": ArticleLevelSpecs(
        min_words=500,
        max_words=800,
        description="Elementary Level (grades 1-6)",
        characteristics=(
            "Short paragraphs",
            "Simple language",
            "Key terms highlighted",
            "Fun fact boxes or sidebars",
        ),
        audience="Young students (grades 1-6)",
    ),
    "middle_school": ArticleLevelSpecs(
        min_words=800,
        max_words=1200,
        description="Middle School Level (grades 7-9)",
        characteristics=(
            "More detailed explanations",
            "Introduction to complex concepts",
            "Mix of basic and field-specific vocabulary",
            "Pull quotes from historical documents",
        ),
        audience="Middle school students (grades 7-9)",
    ),
    "high_school": ArticleLevelSpecs(
        min_words=1200,
        max_words=2000,
        description="High School Level (grades 9-12)",
        characteristics=(
            "In-depth analysis",
            "Sophisticated language",
            "Historical context",
            "Primary source references",
            "Critical thinking prompts",
        ),
        audience="High school students (grades 9-12)",
    ),
    "college": ArticleLevelSpecs(
        min_words=2000,
        max_words=3000,
        description="College Level",
        characteristics=(
            "Scholarly approach",
            "Detailed analysis",
            "Multiple perspectives",
            "Citations and references",
            "Technical terminology",
            "Theoretical frameworks",
        ),
        audience="College students and academics",
    ),
    "general": ArticleLevelSpecs(
        min_words=1000,
        max_words=1500,
        description="General Audience",
        characteristics=(
            "Balanced approach",
            "Clear explanations without oversimplification",
            "Mix of basic and advanced concepts",
            "Engaging storytelling elements",
            "Contemporary relevance highlighted",
        ),
        audience="General adult audience",
    ),
}

# Maximum length for different content elements
CONTENT_LIMITS = {
    "title": 100,  # characters
    "excerpt": 160,  # characters
    "main_topic": 200,  # characters
    "sub_topic": 100,  # characters per sub-topic
    "point_of_view": 300,  # characters
}
