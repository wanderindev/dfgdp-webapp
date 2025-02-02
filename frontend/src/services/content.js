// noinspection JSUnusedGlobalSymbols


const API_URL = `${import.meta.env.VITE_API_URL}/content/graphql`;
// noinspection JSUnusedLocalSymbols
const UPLOAD_URL = `${import.meta.env.VITE_UPLOAD_URL}`;

// GraphQL query/mutation strings
const QUERIES = {
  GET_TAXONOMIES: `
    query GetTaxonomies {
      taxonomies {
        id
        name
        description
        slug
        categories {
          id
          name
          description
          taxonomyId
          slug
        }
      }
    }
  `,

  GET_TAGS: `
    query GetTags(
      $page: Int, 
      $pageSize: Int, 
      $status: ContentStatus, 
      $search: String, 
      $sort: String, 
      $dir: String
    ) {
      tags(
        page: $page, 
        pageSize: $pageSize, 
        status: $status, 
        search: $search, 
        sort: $sort, 
        dir: $dir
      ) {
        tags {
          id
          name
          status
        }
        total
        pages
        currentPage
      }
    }
  `,

  GET_ALL_TAGS: `
    query GetAllTags($status: ContentStatus) {
      allTags(status: $status) {
        id
        name
        status
      }
    }
  `,

  GET_SUGGESTIONS: `
    query GetArticleSuggestions(
      $page: Int, 
      $pageSize: Int, 
      $status: ContentStatus, 
      $search: String, 
      $sort: String, 
      $dir: String
    ) {
      articleSuggestions(
        page: $page, 
        pageSize: $pageSize, 
        status: $status, 
        search: $search, 
        sort: $sort, 
        dir: $dir
      ) {
        suggestions {
          id
          title
          mainTopic
          subTopics
          pointOfView
          status
          research {
            id
            status
          }
          category {
            id
            name
          }
        }
        total
        pages
        currentPage
      }
    }
  `,

  BULK_GENERATE_ARTICLES: `
    mutation BulkGenerateArticles($suggestionId: Int!) {
      bulkGenerateArticles(suggestionId: $suggestionId) {
        success
        message
      }
    }
  `,

  GET_RESEARCH: `
    query GetResearch(
      $page: Int,
      $pageSize: Int,
      $status: ContentStatus,
      $search: String,
      $sort: String,
      $dir: String
    ) {
      research(
        page: $page,
        pageSize: $pageSize,
        status: $status,
        search: $search,
        sort: $sort,
        dir: $dir
      ) {
        research {
          id
          content
          status
          suggestion {
            id
            title
          }
          articles {
            id
          }
        }
        total
        pages
        currentPage
      }
    }
  `,

  GET_ARTICLES: `
    query GetArticles(
      $page: Int,
      $pageSize: Int,
      $status: ContentStatus,
      $search: String,
      $sort: String,
      $dir: String
    ) {
      articles(
        page: $page,
        pageSize: $pageSize,
        status: $status,
        search: $search,
        sort: $sort,
        dir: $dir
      ) {
        articles {
          id
          title
          content
          excerpt
          aiSummary
          status
          research {
            id
            suggestion {
              id
              title
            }
          }
          tags {
            id
            name
          }
          category {
            id
            name
          }
          approvedById
          approvedAt
          publishedAt
        }
        total
        pages
        currentPage
      }
    }
  `,

  GET_MEDIA_SUGGESTIONS: `
    query GetMediaSuggestions {
      mediaSuggestions {
        id
        research {
          id
          suggestion {
            title
          }
        }
        commonsCategories
        searchQueries
        illustrationTopics
        reasoning
        candidates {
          id
          status
        }
      }
    }
  `,

  GET_MEDIA_CANDIDATES: `
    query GetMediaCandidates($status: ContentStatus) {
      mediaCandidates(status: $status) {
        id
        commonsId
        commonsUrl
        title
        description
        author
        license
        licenseUrl
        width
        height
        mimeType
        fileSize
        status
        suggestion {
          id
          research {
            suggestion {
              title
            }
          }
        }
      }
    }
  `,

  GET_MEDIA_LIBRARY: `
    query GetMediaLibrary($mediaType: MediaType) {
      mediaLibrary(mediaType: $mediaType) {
        id
        filename
        originalFilename
        filePath
        publicUrl
        fileSize
        mimeType
        mediaType
        source
        title
        caption
        altText
        externalUrl
        width
        height
        attribution
        instagramMediaType
      }
    }
  `,
};

