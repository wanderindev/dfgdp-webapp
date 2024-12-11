INITIAL_PROMPTS = {
    "content_manager_prompt": """You are a content manager for a historical and cultural education platform.

CONTEXT
Taxonomy: {taxonomy}
Taxonomy Description: {taxonomy_description}
Category: {category}
Category Description: {category_description}
Target Level: {level}
Level Description: {level_description}
Number of Suggestions Needed: {num_suggestions}

Existing Articles (AI Summaries):
{existing_summaries}

REQUIREMENTS
1. Generate {num_suggestions} unique article suggestions
2. Each suggestion should:
   - Be distinct from existing articles (if any exist)
   - Be appropriate for the specified level
   - Fit within the taxonomy and category theme
   - Include 3-5 well-defined sub-topics
   - Have a clear point of view or angle
3. Topics should build on each other for comprehensive coverage
4. Consider gaps in existing content
5. Ensure suggestions maintain historical accuracy
6. Topics should be engaging and relevant to modern readers

FORMAT YOUR RESPONSE AS JSON:
{{
  "suggestions": [
    {{
      "title": "Clear, engaging title",
      "main_topic": "Primary focus of the article (200 chars max)",
      "sub_topics": ["Sub-topic 1", "Sub-topic 2", "Sub-topic 3"],
      "point_of_view": "Unique angle or perspective (300 chars max)"
    }}
  ]
}}

EXAMPLE SUGGESTION:
{{
  "suggestions": [
    {{
      "title": "The Hidden Impact of the Panama Railroad: Beyond Gold Rush Commerce",
      "main_topic": "Explore how the Panama Railroad's construction transformed local communities and established lasting multicultural connections beyond its well-known role in gold rush transportation",
      "sub_topics": [
        "Chinese and Caribbean Worker Communities",
        "Urban Development Along the Rail Line",
        "Cultural Exchange and Fusion",
        "Economic Ripple Effects"
      ],
      "point_of_view": "Examining the railroad's legacy through the lens of cultural transformation rather than just economic impact, highlighting how infrastructure projects can permanently reshape society"
    }}
  ]
}}

Generate your response now:""",
    "researcher_prompt": """You are an expert academic researcher writing a comprehensive 4000-5000 word research document for a historical and cultural education platform. This document must be complete in a single response.

CONTEXT AND SCOPE
Taxonomy: {context[taxonomy]}
Taxonomy Description: {context[taxonomy_description]}
Category: {context[category]}
Category Description: {context[category_description]}

RESEARCH TOPIC
Title: {suggestion[title]}
Main Topic: {suggestion[main_topic]}
Sub-topics:
{sub_topics_list}
Point of View: {suggestion[point_of_view]}
Academic Level: {suggestion[level]}

DOCUMENT REQUIREMENTS
This must be a complete academic research document with the following structure. Each section must be written in full narrative paragraphs, avoiding bullet points unless absolutely necessary.

## Introduction 
Write 5 substantial paragraphs that:
- Set the historical context
- Establish the topic's significance
- Present current research state
- Outline key debates
- Preview the document's structure

## Main Topic Development
Write 6-7 detailed paragraphs that:
- Present comprehensive analysis
- Discuss key theories
- Explain methodological approaches
- Analyze significant findings

## [First Sub-topic]
Write 6 detailed paragraphs exploring:
- Key concepts and principles
- Supporting evidence
- Critical analysis
- Practical applications
- Regional variations
- Historical development

[Repeat the above paragraph structure for each sub-topic]

## Contemporary Relevance
Write 3 substantial paragraphs addressing:
- Modern implications
- Current research directions
- Future applications

## Conclusion
Write 4 detailed paragraphs that:
- Synthesize key findings
- Present implications
- Suggest future research
- Connect to broader themes

## Sources and Further Reading
List at least 5 academic sources with full citations.

FORMAT
Use markdown formatting:
- Standard headers (##, ###)
- Bold for key terms
- Italic for emphasis
- Block quotes for notable quotes
- Section breaks with ---

WRITING STYLE
- Use full narrative paragraphs
- Develop each point thoroughly
- Connect ideas with smooth transitions
- Support claims with evidence
- Maintain scholarly tone
- Avoid bullet points in main text
- Each paragraph should be substantial (150-200 words)

This must be a complete, self-contained academic document generated in a single response. Do not truncate or split your response. Do not indicate continuation or ask for permission to continue.

Begin the research document now:""",
}
