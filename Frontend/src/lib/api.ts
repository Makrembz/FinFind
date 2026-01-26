/**
 * API client for FinFind backend
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from "axios";
import type {
  SearchRequest,
  SearchResponse,
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
// Search API
// ============================================================================

export const searchApi = {
  /**
   * Search products with text query
   */
  async searchProducts(request: SearchRequest): Promise<SearchResponse> {
    const response = await apiClient.post<SearchResponse>("/search/products", {
      query: request.query,
      filters: request.filters,
      limit: request.pageSize || 20,
      offset: ((request.page || 1) - 1) * (request.pageSize || 20),
      use_mmr: request.useMmr ?? true,
      diversity: request.diversity ?? 0.3,
    });
    return response.data;
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

    const response = await apiClient.post<SearchResponse>("/multimodal/voice/search", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
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

    const response = await apiClient.post<SearchResponse>("/multimodal/image/search", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  /**
   * Get search suggestions
   */
  async getSuggestions(query: string): Promise<{ suggestions: string[] }> {
    const response = await apiClient.get<{ suggestions: string[] }>("/search/suggestions", {
      params: { q: query },
    });
    return response.data;
  },
};

// ============================================================================
// Product API
// ============================================================================

export const productApi = {
  /**
   * Get product details
   */
  async getProduct(productId: string): Promise<{ product: Product; similarProducts: ProductSearchResult[] }> {
    const response = await apiClient.get(`/products/${productId}`);
    return response.data;
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
    return response.data;
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
    const response = await apiClient.put(`/users/${userId}/preferences`, preferences);
    return response.data;
  },

  /**
   * Update financial profile
   */
  async updateFinancialProfile(
    userId: string,
    profile: Partial<import("@/types").FinancialProfile>
  ): Promise<{ profile: User }> {
    const response = await apiClient.put(`/users/${userId}/financial`, profile);
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
    const response = await apiClient.get<RecommendationResponse>(
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
    return response.data;
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
    const response = await apiClient.get<AlternativesResponse>(
      `/recommendations/alternatives/${productId}`,
      { params: { criteria, limit } }
    );
    return response.data;
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
    const response = await apiClient.post<ChatResponse>("/agents/query", {
      query: request.message,
      session_id: request.sessionId,
      context: request.context,
      include_explanations: request.includeProducts ?? true,
    });
    return response.data;
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
