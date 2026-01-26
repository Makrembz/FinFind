/**
 * TypeScript type definitions for FinFind
 */

// ============================================================================
// Product Types
// ============================================================================

export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  originalPrice?: number;
  currency: string;
  category: string;
  subcategory?: string;
  brand: string;
  rating: number;
  reviewCount: number;
  imageUrl: string;
  imageUrls: string[];
  inStock: boolean;
  stockQuantity?: number;
  paymentOptions: string[];
  tags: string[];
  attributes: ProductAttributes;
  createdAt: string;
  updatedAt?: string;
}

export interface ProductAttributes {
  color?: string;
  size?: string;
  material?: string;
  model?: string;
  weight?: string;
  dimensions?: string;
  [key: string]: string | undefined;
}

export interface ProductSearchResult {
  id: string;
  name: string;
  description?: string;
  price: number;
  originalPrice?: number;
  category: string;
  subcategory?: string;
  brand?: string;
  rating?: number;
  reviewCount?: number;
  imageUrl?: string;
  inStock: boolean;
  relevanceScore: number;
  matchExplanation?: string;
  matchScore?: number;
}

export interface ProductReview {
  id: string;
  userId: string;
  userName?: string;
  productId: string;
  rating: number;
  title?: string;
  content: string;
  comment?: string; // Alias for content
  helpfulCount: number;
  verifiedPurchase: boolean;
  createdAt: string;
  date?: string; // Alias for createdAt
}

// Alias for backwards compatibility
export type Review = ProductReview;

// ============================================================================
// User Types
// ============================================================================

export interface User {
  id: string;
  email?: string;
  name?: string;
  avatarUrl?: string;
  financialProfile: FinancialProfile;
  preferences: UserPreferences;
  createdAt: string;
  updatedAt?: string;
}

export interface FinancialProfile {
  monthlyIncome?: number;
  monthlyBudget?: number;
  creditScoreRange?: 'poor' | 'fair' | 'good' | 'excellent';
  preferredPaymentMethods: string[];
  riskTolerance?: 'conservative' | 'moderate' | 'aggressive';
  savingsGoal?: number;
}

export interface UserPreferences {
  favoriteCategories: string[];
  favoriteBrands: string[];
  priceSensitivity?: 'low' | 'medium' | 'high';
  qualityPreference?: 'budget' | 'mid-range' | 'premium';
  ecoFriendly: boolean;
  localPreference: boolean;
}

export interface UserInteraction {
  id: string;
  userId: string;
  productId: string;
  interactionType: InteractionType;
  timestamp: string;
  metadata?: Record<string, unknown>;
  sessionId?: string;
}

export type InteractionType = 
  | 'view' 
  | 'click' 
  | 'add_to_cart' 
  | 'remove_from_cart' 
  | 'purchase' 
  | 'wishlist' 
  | 'review' 
  | 'share';

// ============================================================================
// Search Types
// ============================================================================

export interface SearchFilters {
  categories?: string[];
  brands?: string[];
  priceRange?: {
    min?: number;
    max?: number;
  };
  minRating?: number;
  inStock?: boolean;
  paymentMethods?: string[];
  tags?: string[];
  sortBy?: string;
}

export interface SearchRequest {
  query: string;
  filters?: SearchFilters;
  sort?: SortOrder;
  page?: number;
  pageSize?: number;
  useMmr?: boolean;
  diversity?: number;
  includeExplanation?: boolean;
  userId?: string;
}

export type SortOrder = 
  | 'relevance' 
  | 'price_low' 
  | 'price_high' 
  | 'rating' 
  | 'newest' 
  | 'popularity';

export interface SearchResponse {
  success: boolean;
  query: string;
  interpretedQuery?: string;
  products: ProductSearchResult[];
  totalResults: number;
  page: number;
  pageSize: number;
  totalPages: number;
  filtersApplied: Record<string, unknown>;
  searchTimeMs: number;
  requestId: string;
}

export interface SearchSuggestion {
  text: string;
  type: 'query' | 'category' | 'brand' | 'popular';
}

// ============================================================================
// Recommendation Types
// ============================================================================

export interface Recommendation {
  product: ProductSearchResult;
  score: number;
  reasons: string[];
  affordabilityScore?: number;
  personalizationFactors: string[];
}

export interface RecommendationResponse {
  success: boolean;
  userId: string;
  recommendations: ProductSearchResult[];
  reasons: Record<string, string[]>;
  explanation?: string;
  total: number;
  requestId: string;
}

export interface ExplanationResponse {
  success: boolean;
  userId: string;
  productId: string;
  summary: string;
  factors: ExplanationFactor[];
  factorScores: Record<string, number>;
  confidenceScore: number;
  requestId: string;
}

export interface ExplanationFactor {
  type: string;
  description: string;
  weight: number;
}

export interface AlternativesResponse {
  success: boolean;
  originalProductId: string;
  criteria: string;
  alternatives: ProductSearchResult[];
  reasons: Record<string, string>;
  total: number;
  requestId: string;
}

// ============================================================================
// Chat/Agent Types
// ============================================================================

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  products?: ProductSearchResult[];
  metadata?: Record<string, unknown>;
}

export interface ChatRequest {
  message: string;
  sessionId?: string;
  userId?: string;
  context?: Record<string, unknown>;
  includeProducts?: boolean;
}

export interface ChatResponse {
  success: boolean;
  message: string;
  sessionId: string;
  agentUsed?: string;
  products: ProductSearchResult[];
  followUpSuggestions: string[];
  confidence?: number;
  processingTimeMs: number;
  requestId: string;
}

export interface ChatSession {
  sessionId: string;
  userId?: string;
  messages: ChatMessage[];
  createdAt: string;
  lastActivity: string;
  context: Record<string, unknown>;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  requestId?: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// ============================================================================
// UI Component Types
// ============================================================================

export interface FilterOption {
  label: string;
  value: string;
  count?: number;
}

export interface PriceRange {
  min: number;
  max: number;
  step?: number;
}

export interface AffordabilityInfo {
  isAffordable: boolean;
  percentageOfBudget: number;
  monthlyPayment?: number;
  recommendation: 'within_budget' | 'slightly_over' | 'over_budget' | 'consider_alternatives';
}
