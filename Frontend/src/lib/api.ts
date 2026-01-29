/**
 * API client for FinFind backend
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from "axios";
import type {
  SearchRequest,
  SearchResponse,
  SearchFilters,
  Product,
  ProductReview,
  User,
  UserInteraction,
  RecommendationResponse,
  ExplanationResponse,
  AlternativesResponse,
  ChatRequest,
  ChatResponse,
  ChatSession,
  ProductSearchResult,
} from "@/types";

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for adding auth headers
apiClient.interceptors.request.use(
  (config) => {
    // Add user ID from localStorage if available
    if (typeof window !== "undefined") {
      const userId = localStorage.getItem("userId");
      if (userId) {
        config.headers["X-User-ID"] = userId;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const message = error.response?.data 
      ? (error.response.data as { detail?: string }).detail || "An error occurred"
      : error.message;
    console.error("API Error:", message);
    return Promise.reject(new Error(message));
  }
);

// ============================================================================
// Utility Functions
// ============================================================================

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function transformProduct(product: any): ProductSearchResult {
  return {
    id: product.id,
    name: product.name || product.title,
    description: product.description,
    price: product.price,
    originalPrice: product.original_price || product.originalPrice,
    category: product.category,
    subcategory: product.subcategory,
    brand: product.brand,
    rating: product.rating || product.rating_avg,
    reviewCount: product.review_count || product.reviewCount,
    imageUrl: product.image_url || product.imageUrl,
    inStock: product.in_stock ?? product.inStock ?? true,
    relevanceScore: product.relevance_score || product.relevanceScore || 0,
    matchExplanation: product.match_reason || product.matchExplanation,
    matchScore: product.match_score || product.matchScore,
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function transformSearchResponse(data: any): SearchResponse {
  return {
    success: data.success,
    query: data.query,
    interpretedQuery: data.interpreted_query || data.interpretedQuery,
    products: (data.products || []).map(transformProduct),
    totalResults: data.total_results ?? data.totalResults ?? 0,
    page: data.page ?? 1,
    pageSize: data.page_size ?? data.pageSize ?? 20,
    totalPages: data.total_pages ?? data.totalPages ?? 1,
    filtersApplied: data.filters_applied || data.filtersApplied || {},
    searchTimeMs: data.search_time_ms ?? data.searchTimeMs ?? 0,
    requestId: data.request_id || data.requestId || '',
  };
}

// ============================================================================
// Search API
// ============================================================================

// Transform frontend filters to backend format
function transformFilters(filters?: SearchFilters) {
  if (!filters) return undefined;
  return {
    min_price: filters.priceRange?.min,
    max_price: filters.priceRange?.max,
    categories: filters.categories,
    brands: filters.brands,
    min_rating: filters.minRating,
    in_stock: filters.inStock,
  };
}

export const searchApi = {
  /**
   * Search products with text query
   */
  async searchProducts(request: SearchRequest): Promise<SearchResponse> {
    const response = await apiClient.post("/search/products", {
      query: request.query,
      filters: transformFilters(request.filters),
      limit: request.pageSize || 20,
      offset: ((request.page || 1) - 1) * (request.pageSize || 20),
      use_mmr: request.useMmr ?? true,
      diversity: request.diversity ?? 0.3,
    });
    return transformSearchResponse(response.data);
  },

  /**
   * Search with voice input
   */
  async searchWithVoice(audioBlob: Blob, filters?: SearchRequest["filters"]): Promise<SearchResponse> {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");
    if (filters) {
      formData.append("filters", JSON.stringify(filters));
    }

    const response = await apiClient.post("/multimodal/voice/search", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return transformSearchResponse(response.data);
  },

  /**
   * Search with image
   */
  async searchWithImage(imageFile: File, filters?: SearchRequest["filters"]): Promise<SearchResponse> {
    const formData = new FormData();
    formData.append("image", imageFile);
    if (filters) {
      formData.append("filters", JSON.stringify(filters));
    }

    const response = await apiClient.post("/multimodal/image/search", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return transformSearchResponse(response.data);
  },

  /**
   * Get search suggestions
   */
  async getSuggestions(query: string): Promise<{ suggestions: string[] }> {
    const response = await apiClient.get<{ suggestions: string[] }>("/search/suggest", {
      params: { q: query },
    });
    return response.data;
  },
};

// ============================================================================
// Product API
// ============================================================================

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function transformFullProduct(product: any): Product {
  return {
    id: product.id,
    name: product.name || product.title,
    description: product.description || '',
    price: product.price,
    originalPrice: product.original_price || product.originalPrice,
    currency: product.currency || 'USD',
    category: product.category,
    subcategory: product.subcategory,
    brand: product.brand || '',
    rating: product.rating || product.rating_avg || 0,
    reviewCount: product.review_count || product.reviewCount || 0,
    imageUrl: product.image_url || product.imageUrl || '',
    imageUrls: product.image_urls || product.imageUrls || [],
    inStock: product.in_stock ?? product.inStock ?? true,
    stockQuantity: product.stock_quantity || product.stockQuantity,
    paymentOptions: product.payment_options || product.paymentOptions || [],
    tags: product.tags || [],
    attributes: product.attributes || {},
    createdAt: product.created_at || product.createdAt || new Date().toISOString(),
    updatedAt: product.updated_at || product.updatedAt,
  };
}

export const productApi = {
  /**
   * Get product details
   */
  async getProduct(productId: string): Promise<{ product: Product; similarProducts: ProductSearchResult[] }> {
    const response = await apiClient.get(`/products/${productId}`);
    const data = response.data;
    return {
      product: transformFullProduct(data.product || data),
      similarProducts: (data.similar_products || data.similarProducts || []).map(transformProduct),
    };
  },

  /**
   * Get product reviews
   */
  async getReviews(
    productId: string,
    page: number = 1,
    pageSize: number = 20,
    sortBy: string = "newest"
  ): Promise<{ reviews: ProductReview[]; total: number; averageRating: number }> {
    const response = await apiClient.get(`/products/${productId}/reviews`, {
      params: { page, page_size: pageSize, sort_by: sortBy },
    });
    return response.data;
  },

  /**
   * Get similar products
   */
  async getSimilarProducts(
    productId: string,
    limit: number = 10
  ): Promise<ProductSearchResult[]> {
    const response = await apiClient.get(`/products/${productId}/similar`, {
      params: { limit },
    });
    const products = response.data.products || response.data;
    return (Array.isArray(products) ? products : []).map(transformProduct);
  },

  /**
   * Log product interaction
   */
  async logInteraction(
    productId: string,
    interactionType: string,
    metadata?: Record<string, unknown>
  ): Promise<void> {
    await apiClient.post(`/products/${productId}/interact`, {
      interaction_type: interactionType,
      metadata,
    });
  },
};

// ============================================================================
// User API
// ============================================================================

export const userApi = {
  /**
   * Get user profile
   */
  async getProfile(userId: string): Promise<{ profile: User }> {
    const response = await apiClient.get(`/users/${userId}/profile`);
    return response.data;
  },

  /**
   * Update user profile
   */
  async updateProfile(userId: string, updates: Partial<User>): Promise<{ profile: User }> {
    const response = await apiClient.put(`/users/${userId}/profile`, updates);
    return response.data;
  },

  /**
   * Get user interactions
   */
  async getInteractions(
    userId: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<{ interactions: UserInteraction[]; total: number }> {
    const response = await apiClient.get(`/users/${userId}/interactions`, {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  /**
   * Log user interaction
   */
  async logInteraction(
    userId: string,
    productId: string,
    interactionType: string,
    metadata?: Record<string, unknown>
  ): Promise<void> {
    await apiClient.post(`/users/${userId}/interactions`, {
      product_id: productId,
      interaction_type: interactionType,
      metadata,
    });
  },

  /**
   * Update user preferences
   */
  async updatePreferences(
    userId: string,
    preferences: Partial<import("@/types").UserPreferences>
  ): Promise<{ profile: User }> {
    const response = await apiClient.put(`/users/${userId}/profile`, {
      preferences: {
        favorite_categories: preferences.favoriteCategories,
        favorite_brands: preferences.favoriteBrands,
        price_sensitivity: preferences.priceSensitivity,
        quality_preference: preferences.qualityPreference,
        eco_friendly: preferences.ecoFriendly,
        local_preference: preferences.localPreference,
      }
    });
    return response.data;
  },

  /**
   * Update financial profile
   */
  async updateFinancialProfile(
    userId: string,
    profile: Partial<import("@/types").FinancialProfile>
  ): Promise<{ profile: User }> {
    const response = await apiClient.put(`/users/${userId}/profile`, {
      financial_profile: {
        monthly_income: profile.monthlyIncome,
        monthly_budget: profile.monthlyBudget,
        credit_score_range: profile.creditScoreRange,
        preferred_payment_methods: profile.preferredPaymentMethods,
        risk_tolerance: profile.riskTolerance,
        savings_goal: profile.savingsGoal,
      }
    });
    return response.data;
  },
};

// ============================================================================
// Recommendations API
// ============================================================================

export const recommendationsApi = {
  /**
   * Get personalized recommendations
   */
  async getRecommendations(
    userId: string,
    options?: {
      category?: string;
      limit?: number;
      includeReasons?: boolean;
      diversity?: number;
    }
  ): Promise<RecommendationResponse> {
    const response = await apiClient.get(
      `/recommendations/${userId}`,
      {
        params: {
          category: options?.category,
          limit: options?.limit || 10,
          include_reasons: options?.includeReasons ?? true,
          diversity: options?.diversity ?? 0.3,
        },
      }
    );
    const data = response.data;
    const reasons = data.reasons || {};
    
    // Map recommendations and attach reasons as matchExplanation
    const recommendations = (data.recommendations || []).map((product: any) => {
      const transformed = transformProduct(product);
      const productReasons = reasons[transformed.id];
      if (productReasons && productReasons.length > 0) {
        transformed.matchExplanation = productReasons.join('. ');
      }
      return transformed;
    });
    
    return {
      ...data,
      recommendations,
    };
  },

  /**
   * Get explanation for a recommendation
   */
  async explainRecommendation(
    userId: string,
    productId: string
  ): Promise<ExplanationResponse> {
    const response = await apiClient.post<ExplanationResponse>(
      "/recommendations/explain",
      { user_id: userId, product_id: productId }
    );
    return response.data;
  },

  /**
   * Get alternative products
   */
  async getAlternatives(
    productId: string,
    criteria: "cheaper" | "better_rated" | "similar" | "balanced" = "balanced",
    limit: number = 5
  ): Promise<AlternativesResponse> {
    const response = await apiClient.get(
      `/recommendations/alternatives/${productId}`,
      { params: { criteria, limit } }
    );
    const data = response.data;
    return {
      ...data,
      alternatives: (data.alternatives || []).map(transformProduct),
    };
  },
};

// ============================================================================
// Chat/Agent API
// ============================================================================

export const chatApi = {
  /**
   * Create a new chat session
   */
  async createSession(userId: string): Promise<{ sessionId: string }> {
    const response = await apiClient.post("/agents/session", { user_id: userId });
    return response.data;
  },

  /**
   * Send chat message
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post("/agents/query", {
      query: request.message,
      session_id: request.sessionId,
      context: request.context,
      include_explanations: request.includeProducts ?? true,
    });
    const data = response.data;
    return {
      ...data,
      products: (data.products || []).map(transformProduct),
    };
  },

  /**
   * Get session history
   */
  async getSession(sessionId: string): Promise<ChatSession> {
    const response = await apiClient.get<{ session: ChatSession }>(
      `/agents/session/${sessionId}`
    );
    return response.data.session;
  },

  /**
   * Get available agents
   */
  async getAgents(): Promise<{ agents: { name: string; description: string }[] }> {
    const response = await apiClient.get("/agents/list");
    return response.data;
  },
};

// ============================================================================
// Multimodal API
// ============================================================================

export const multimodalApi = {
  /**
   * Transcribe audio to text
   */
  async transcribeAudio(audioBlob: Blob): Promise<{ text: string; confidence: number }> {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");

    const response = await apiClient.post("/multimodal/voice/transcribe", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  /**
   * Process image for search
   */
  async processImage(imageFile: File): Promise<{ embedding: number[]; description: string }> {
    const formData = new FormData();
    formData.append("image", imageFile);

    const response = await apiClient.post("/multimodal/image/process", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },
};

// Export the axios instance for custom requests
export { apiClient };