const MUTATIONS = {
  CREATE_TAXONOMY: `
    mutation CreateTaxonomy($input: TaxonomyInput!) {
      createTaxonomy(input: $input) {
        id
        name
        description
      }
    }
  `,

  UPDATE_TAXONOMY: `
    mutation UpdateTaxonomy($id: Int!, $input: TaxonomyInput!) {
      updateTaxonomy(id: $id, input: $input) {
        id
        name
        description
      }
    }
  `,

  DELETE_TAXONOMY: `
    mutation DeleteTaxonomy($id: Int!) {
      deleteTaxonomy(id: $id)
    }
  `,

  CREATE_CATEGORY: `
    mutation CreateCategory($input: CategoryInput!) {
      createCategory(input: $input) {
        id
        name
        description
        taxonomyId
      }
    }
  `,

  UPDATE_CATEGORY: `
    mutation UpdateCategory($id: Int!, $input: CategoryInput!) {
      updateCategory(id: $id, input: $input) {
        id
        name
        description
        taxonomyId
      }
    }
  `,

  DELETE_CATEGORY: `
    mutation DeleteCategory($id: Int!) {
      deleteCategory(id: $id)
    }
  `,

  CREATE_TAG: `
    mutation CreateTag($input: TagInput!) {
      createTag(input: $input) {
        id
        name
        status
      }
    }
  `,

  UPDATE_TAG: `
    mutation UpdateTag($id: Int!, $input: TagInput!) {
      updateTag(id: $id, input: $input) {
        id
        name
        status
      }
    }
  `,

  UPDATE_TAG_STATUS: `
    mutation UpdateTagStatus($id: Int!, $status: ContentStatus!) {
      updateTagStatus(id: $id, status: $status) {
        id
        name
        status
      }
    }
  `,

  GENERATE_SUGGESTIONS: `
    mutation GenerateSuggestions($categoryId: Int!, $count: Int!) {
      generateSuggestions(categoryId: $categoryId, count: $count) {
        success
        message
      }
    }
  `,

  UPDATE_SUGGESTION: `
    mutation UpdateSuggestion($id: Int!, $input: ArticleSuggestionInput!) {
      updateSuggestion(id: $id, input: $input) {
        id
        title
        mainTopic
        subTopics
        pointOfView
        status
      }
    }
  `,

  UPDATE_SUGGESTION_STATUS: `
    mutation UpdateSuggestionStatus($id: Int!, $status: ContentStatus!) {
      updateSuggestionStatus(id: $id, status: $status) {
        id
        status
      }
    }
  `,

  GENERATE_RESEARCH: `
    mutation GenerateResearch($suggestionId: Int!) {
      generateResearch(suggestionId: $suggestionId) {
        success
        message
      }
    }
  `,

  UPDATE_RESEARCH: `
    mutation UpdateResearch($id: Int!, $content: String!) {
      updateResearch(id: $id, content: $content) {
        id
        content
        status
      }
    }
  `,

  UPDATE_RESEARCH_STATUS: `
    mutation UpdateResearchStatus($id: Int!, $status: ContentStatus!) {
      updateResearchStatus(id: $id, status: $status) {
        id
        status
      }
    }
  `,

  GENERATE_ARTICLE: `
    mutation GenerateArticle($researchId: Int!) {
      generateArticle(researchId: $researchId) {
        success
        message
      }
    }
  `,

  GENERATE_MEDIA_SUGGESTIONS: `
    mutation GenerateMediaSuggestions($researchId: Int!) {
      generateMediaSuggestions(researchId: $researchId) {
        success
        message
      }
    }
  `,

  UPDATE_ARTICLE: `
    mutation UpdateArticle($id: Int!, $input: ArticleInput!) {
      updateArticle(id: $id, input: $input) {
        id
        title
        content
        excerpt
        aiSummary
        status
        tags {
          id
          name
        }
      }
    }
  `,

  UPDATE_ARTICLE_STATUS: `
    mutation UpdateArticleStatus($id: Int!, $status: ContentStatus!) {
      updateArticleStatus(id: $id, status: $status) {
        id
        status
      }
    }
  `,

  GENERATE_STORY_PROMOTION: `
    mutation GenerateStoryPromotion($articleId: Int!) {
      generateStoryPromotion(articleId: $articleId) {
        success
        message
      }
    }
  `,

  GENERATE_DID_YOU_KNOW_POSTS: `
    mutation GenerateDidYouKnowPosts($articleId: Int!, $count: Int!) {
      generateDidYouKnowPosts(articleId: $articleId, count: $count) {
        success
        message
      }
    }
  `,

  FETCH_MEDIA_CANDIDATES: `
    mutation FetchMediaCandidates($suggestionId: Int!, $maxPerQuery: Int!) {
      fetchMediaCandidates(suggestionId: $suggestionId, maxPerQuery: $maxPerQuery) {
        success
        message
      }
    }
  `,

  UPDATE_CANDIDATE_STATUS: `
    mutation UpdateCandidateStatus($id: Int!, $status: ContentStatus!, $notes: String) {
      updateCandidateStatus(id: $id, status: $status, notes: $notes) {
        id
        status
      }
    }
  `,

  APPROVE_AND_CREATE_MEDIA: `
    mutation ApproveCandidateAndCreateMedia($id: Int!, $notes: String) {
      approveCandidateAndCreateMedia(id: $id, notes: $notes) {
        id
        status
        mediaId
      }
    }
  `,

  UPDATE_MEDIA_METADATA: `
    mutation UpdateMediaMetadata($id: Int!, $input: MediaMetadataInput!) {
      updateMediaMetadata(id: $id, input: $input) {
        id
        title
        caption
        altText
        instagramMediaType
      }
    }
  `,

  UPLOAD_MEDIA: `
    mutation UploadMedia($file: Upload!) {
      uploadMedia(file: $file) {
        id
        filename
        filePath
      }
    }
  `,
};

