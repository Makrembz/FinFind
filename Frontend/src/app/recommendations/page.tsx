"use client";

import * as React from "react";
import { Sparkles, TrendingUp, Clock, Tag, RefreshCw, Star, Flame } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { ProductCard } from "@/components/product/ProductCard";
import { ExplanationTooltip } from "@/components/product/ExplanationTooltip";
import { useRecommendations, useTrendingProducts, useUserBrowsingHistory, useUser } from "@/hooks/useApi";
import { useRecentlyViewed } from "@/hooks/useRecentlyViewed";
import type { ProductSearchResult } from "@/types";

// Demo user ID - in production this would come from auth
const DEMO_USER_ID = "013c3cb2-482a-55b0-9559-6688c3b78313";

export default function RecommendationsPage() {
  // Use a real user ID from Qdrant (in production, this would come from auth context)
  const userId = typeof window !== 'undefined' 
    ? localStorage.getItem("userId") || DEMO_USER_ID 
    : DEMO_USER_ID;
  
  // Get user profile for budget
  const { data: userData } = useUser(userId);
  const monthlyBudget = userData?.profile?.financialProfile?.monthlyBudget || 1000;

  const {
    data: recommendations,
    isLoading: isLoadingRecs,
    refetch: refetchRecs,
    isFetching: isFetchingRecs,
    isError: isRecError,
  } = useRecommendations(userId);

  const { 
    data: trendingData, 
    isLoading: isLoadingTrending,
    refetch: refetchTrending,
    isFetching: isFetchingTrending,
  } = useTrendingProducts();

  const { data: browsingHistory, isLoading: isLoadingHistory } =
    useUserBrowsingHistory(userId);
    
  // Get locally stored recently viewed products
  const { items: localRecentlyViewed } = useRecentlyViewed();

  const personalizedRecs = recommendations?.recommendations || [];
  const trending = trendingData?.recommendations || [];
  const recentlyViewed = browsingHistory?.interactions || [];
  
  // Use trending as fallback for personalized when no recommendations
  const displayRecs = personalizedRecs.length > 0 ? personalizedRecs : trending;
  const showingFallback = personalizedRecs.length === 0 && trending.length > 0;

  const handleAddToCart = (productId: string) => {
    const cart = JSON.parse(localStorage.getItem("cart") || "[]");
    if (!cart.includes(productId)) {
      cart.push(productId);
      localStorage.setItem("cart", JSON.stringify(cart));
      window.dispatchEvent(new Event("cartUpdated"));
    }
  };

  const handleAddToWishlist = (productId: string) => {
    const wishlist = JSON.parse(localStorage.getItem("wishlist") || "[]");
    if (!wishlist.includes(productId)) {
      wishlist.push(productId);
      localStorage.setItem("wishlist", JSON.stringify(wishlist));
      window.dispatchEvent(new Event("wishlistUpdated"));
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Sparkles className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold sm:text-3xl">For You</h1>
            <p className="text-muted-foreground">
              Personalized recommendations based on your preferences and budget
            </p>
          </div>
        </div>
      </div>

      <Tabs defaultValue="personalized" className="space-y-6">
        <TabsList>
          <TabsTrigger value="personalized" className="gap-2">
            <Sparkles className="h-4 w-4" />
            Personalized
          </TabsTrigger>
          <TabsTrigger value="trending" className="gap-2">
            <TrendingUp className="h-4 w-4" />
            Trending
          </TabsTrigger>
          <TabsTrigger value="deals" className="gap-2">
            <Tag className="h-4 w-4" />
            Deals
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <Clock className="h-4 w-4" />
            Recently Viewed
          </TabsTrigger>
        </TabsList>

        {/* Personalized Recommendations */}
        <TabsContent value="personalized" className="space-y-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {showingFallback 
                ? "Discover popular products while we learn your preferences"
                : "Products tailored to your interests and budget"}
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                refetchRecs();
                refetchTrending();
              }}
              disabled={isFetchingRecs || isFetchingTrending}
            >
              <RefreshCw
                className={`mr-2 h-4 w-4 ${(isFetchingRecs || isFetchingTrending) ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
          </div>

          {/* Fallback notice when showing trending */}
          {showingFallback && (
            <Card className="border-amber-500/20 bg-amber-500/5">
              <CardContent className="flex items-start gap-3 p-4">
                <Flame className="mt-0.5 h-5 w-5 text-amber-500" />
                <div>
                  <p className="font-medium">Featured Products</p>
                  <p className="text-sm text-muted-foreground">
                    Browse our top-rated and trending items. As you explore and interact with products, 
                    we&apos;ll personalize your recommendations!
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Overall explanation when personalized */}
          {!showingFallback && recommendations?.explanation && (
            <Card className="border-primary/20 bg-primary/5">
              <CardContent className="flex items-start gap-3 p-4">
                <Sparkles className="mt-0.5 h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">Why these recommendations?</p>
                  <p className="text-sm text-muted-foreground">
                    {recommendations.explanation}
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {(isLoadingRecs && isLoadingTrending) ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="rounded-lg border p-4">
                  <Skeleton className="aspect-square w-full" />
                  <Skeleton className="mt-4 h-4 w-3/4" />
                  <Skeleton className="mt-2 h-4 w-1/2" />
                  <Skeleton className="mt-2 h-6 w-1/4" />
                </div>
              ))}
            </div>
          ) : displayRecs.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {displayRecs.map((product: ProductSearchResult) => (
                <div key={product.id} className="relative">
                  <ProductCard
                    product={{
                      ...product,
                      matchScore: product.matchScore,
                      matchExplanation: product.matchExplanation,
                    }}
                    monthlyBudget={monthlyBudget}
                    onAddToCart={() => handleAddToCart(product.id)}
                    onAddToWishlist={() => handleAddToWishlist(product.id)}
                  />
                  {product.matchScore !== undefined && !showingFallback && (
                    <Badge
                      className="absolute right-2 top-2 z-10"
                      variant="default"
                    >
                      {Math.round(product.matchScore * 100)}% match
                    </Badge>
                  )}
                  {showingFallback && product.rating && product.rating >= 4.5 && (
                    <Badge
                      className="absolute right-2 top-2 z-10 bg-amber-500"
                      variant="default"
                    >
                      <Star className="mr-1 h-3 w-3 fill-current" />
                      Top Rated
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Sparkles className="mb-4 h-12 w-12 text-muted-foreground" />
                <h3 className="mb-2 text-lg font-medium">
                  No recommendations yet
                </h3>
                <p className="text-center text-sm text-muted-foreground">
                  Start browsing and adding items to get personalized recommendations
                </p>
                <Button className="mt-4" onClick={() => window.location.href = "/"}>
                  Start Shopping
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Trending Products */}
        <TabsContent value="trending" className="space-y-6">
          <p className="text-sm text-muted-foreground">
            Most popular products right now
          </p>

          {isLoadingTrending ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="rounded-lg border p-4">
                  <Skeleton className="aspect-square w-full" />
                  <Skeleton className="mt-4 h-4 w-3/4" />
                  <Skeleton className="mt-2 h-4 w-1/2" />
                </div>
              ))}
            </div>
          ) : trending.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {trending.map((product: any, index: number) => (
                <div key={product.id} className="relative">
                  <ProductCard
                    product={product}
                    monthlyBudget={monthlyBudget}
                    showExplanation={false}
                    onAddToCart={() => handleAddToCart(product.id)}
                    onAddToWishlist={() => handleAddToWishlist(product.id)}
                  />
                  <Badge
                    className="absolute left-2 top-2 z-10"
                    variant="secondary"
                  >
                    #{index + 1} Trending
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <TrendingUp className="mb-4 h-12 w-12 text-muted-foreground" />
                <h3 className="mb-2 text-lg font-medium">No trending products</h3>
                <p className="text-center text-sm text-muted-foreground">
                  Check back later for trending items
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Deals */}
        <TabsContent value="deals" className="space-y-6">
          <p className="text-sm text-muted-foreground">
            Best deals and discounts for you
          </p>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {/* Use displayRecs which includes trending as fallback */}
            {displayRecs
              .filter(
                (p: ProductSearchResult) =>
                  p.originalPrice && p.originalPrice > p.price
              )
              .map((product: ProductSearchResult) => {
                const discount = Math.round(
                  (1 - product.price / product.originalPrice!) * 100
                );
                return (
                  <div key={product.id} className="relative">
                    <ProductCard
                      product={product}
                      monthlyBudget={monthlyBudget}
                      showExplanation={false}
                      onAddToCart={() => handleAddToCart(product.id)}
                      onAddToWishlist={() => handleAddToWishlist(product.id)}
                    />
                    <Badge
                      className="absolute left-2 top-2 z-10"
                      variant="destructive"
                    >
                      -{discount}% OFF
                    </Badge>
                  </div>
                );
              })}
          </div>

          {displayRecs.filter(
            (p: ProductSearchResult) =>
              p.originalPrice && p.originalPrice > p.price
          ).length === 0 && (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Tag className="mb-4 h-12 w-12 text-muted-foreground" />
                <h3 className="mb-2 text-lg font-medium">No deals available</h3>
                <p className="text-center text-sm text-muted-foreground">
                  Check back later for special offers
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Recently Viewed */}
        <TabsContent value="history" className="space-y-6">
          <p className="text-sm text-muted-foreground">
            Products you&apos;ve recently viewed
          </p>

          {isLoadingHistory ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="rounded-lg border p-4">
                  <Skeleton className="aspect-square w-full" />
                  <Skeleton className="mt-4 h-4 w-3/4" />
                  <Skeleton className="mt-2 h-4 w-1/2" />
                </div>
              ))}
            </div>
          ) : localRecentlyViewed.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {localRecentlyViewed.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  monthlyBudget={monthlyBudget}
                  showExplanation={false}
                  onAddToCart={() => handleAddToCart(product.id)}
                  onAddToWishlist={() => handleAddToWishlist(product.id)}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Clock className="mb-4 h-12 w-12 text-muted-foreground" />
                <h3 className="mb-2 text-lg font-medium">No recent history</h3>
                <p className="text-center text-sm text-muted-foreground">
                  Products you view will appear here
                </p>
                <Button className="mt-4" onClick={() => window.location.href = "/"}>
                  Start Browsing
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Budget Overview Card */}
      <Card className="mt-12">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Your Budget Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 sm:grid-cols-3">
            <div className="text-center">
              <p className="text-3xl font-bold text-primary">
                ${monthlyBudget.toLocaleString()}
              </p>
              <p className="text-sm text-muted-foreground">Monthly Budget</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">
                {personalizedRecs.filter(
                  (p: ProductSearchResult) => p.price <= monthlyBudget * 0.2
                ).length}
              </p>
              <p className="text-sm text-muted-foreground">Affordable Items</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-orange-600">
                {personalizedRecs.filter(
                  (p: ProductSearchResult) => p.price > monthlyBudget * 0.5
                ).length}
              </p>
              <p className="text-sm text-muted-foreground">Premium Items</p>
            </div>
          </div>
          <div className="mt-4 text-center">
            <Button variant="outline" onClick={() => window.location.href = "/profile"}>
              Adjust Budget Settings
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
