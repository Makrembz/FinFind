/**
 * React Query hooks for API interactions
 */

"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  searchApi,
  productApi,
  userApi,
  recommendationsApi,
  chatApi,
  multimodalApi,
} from "@/lib/api";
import type {
  SearchRequest,
  SearchFilters,
  ChatRequest,
  User,
} from "@/types";

// ============================================================================
// Query Keys
// ============================================================================

export const queryKeys = {
  search: (query: string, filters?: SearchFilters) => ["search", query, filters],
  suggestions: (query: string) => ["suggestions", query],
  product: (id: string) => ["product", id],
  productReviews: (id: string, page: number) => ["product", id, "reviews", page],
  similarProducts: (id: string) => ["product", id, "similar"],
  user: (id: string) => ["user", id],
  userInteractions: (id: string, page: number) => ["user", id, "interactions", page],
  recommendations: (userId: string, category?: string) => ["recommendations", userId, category],
  chatSession: (sessionId: string) => ["chat", sessionId],
  agents: () => ["agents"],
};

// ============================================================================
// Search Hooks
// ============================================================================

export function useSearch(
  request: SearchRequest,
  options?: { enabled?: boolean }
) {
  const enabled = options?.enabled ?? (request.query.length > 0);
  return useQuery({
    queryKey: queryKeys.search(request.query, request.filters),
    queryFn: () => searchApi.searchProducts(request),
    enabled,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function useSearchSuggestions(query: string) {
  return useQuery({
    queryKey: queryKeys.suggestions(query),
    queryFn: () => searchApi.getSuggestions(query),
    enabled: query.length >= 2,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}

export function useVoiceSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      audioBlob,
      filters,
    }: {
      audioBlob: Blob;
      filters?: SearchFilters;
    }) => searchApi.searchWithVoice(audioBlob, filters),
    onSuccess: (data) => {
      // Cache the results
      queryClient.setQueryData(queryKeys.search(data.query, {}), data);
    },
  });
}

export function useImageSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      imageFile,
      imageData,
      filters,
    }: {
      imageFile?: File;
      imageData?: string;
      filters?: SearchFilters;
    }) => {
      // If imageData (base64) is provided, convert it to a File
      if (imageData) {
        const response = await fetch(imageData);
        const blob = await response.blob();
        const file = new File([blob], "image.jpg", { type: "image/jpeg" });
        return searchApi.searchWithImage(file, filters);
      }
      if (imageFile) {
        return searchApi.searchWithImage(imageFile, filters);
      }
      throw new Error("Either imageFile or imageData must be provided");
    },
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.search("image-search", {}), data);
    },
  });
}

// ============================================================================
// Product Hooks
// ============================================================================

export function useProduct(productId: string) {
  return useQuery({
    queryKey: queryKeys.product(productId),
    queryFn: () => productApi.getProduct(productId),
    enabled: !!productId,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}

export function useProductReviews(productId: string, page: number = 1) {
  return useQuery({
    queryKey: queryKeys.productReviews(productId, page),
    queryFn: () => productApi.getReviews(productId, page),
    enabled: !!productId,
    staleTime: 1000 * 60 * 5,
  });
}

export function useSimilarProducts(productId: string, limit: number = 10) {
  return useQuery({
    queryKey: queryKeys.similarProducts(productId),
    queryFn: () => productApi.getSimilarProducts(productId, limit),
    enabled: !!productId,
    staleTime: 1000 * 60 * 10,
  });
}

export function useLogProductInteraction() {
  return useMutation({
    mutationFn: ({
      productId,
      interactionType,
      metadata,
    }: {
      productId: string;
      interactionType: string;
      metadata?: Record<string, unknown>;
    }) => productApi.logInteraction(productId, interactionType, metadata),
  });
}

// ============================================================================
// User Hooks
// ============================================================================

export function useUser(userId: string) {
  return useQuery({
    queryKey: queryKeys.user(userId),
    queryFn: () => userApi.getProfile(userId),
    enabled: !!userId,
    staleTime: 1000 * 60 * 5,
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, updates }: { userId: string; updates: Partial<User> }) =>
      userApi.updateProfile(userId, updates),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(queryKeys.user(variables.userId), data);
    },
  });
}

