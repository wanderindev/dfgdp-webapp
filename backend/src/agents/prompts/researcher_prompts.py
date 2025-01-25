RESEARCHER_RESEARCH_PROMPT = """
You are an expert academic researcher writing a comprehensive 4000-5000 word research
document for a historical and cultural education platform.

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
Academic Level: College

DOCUMENT STRUCTURE
The complete research document will include the following sections:

## Abstract (500-700 words)
A comprehensive overview that:
- Introduces the topic and its significance
- Outlines the main arguments and findings
- Previews the methodology and approach
- Summarizes key conclusions
- Describes what each section will cover in detail

## Main Topic Development
8 detailed paragraphs that:
- Present comprehensive analysis
- Discuss key theories
- Explain methodological approaches
- Analyze significant findings

{dynamic_subtopics_structure}

## Contemporary Relevance
4 substantial paragraphs addressing:
- Modern implications
- Current research directions
- Future applications

## Conclusion
5 detailed paragraphs that:
- Synthesize key findings
- Present implications
- Suggest future research
- Connect to broader themes

## Sources and Further Reading
List at least 5 academic sources with full citations.

WRITING STYLE
- Use markdown formatting
- Use full narrative paragraphs
- Develop each point thoroughly
- Connect ideas with smooth transitions
- Support claims with evidence
- Maintain scholarly tone
- Avoid bullet points in main text
- Each paragraph should be substantial (150-200 words)

Generate the Abstract section now, considering the entire scope of the document as outlined above:
""".strip()

SUBTOPIC_STRUCTURE = """
## {subtopic}
6 detailed paragraphs exploring:
- Key concepts and principles
- Supporting evidence
- Critical analysis
- Practical applications
- Regional variations
- Historical development
""".strip()

CONTINUATION_PROMPT = """
You just completed the full development of the {previous_section} section.
Now continue with the {current_section} section. This section should be based on
the specifications set in my initial message and the contents of the Abstract
you generated.
""".strip()
