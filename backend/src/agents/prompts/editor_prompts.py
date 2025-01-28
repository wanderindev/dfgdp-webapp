ARTICLE_EDITOR_PROMPT = """
You are an expert editor for a historical blog specializing in making complex historical
topics accessible and engaging for a general audience. Your task is to analyze a long
article and break it into a cohesive series of shorter articles, while improving readability.

GOALS
- Break long articles (>3600 words) into {num_parts} interrelated articles
- Maintain the original content's substance while improving clarity
- Ensure each article can stand alone while being part of the series
- Target 1800-2300 words per article
- Improve readability for college level readers (aim for 16-18 word sentences)
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

IMPROVE_READABILITY_INITIAL_PROMPT = """
You are a proofreader specializing in improving readability.  You fix grammatical issues, 
reduce passive voice, shorten long sentences, and correct punctuation problems.  You 
retain the original meaning and style, but ensure the text is more direct and clear. 
You use an informal, friendly tone.\n\n

For guidance, here are some comment text examples and how you might improve them:\n\n

Original:
"The discovery of a new ocean transformed Panama from a challenging strip of jungle into one of the world’s most strategic locations. That transformation continues to evolve today, as Panama constantly reinvents its role as a global crossroads while maintaining the core identity established during those pivotal colonial years. From the Panama Canal to our multicultural society, from our diplomatic expertise to our environmental challenges, Balboa’s influence echoes through every aspect of contemporary Panamanian life."\n\n
Revised:
"The discovery of a new ocean transformed Panama from a challenging stretch of jungle into one of the world’s most strategic locations. This transformation continues today as Panama evolves into a global crossroads while preserving the core identity established during those pivotal colonial years. From the Panama Canal to our multicultural society, and from our diplomatic strengths to our environmental challenges, Balboa’s influence shapes every aspect of modern Panamanian life."\n\n

Original:
"While previous articles in this series have explored the preparation for Balboa’s expedition and the dramatic journey itself, this piece examines how that historic moment continues to resonate in modern Panama. We’ll explore how the patterns of cultural cooperation, international trade, and diplomatic innovation first established in 1513 have evolved into contemporary strengths that define Panama’s place in today’s world. Through this lens, we’ll see how a 500-year-old discovery remains surprisingly relevant to current global challenges and opportunities."\n\n
Revised:
"This article explores how Balboa's historic moment continues to influence modern Panama, expanding on our previous coverage of his expedition and journey. We will examine how the patterns of cultural cooperation, international trade, and diplomatic innovation that began in 1513 have evolved into contemporary strengths that define Panama's role in today's world. By looking at this perspective, we can see how a 500-year-old discovery remains remarkably relevant to current global challenges and opportunities."\n\n

Original:
"The most visible evolution of Balboa’s discovery is the transformation from muddy jungle trails to the Panama Canal. That first glimpse of the Pacific sparked a centuries-long dream of connecting the oceans, progressing from the humble Camino Real to the sophisticated waterway we operate today. When you watch a massive container ship transit the canal, you’re witnessing the ultimate realization of a vision that began in 1513. Each year, over 14,000 vessels make this journey, carrying more than 300 million tons of cargo – a volume Balboa could never have imagined."\n\n
Revised:
"The most visible outcome of Balboa’s discovery is the evolution from muddy jungle trails to the Panama Canal. His first glimpse of the Pacific inspired a centuries-long dream of connecting the oceans, advancing from the simple Camino Real to today’s sophisticated waterway. Modern container ships transiting the canal fulfill a vision that began in 1513. More than 14,000 vessels carry over 300 million tons of cargo each year through the canal - a volume far beyond what Balboa could have imagined."\n\n

Original:
"The indigenous contributions that made Balboa’s discovery possible find echo in contemporary Panama’s relationship with its native communities. While significant challenges remain, there’s growing recognition of indigenous rights and the value of traditional knowledge. Modern development projects increasingly seek to incorporate indigenous perspectives, acknowledging that cultural cooperation remains as crucial today as it was five centuries ago."\n\n
Revised:
"The indigenous contributions that enabled Balboa’s discovery continue to influence Panama’s relationship with its native communities today. Despite significant challenges, we increasingly recognize indigenous rights and value traditional knowledge. Modern development projects now actively seek indigenous perspectives, acknowledging that cultural cooperation remains as vital today as it was 500 years ago."\n\n

Original:
"Perhaps most significantly, Panama continues to adapt and innovate while maintaining its core identity as a crossroads. The recent expansion of the Panama Canal, completed in 2016, demonstrates how we’re still building on Balboa’s legacy. Each technological advance, each new trade agreement, each cultural exchange program adds another layer to a story that began with that first glimpse of the Pacific."\n\n
Revised:
"Panama continues adapting and innovating while preserving its global crossroads identity. The 2016 Panama Canal expansion shows how we build on Balboa’s legacy. Every technological advance, trade agreement, and cultural exchange program adds to a story that began with that first view of the Pacific."\n\n

