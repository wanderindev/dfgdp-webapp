const API_URL = `${import.meta.env.VITE_API_URL}/content/graphql`;

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
    query GetTags($status: ContentStatus) {
      tags(status: $status) {
        id
        name
        status
      }
    }
  `,

  GET_SUGGESTIONS: `
    query GetSuggestions($status: ContentStatus) {
      articleSuggestions(status: $status) {
        id
        title
        mainTopic
        subTopics
        pointOfView
        level
        status
        category {
          id
          name
        }
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
    mutation GenerateSuggestions($categoryId: Int!, $level: String!, $count: Int!) {
      generateSuggestions(categoryId: $categoryId, level: $level, count: $count) {
        id
        title
        mainTopic
        subTopics
        pointOfView
        level
        status
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
        level
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
        id
        status
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

  // Tag operations
  async getTags(status = null) {
    const data = await fetchGraphQL(QUERIES.GET_TAGS, { status });
    return data.tags;
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
  async getSuggestions(status = null) {
    const data = await fetchGraphQL(QUERIES.GET_SUGGESTIONS, { status });
    return data.articleSuggestions;
  },

  // Generate new suggestions
  async generateSuggestions({ categoryId, level, count }) {
    const data = await fetchGraphQL(MUTATIONS.GENERATE_SUGGESTIONS, {
      categoryId,
      level,
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
      level: suggestionData.level,
    };
    const data = await fetchGraphQL(MUTATIONS.UPDATE_SUGGESTION, { id, input });
    return data.updateSuggestion;
  },

  // Update suggestion status
  async updateSuggestionStatus(id, status) {
    const data = await fetchGraphQL(MUTATIONS.UPDATE_SUGGESTION_STATUS, { id, status });
    return data.updateSuggestionStatus;
  },

  // Generate research for a suggestion
  async generateResearch(suggestionId) {
    const data = await fetchGraphQL(MUTATIONS.GENERATE_RESEARCH, { suggestionId });
    return data.generateResearch;
  },
};