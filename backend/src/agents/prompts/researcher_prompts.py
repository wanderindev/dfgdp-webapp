RESEARCH_LONG_FORM_PROMPT = """
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

RESEARCH_SUBTOPIC_STRUCTURE_PROMPT = """
## {subtopic}
6 detailed paragraphs exploring:
- Key concepts and principles
- Supporting evidence
- Critical analysis
- Practical applications
- Regional variations
- Historical development
""".strip()

RESEARCH_LONG_FORM_CONTINUATION_PROMPT = """
You just completed the full development of the {previous_section} section.
Now continue with the {current_section} section. This section should be based on
the specifications set in my initial message and the contents of the Abstract
you generated.
""".strip()

RESEARCH_BIO_PROMPT = """
You are an academic researcher. Your task is to produce a biographic research document
of the following figure for an education platform focusing on the history and culture of Panama.

CONTEXT
Taxonomy: {context[taxonomy]}
Taxonomy Description: {context[taxonomy_description]}
Category: {context[category]}
Category Description: {context[category_description]}

BIOGRAPHICAL SUBJECT
Full Name: {suggestion[title]}
Highlights: {suggestion[point_of_view]}

ARTICLE STRUCTURE
The final biography should have:
1. **Overview**: Introduce the figure, their historical/cultural context, and their main achievements.
3. **Biographical Data**: Birth, death, major life events, etc.
2. **Detailed Life & Legacy**: Expand on childhood (if relevant), career or major contributions, significant events or accomplishments, and historical impact.
3. **Conclusion**: Summarize their enduring significance or legacy.
4. **Sources and Further Reading**: Provide at least 3 relevant references.

WRITING STYLE
- Use Markdown formatting
- Maintain a coherent narrative
- Avoid bullet points in the main text
- Keep the total length below 3000 words
- Cite important facts using references where possible
- Use a factual, narrative tone

Generate **only** the Overview section now (step 1). Limit the Overview to ~300-500 words. 
""".strip()

RESEARCH_SITE_PROMPT = """
You are an academic researcher. Your task is to produce a research document
about the following site or landmark for an education platform focusing on the history and culture of Panama.

CONTEXT
Taxonomy: {context[taxonomy]}
Taxonomy Description: {context[taxonomy_description]}
Category: {context[category]}
Category Description: {context[category_description]}

SITE DETAILS
Name: {suggestion[title]}
Key Info: {suggestion[point_of_view]}

DOCUMENT STRUCTURE
The final article should have:

1. **Introduction** (required)
   - Introduce the site, its location, and its historical or cultural significance.

2. Depending on the specific site category, include only the relevant section below:

   -- If the category is "Colonial Forts & Ruins":
      2A. **Colonial Military Architecture & Defense Strategies**
         - Discuss the design, strategic importance, and defense features.
      2B. **Key Historical Events & Preservation**
         - Outline major events (e.g., pirate attacks, trade routes) and current preservation efforts.

   -- If the category is "Historic & Modern Landmarks":
      2A. **Historical Evolution & Cultural Impact**
         - Highlight key eras and transformations over time.
      2B. **Modern Relevance & Urban Development**
         - Explore how the landmark functions today (tourism, civic life, etc.).

   -- If the category is "Museums & Cultural Centers":
      2A. **Origins & Curatorial Focus**
         - Detail how and why the museum/center was established.
      2B. **Notable Exhibitions & Community Engagement**
         - Describe major exhibits, educational programs, outreach, etc.

   -- If the category is "Religious Landmarks":
      2A. **Founding & Spiritual Significance**
         - Explain when and why it was founded, and its role in local faith.
      2B. **Architecture & Community Role**
         - Discuss notable architectural features, religious art, and community events.

   -- If the category is "Archaeological Sites":
      2A. **Archaeological Findings & Historical Context**
         - Summarize major discoveries and what they reveal about past cultures.
      2B. **Conservation Efforts & Research**
         - Highlight ongoing excavations, preservation activities, and scholarly work.

   -- If the category is "Natural Heritage Attractions":
      2A. **Geological/Environmental Significance**
         - Detail geological history, unique flora/fauna, or environmental importance.
      2B. **Ecotourism & Conservation**
         - Explore how visitors engage with the site and any conservation strategies.

3. **Conclusion**
   - Summarize the site's importance today and any ongoing relevance to Panamanian identity.

4. **Sources and Further Reading**:
   - Provide at least 3 references or scholarly resources.

WRITING STYLE
- Use Markdown
- Keep the total length below 3000 words
- Use a factual, narrative tone
- Avoid bullet points in the main text
- Each section should be substantial and well-developed

Generate **only** the Introduction section now (step 1). Limit it to ~300-500 words.
""".strip()


RESEARCH_SHORT_FORM_CONTINUATION_PROMPT = """
You just completed the {previous_section} section of this short-form article on: "{title}."
Now continue with the {current_section} section.
Remember:
- The total article must stay below 3000 words.
- Maintain the structure described in the original instructions.
- Build upon the context set in the previous sections you generated.
- Return only the markdown content for the {current_section} section. Don't include additional comments.
""".strip()

SITES_SECTIONS_MAP = {
    "Colonial Forts & Ruins": [
        "Introduction",
        "Military Architecture & Defense Strategies",
        "Key Historical Events & Preservation",
        "Conclusion",
        "Sources and Further Reading",
    ],
    "Historic & Modern Landmarks": [
        "Introduction",
        "Historical Evolution & Cultural Impact",
        "Modern Relevance & Urban Development",
        "Conclusion",
        "Sources and Further Reading",
    ],
    "Museums & Cultural Centers": [
        "Introduction",
        "Origins & Curatorial Focus",
        "Notable Exhibitions & Community Engagement",
        "Conclusion",
        "Sources and Further Reading",
    ],
    "Religious Landmarks": [
        "Introduction",
        "Founding & Spiritual Significance",
        "Architecture & Community Role",
        "Conclusion",
        "Sources and Further Reading",
    ],
    "Archaeological Sites": [
        "Introduction",
        "Archaeological Findings & Historical Context",
        "Conservation Efforts & Research",
        "Conclusion",
        "Sources and Further Reading",
    ],
    "Natural Heritage Attractions": [
        "Introduction",
        "Geological/Environmental Significance",
        "Ecotourism & Conservation",
        "Conclusion",
        "Sources and Further Reading",
    ],
}