// Helper function for GraphQL requests
async function fetchGraphQL(query, variables = {}) {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      query,
      variables,
    }),
  });

  const json = await response.json();

  if (json.errors) {
    throw new Error(json.errors[0].message);
  }

  return json.data;
}

// Content service functions
export const contentService = {
  // Taxonomy operations
  async getTaxonomies() {
    const data = await fetchGraphQL(QUERIES.GET_TAXONOMIES);
    return data.taxonomies;
  },

  async createTaxonomy(input) {
    const data = await fetchGraphQL(MUTATIONS.CREATE_TAXONOMY, { input });
    return data.createTaxonomy;
  },

  async updateTaxonomy(id, taxonomyData) {
    const input = {
      name: taxonomyData.name,
      description: taxonomyData.description
    };
    const data = await fetchGraphQL(MUTATIONS.UPDATE_TAXONOMY, { id, input });
    return data.updateTaxonomy;
  },

  async deleteTaxonomy(id) {
    const data = await fetchGraphQL(MUTATIONS.DELETE_TAXONOMY, { id });
    return data.deleteTaxonomy;
  },

  // Category operations
  async createCategory(categoryData) {
    const input = {
      name: categoryData.name,
      description: categoryData.description,
      taxonomyId: categoryData.taxonomyId
    };
    const data = await fetchGraphQL(MUTATIONS.CREATE_CATEGORY, { input });
    return data.createCategory;
  },

  async updateCategory(id, categoryData) {
    const input = {
      name: categoryData.name,
      description: categoryData.description,
      taxonomyId: categoryData.taxonomyId
    };
    const data = await fetchGraphQL(MUTATIONS.UPDATE_CATEGORY, { id, input });
    return data.updateCategory;
  },

  async deleteCategory(id) {
    const data = await fetchGraphQL(MUTATIONS.DELETE_CATEGORY, { id });
    return data.deleteCategory;
  },

  async getTags(page, pageSize, status, search, sort, dir) {
    const variables = { page, pageSize, status, search, sort, dir };
    const data = await fetchGraphQL(QUERIES.GET_TAGS, variables);
    return data.tags;
  },

  async getAllTags(status = null) {
    const variables = { status };
    const data = await fetchGraphQL(QUERIES.GET_ALL_TAGS, variables);
    return data.allTags;
  },

  async createTag(input) {
    const data = await fetchGraphQL(MUTATIONS.CREATE_TAG, { input });
    return data.createTag;
  },

  async updateTag(id, input) {
    const data = await fetchGraphQL(MUTATIONS.UPDATE_TAG, { id, input });
    return data.updateTag;
  },

  async updateTagStatus(id, status) {
    const data = await fetchGraphQL(MUTATIONS.UPDATE_TAG_STATUS, { id, status });
    return data.updateTagStatus;
  },

  // Get article suggestions
  async getSuggestions(page, pageSize, status, search, sort, dir) {
    const variables = { page, pageSize, status, search, sort, dir };

    const data = await fetchGraphQL(QUERIES.GET_SUGGESTIONS, variables);
    // noinspection JSUnresolvedReference
    return data.articleSuggestions;
  },

  // Generate new suggestions
  async generateSuggestions({ categoryId, count }) {
    const data = await fetchGraphQL(MUTATIONS.GENERATE_SUGGESTIONS, {
      categoryId,
      count,
    });
    return data.generateSuggestions;
  },

  // Update suggestion
  async updateSuggestion(id, suggestionData) {
    const input = {
      title: suggestionData.title,
      mainTopic: suggestionData.mainTopic,
      subTopics: suggestionData.subTopics,
      pointOfView: suggestionData.pointOfView,
    };
    const data = await fetchGraphQL(MUTATIONS.UPDATE_SUGGESTION, { id, input });
    return data.updateSuggestion;
  },

  // Update suggestion status
  async updateSuggestionStatus(id, status) {
    const data = await fetchGraphQL(MUTATIONS.UPDATE_SUGGESTION_STATUS, { id, status });
    return data.updateSuggestionStatus;
  },

  async bulkGenerateArticles(suggestionId) {
    const variables = { suggestionId };
    const data = await fetchGraphQL(MUTATIONS.BULK_GENERATE_ARTICLES, variables);
    return data.bulkGenerateArticles;
  },

  // Generate research for a suggestion
  async generateResearch(suggestionId) {
    const data = await fetchGraphQL(MUTATIONS.GENERATE_RESEARCH, { suggestionId });
    return data.generateResearch;
  },

   // Research operations
  async getResearch(page, pageSize, status, search, sort, dir) {
    const variables = { page, pageSize, status, search, sort, dir };
    const data = await fetchGraphQL(QUERIES.GET_RESEARCH, variables);
    return data.research;
  },

  async updateResearch(id, { content }) {
    const data = await fetchGraphQL(MUTATIONS.UPDATE_RESEARCH, {
      id,
      content
    });
    return data.updateResearch;
  },

  async updateResearchStatus(id, status) {
    const data = await fetchGraphQL(MUTATIONS.UPDATE_RESEARCH_STATUS, {
      id,
      status
    });
    return data.updateResearchStatus;
  },

  async generateArticle(researchId) {
    const data = await fetchGraphQL(MUTATIONS.GENERATE_ARTICLE, {
      researchId
    });
    return data.generateArticle;
  },

  async generateMediaSuggestions(researchId) {
    const data = await fetchGraphQL(MUTATIONS.GENERATE_MEDIA_SUGGESTIONS, {
      researchId
    });
    return data.generateMediaSuggestions;
  },

  // Get articles
  async getArticles(page, pageSize, status, search, sort, dir) {
    const variables = { page, pageSize, status, search, sort, dir };
    const data = await fetchGraphQL(QUERIES.GET_ARTICLES, variables);
    // noinspection JSUnresolvedReference
    return data.articles;
  },

  // Update article
  async updateArticle(id, articleData) {
    const input = {
      title: articleData.title,
      content: articleData.content,
      excerpt: articleData.excerpt,
      aiSummary: articleData.aiSummary,
      tagIds: articleData.tagIds,
    };
    const data = await fetchGraphQL(MUTATIONS.UPDATE_ARTICLE, { id, input });
    return data.updateArticle;
  },

  // Update article status
  async updateArticleStatus(id, status) {
    const data = await fetchGraphQL(MUTATIONS.UPDATE_ARTICLE_STATUS, {
      id,
      status
    });
    return data.updateArticleStatus;
  },

  // Generate Instagram story promotion
  async generateStoryPromotion(articleId) {
    const data = await fetchGraphQL(MUTATIONS.GENERATE_STORY_PROMOTION, {
      articleId
    });
    return data.generateStoryPromotion;
  },

  // Generate Did You Know posts
  async generateDidYouKnowPosts(articleId, count = 3) {
    const data = await fetchGraphQL(MUTATIONS.GENERATE_DID_YOU_KNOW_POSTS, {
      articleId,
      count
    });
    return data.generateDidYouKnowPosts;
  },

  // Get all media suggestions
  async getMediaSuggestions() {
    const data = await fetchGraphQL(QUERIES.GET_MEDIA_SUGGESTIONS);
    // noinspection JSUnresolvedReference
    return data.mediaSuggestions;
  },

  // Fetch candidates for a suggestion
  async fetchCandidates(suggestionId, maxPerQuery = 5) {
    const data = await fetchGraphQL(MUTATIONS.FETCH_MEDIA_CANDIDATES, {
      suggestionId,
      maxPerQuery,
    });
    // noinspection JSUnresolvedReference
    return data.fetchMediaCandidates;
  },

  // Helper to count candidates by status
  getCandidateStatusCounts(candidates) {
    return candidates.reduce((acc, candidate) => {
      acc[candidate.status] = (acc[candidate.status] || 0) + 1;
      return acc;
    }, {});
  },

  // Get media candidates with optional status filter
  async getMediaCandidates(status = null) {
    const data = await fetchGraphQL(QUERIES.GET_MEDIA_CANDIDATES, { status });
    // noinspection JSUnresolvedReference
    return data.mediaCandidates;
  },

  // Update candidate status
  async updateCandidateStatus(id, status, notes = null) {
    const data = await fetchGraphQL(MUTATIONS.UPDATE_CANDIDATE_STATUS, {
      id,
      status,
      notes,
    });
    return data.updateCandidateStatus;
  },

  // Approve candidate and create media entry
  async approveCandidateAndCreateMedia(id, notes = null) {
    const data = await fetchGraphQL(MUTATIONS.APPROVE_AND_CREATE_MEDIA, {
      id,
      notes,
    });
    return data.approveCandidateAndCreateMedia;
  },

  // Get media library items with optional type filter
  async getMediaLibrary(mediaType = null) {
    const data = await fetchGraphQL(QUERIES.GET_MEDIA_LIBRARY, { mediaType });
    // noinspection JSUnresolvedReference
    return data.mediaLibrary;
  },

  // Update media metadata
  async updateMediaMetadata(id, metadata) {
    const data = await fetchGraphQL(MUTATIONS.UPDATE_MEDIA_METADATA, {
      id,
      input: metadata,
    });
    return data.updateMediaMetadata;
  },

  // Upload new media file
  async uploadMedia(file) {
    // Note: We'll need to handle file upload differently since GraphQL
    // doesn't directly support file uploads. We'll use a regular REST
    // endpoint for this.
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${import.meta.env.VITE_API_URL}/content/api/media/upload`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to upload media');
    }

    return response.json();
  },
};