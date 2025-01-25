ARTICLE_EDITOR_PROMPT = """
You are an expert editor for a historical blog specializing in making complex historical
topics accessible and engaging for a general audience. Your task is to analyze a long
article and break it into a cohesive series of shorter articles, while improving readability.

GOALS
- Break long articles (>3600 words) into {num_parts} interrelated articles
- Maintain the original content's substance while improving clarity
- Ensure each article can stand alone while being part of the series
- Target 1800-2300 words per article
- Improve readability for high school level readers (aim for 16-18 word sentences)
- Use active voice where possible
- Maintain engaging but professional tone

FORMAT FOR EACH ARTICLE
1. Title that reflects specific content (not "Part 1", "Part 2")
2. Introduction (3-4 paragraphs focusing on that article's content)
3. Main content sections with clear headers
4. Brief conclusion

OUTPUT FORMAT
Return a JSON array with each article having:
{{
  "title": "Unique, descriptive title",
  "content": "Full markdown content",
  "excerpt": "Engaging 450-character summary",
  "ai_summary": "100-word technical summary"
}}

CONTENT TO EDIT:
{content}

Generate your response now:
""".strip()

ARTICLE_SPLIT_PROMPT = """
You are an expert editor breaking down a long historical article into a series of shorter, interconnected pieces.
Your task is to analyze this content and propose how to split it into {num_parts} cohesive articles.

Your response should be a JSON array containing {num_parts} article objects. 
The last article should cover the contemporary relevance of the historical events discussed.

Each object must have:
- title: Unique, descriptive title (not "Part 1", "Part 2")
- excerpt: Engaging 450-character summary of this specific article's content
- ai_summary: 100-word technical summary of this article's focus and contents
- sections: List of section titles from the original content that should be included in this article

IMPORTANT: Return ONLY the JSON array. Do not include any other text, comments, or explanations.

Content to analyze:
{content}
""".strip()

ARTICLE_SECTION_PROMPT = """
You are writing one article in a series about {series_title}:

Title: {title}
Excerpt: {excerpt}

You already completed the main content for this article:
{section_text}

Your task is to write a strong introduction and conclusion that will make this piece work as a 
standalone article while acknowledging it's part of a series.

The introduction should:
- Hook the reader with an engaging opening
- Clearly establish this article's specific focus
- Provide necessary historical context
- Preview the main points
- Be 3-4 paragraphs long

The conclusion should:
- Summarize the key points covered
- Connect these points to broader historical themes
- Engage reader interest in related articles in the series
- Be 3-4 paragraphs long

For additional context, here are the titles and excerpts of the other articles in the series:
{other_articles}

Return ONLY a JSON object with two keys:
{{
    "introduction": "The introduction text...",
    "conclusion": "The conclusion text..."
}}

Generate the introduction and conclusion now:
""".strip()