export function useUserInteractions(userId: string, page: number = 1) {
  return useQuery({
    queryKey: queryKeys.userInteractions(userId, page),
    queryFn: () => userApi.getInteractions(userId, page),
    enabled: !!userId,
    staleTime: 1000 * 60 * 2,
  });
}

// ============================================================================
// Recommendations Hooks
// ============================================================================

export function useRecommendations(
  userId: string,
  options?: {
    category?: string;
    limit?: number;
    includeReasons?: boolean;
  }
) {
  return useQuery({
    queryKey: queryKeys.recommendations(userId, options?.category),
    queryFn: () => recommendationsApi.getRecommendations(userId, options),
    enabled: !!userId,
    staleTime: 1000 * 60 * 5,
  });
}

export function useExplainRecommendation() {
  return useMutation({
    mutationFn: ({ userId, productId }: { userId: string; productId: string }) =>
      recommendationsApi.explainRecommendation(userId, productId),
  });
}

export function useAlternatives(
  productId: string,
  criteria: "cheaper" | "better_rated" | "similar" | "balanced" = "balanced"
) {
  return useQuery({
    queryKey: ["alternatives", productId, criteria],
    queryFn: () => recommendationsApi.getAlternatives(productId, criteria),
    enabled: !!productId,
    staleTime: 1000 * 60 * 10,
  });
}

// ============================================================================
// Chat Hooks
// ============================================================================

export function useSendMessage(sessionId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ChatRequest | { message: string }) => {
      // Handle simplified message format
      if ("message" in data && !("sessionId" in data)) {
        return chatApi.sendMessage({
          sessionId: sessionId || "",
          message: data.message,
          userId: "013c3cb2-482a-55b0-9559-6688c3b78313",
        });
      }
      return chatApi.sendMessage(data as ChatRequest);
    },
    onSuccess: (data) => {
      const sid = sessionId || data.sessionId;
      if (sid) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.chatSession(sid),
        });
        queryClient.invalidateQueries({
          queryKey: ["chatHistory", sid],
        });
      }
    },
  });
}

export function useChatSession(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.chatSession(sessionId),
    queryFn: () => chatApi.getSession(sessionId),
    enabled: !!sessionId,
    staleTime: 0, // Always fetch fresh
  });
}

export function useAgents() {
  return useQuery({
    queryKey: queryKeys.agents(),
    queryFn: () => chatApi.getAgents(),
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
}

// ============================================================================
// Multimodal Hooks
// ============================================================================

export function useTranscribeAudio() {
  return useMutation({
    mutationFn: (audioBlob: Blob) => multimodalApi.transcribeAudio(audioBlob),
  });
}

export function useProcessImage() {
  return useMutation({
    mutationFn: (imageFile: File) => multimodalApi.processImage(imageFile),
  });
}

// ============================================================================
// Additional Hooks for Pages
// ============================================================================

export function useRelatedProducts(productId: string) {
  return useQuery({
    queryKey: ["relatedProducts", productId],
    queryFn: () => productApi.getSimilarProducts(productId, 8),
    enabled: !!productId,
    staleTime: 1000 * 60 * 10,
  });
}

export function useTrendingProducts() {
  return useQuery({
    queryKey: ["trending"],
    queryFn: async () => {
      // Placeholder - in production this would call the API
      return [];
    },
    staleTime: 1000 * 60 * 5,
  });
}

export function useUserBrowsingHistory(userId: string) {
  return useQuery({
    queryKey: ["browsingHistory", userId],
    queryFn: () => userApi.getInteractions(userId, 1),
    enabled: !!userId,
    staleTime: 1000 * 60 * 2,
  });
}

export function useUpdateUserPreferences(userId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (preferences: Partial<import("@/types").UserPreferences>) =>
      userApi.updatePreferences(userId, preferences),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.user(userId) });
    },
  });
}

export function useUpdateFinancialProfile(userId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (profile: Partial<import("@/types").FinancialProfile>) =>
      userApi.updateFinancialProfile(userId, profile),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.user(userId) });
    },
  });
}

export function useCreateSession() {
  return useMutation({
    mutationFn: (userId: string) => chatApi.createSession(userId),
  });
}

export function useChatHistory(sessionId?: string) {
  return useQuery({
    queryKey: ["chatHistory", sessionId],
    queryFn: () => chatApi.getSession(sessionId!),
    enabled: !!sessionId,
    staleTime: 0,
  });
}