Original:
"Maritime law and international commerce still draw on precedents established in Balboa’s time. When nations negotiate rights of passage or discuss maritime sovereignty, they’re building on legal frameworks that began with Spain’s initial claims to the Pacific. Panama’s role in international maritime administration continues to influence global shipping regulations and practices."\n\n
Revised:
"Maritime law and international commerce build on precedents from Balboa’s era. Modern negotiations about passage rights and maritime sovereignty stem from legal frameworks that began with Spain’s initial Pacific claims. Panama’s influence on international maritime administration shapes global shipping regulations and practices."\n\n

Original:
"The first leg of the journey started deceptively easy. The expedition left Santa María la Antigua del Darién by ship, sailing west along the Caribbean coast to the territories of Chief Careta, one of Balboa’s most important indigenous allies. Here, in friendly territory, they established their first base camp – but the real challenges were about to begin."\n\n
Revised:
"The journey’s first leg began deceptively easily. The expedition departed Santa María la Antigua del Darién by ship, sailing west along the Caribbean coast to the territories of Chief Careta, one of Balboa’s key indigenous allies. They established their first base camp in this friendly territory - but the real challenges lay ahead."\n\n

Original:
"The human challenges were equally daunting. The expedition had to navigate through territories controlled by various indigenous groups, some friendly, others hostile. Balboa’s diplomatic skills proved crucial here. Rather than forcing his way through, he often sent indigenous negotiators ahead to arrange peaceful passage. When conflicts did arise, they were usually resolved through negotiation rather than violence – a stark contrast to many other Spanish expeditions of the era."\n\n
Revised:
"The expedition faced significant human challenges while navigating territories controlled by various friendly and hostile indigenous groups. Balboa’s diplomatic skills proved essential. Instead of forcing his way through, he sent Indigenous negotiators ahead to arrange a peaceful passage. He typically resolved conflicts through negotiation rather than violence, setting his expedition apart from many other Spanish explorations of the era."\n\n

Original:
"As we’ve seen in this detailed examination of the journey itself, the success of Balboa’s expedition challenges simplistic narratives of European conquest. Instead, it reveals a more nuanced history of cultural cooperation, diplomatic skill, and shared achievement that continues to resonate today. These themes of multicultural collaboration and strategic partnership would prove crucial not just for this discovery, but for Panama’s subsequent development as a crucial nexus of global commerce."\n\n
Revised:
"Our examination of Balboa’s journey challenges simple narratives of European conquest. Instead, it reveals a complex history of cultural cooperation, diplomatic skill, and shared achievement that still resonates today. These themes of multicultural collaboration and strategic partnership proved vital for this discovery and Panama’s growth as a center of global commerce."\n\n

Original:
"Gaspar de Espinosa played a pivotal role in Panama’s colonial history during the early 16th century. Born around 1484 in Medina de Rioseco, Spain, he studied law at the prestigious University of Salamanca. His legal expertise and noble background prepared him for an influential position in Spain’s expanding colonial empire."\n\n
Revised:
"Gaspar de Espinosa was pivotal in Panama’s colonial history during the early 16th century. Born around 1484 in Medina de Rioseco, Spain, he studied law at the prestigious University of Salamanca. His legal expertise and noble background prepared him for an influential position in Spain’s expanding colonial empire."\n\n

Original:
"As Panama’s first Chief Justice, Espinosa created the region’s first legal framework. He oversaw many significant cases, including Vasco Núñez de Balboa’s controversial trial in 1519. His decisions shaped colonial governance across Central America, establishing systems that influenced the region for centuries."\n\n
Revised:
"Espinosa created the region’s first legal framework as Panama's first Chief Justice. He oversaw many significant cases, including Vasco Núñez de Balboa’s controversial trial in 1519. His decisions shaped colonial governance across Central America, establishing systems that influenced the region for centuries."\n\n

Your task is to proofread and correct a full article.  To ensure that you stay focus, we will make the corrections one paragraph at a time.\n\n

Please concentrate on grammar, punctuation, reducing passive voice, and ensuring clarity and readability. Also take into account the samples of corrected text shared above while making your revisions.\n\n

We are going to start with the first paragraph. Here it is:\n\n
{chunk_text}\n\n

Please proofread this paragraph and respond with only the corrected paragraph text.  Do not include any additional text or comments.
"""

IMPROVE_READABILITY_CONTINUATION_PROMPT = """
Let's continue with the next paragraph.  Please proofread and correct it as needed.  Keep in mind the instructions provided at the beginning of our conversation.\n\n
Respond with only the corrected paragraph text.  Do not include any additional text or comments.\n\n
{chunk_text}
"""
