"use client";

import * as React from "react";
import { Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Search, SlidersHorizontal, Grid, List, X } from "lucide-react";
import { SearchBar } from "@/components/search/SearchBar";
import { VoiceRecorder } from "@/components/search/VoiceRecorder";
import { ImageUploader } from "@/components/search/ImageUploader";
import { FilterPanel } from "@/components/search/FilterPanel";
import { ProductCard } from "@/components/product/ProductCard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useSearch, useImageSearch } from "@/hooks/useApi";
import type { SearchFilters, SortOrder } from "@/types";

function SearchPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const query = searchParams.get("q") || "";
  const source = searchParams.get("source");
  
  const [showVoiceRecorder, setShowVoiceRecorder] = React.useState(false);
  const [showImageUploader, setShowImageUploader] = React.useState(false);
  const [viewMode, setViewMode] = React.useState<"grid" | "list">("grid");
  const [sortOrder, setSortOrder] = React.useState<SortOrder>("relevance");
  const [filters, setFilters] = React.useState<SearchFilters>({});
  const [imageSearchData, setImageSearchData] = React.useState<string | null>(null);
  
  // Demo user budget (in production, this would come from user profile)
  const monthlyBudget = 1000;

  // Check for image search on mount
  React.useEffect(() => {
    if (source === "image") {
      const imageData = sessionStorage.getItem("searchImage");
      if (imageData) {
        setImageSearchData(imageData);
      }
    }
  }, [source]);

  // Text search
  const {
    data: searchResults,
    isLoading: isSearching,
    error: searchError,
  } = useSearch(
    {
      query,
      filters,
      page: 1,
      pageSize: 20,
    },
    { enabled: !!query && !imageSearchData }
  );

  // Image search
  const imageSearch = useImageSearch();

  // Perform image search when image data is available
  React.useEffect(() => {
    if (imageSearchData && !imageSearch.isPending && !imageSearch.data) {
      imageSearch.mutate({ imageData: imageSearchData, filters });
    }
  }, [imageSearchData]);

  const products = imageSearchData 
    ? imageSearch.data?.products || []
    : searchResults?.products || [];
  const totalResults = imageSearchData
    ? imageSearch.data?.totalResults || 0
    : searchResults?.totalResults || 0;
  const isLoading = imageSearchData ? imageSearch.isPending : isSearching;

  const handleSearch = (newQuery: string) => {
    if (newQuery.trim()) {
      // Clear image search data
      setImageSearchData(null);
      sessionStorage.removeItem("searchImage");
      router.push(`/search?q=${encodeURIComponent(newQuery.trim())}`);
    }
  };

  const handleVoiceResult = (transcript: string) => {
    setShowVoiceRecorder(false);
    if (transcript.trim()) {
      setImageSearchData(null);
      sessionStorage.removeItem("searchImage");
      router.push(`/search?q=${encodeURIComponent(transcript.trim())}&source=voice`);
    }
  };

  const handleImageResult = (imageData: string) => {
    setShowImageUploader(false);
    setImageSearchData(imageData);
    sessionStorage.setItem("searchImage", imageData);
    router.push(`/search?source=image`);
    // Trigger new image search
    imageSearch.mutate({ imageData, filters });
  };

  const handleFiltersChange = (newFilters: SearchFilters) => {
    setFilters(newFilters);
    // Re-run image search with new filters if needed
    if (imageSearchData) {
      imageSearch.mutate({ imageData: imageSearchData, filters: newFilters });
    }
  };

  const clearImageSearch = () => {
    setImageSearchData(null);
    sessionStorage.removeItem("searchImage");
    router.push("/search");
  };

  const handleAddToCart = (productId: string) => {
    const cart = JSON.parse(localStorage.getItem("cart") || "[]");
    if (!cart.includes(productId)) {
      cart.push(productId);
      localStorage.setItem("cart", JSON.stringify(cart));
    }
  };

  const handleAddToWishlist = (productId: string) => {
    const wishlist = JSON.parse(localStorage.getItem("wishlist") || "[]");
    if (!wishlist.includes(productId)) {
      wishlist.push(productId);
      localStorage.setItem("wishlist", JSON.stringify(wishlist));
    }
  };

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Search Header */}
      <div className="mb-6">
        <SearchBar
          onSearch={handleSearch}
          onVoiceClick={() => setShowVoiceRecorder(true)}
          onImageClick={() => setShowImageUploader(true)}
          initialQuery={query}
          placeholder="Search products..."
        />
        
        {/* Image search indicator */}
        {imageSearchData && (
          <div className="mt-4 flex items-center gap-2">
            <Badge variant="secondary" className="gap-2">
              <img
                src={imageSearchData}
                alt="Search image"
                className="h-6 w-6 rounded object-cover"
              />
              Image search
              <button
                onClick={clearImageSearch}
                className="ml-1 rounded-full hover:bg-muted"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          </div>
        )}
      </div>

      <div className="flex gap-6">
        {/* Desktop Filters Sidebar */}
        <aside className="hidden w-64 flex-shrink-0 lg:block">
          <FilterPanel
            filters={filters}
            onFiltersChange={handleFiltersChange}
            sortOrder={sortOrder}
            onSortChange={setSortOrder}
            categories={[]}
            brands={[]}
          />
        </aside>

        {/* Main Content */}
        <div className="flex-1">
          {/* Results Header */}
          <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
            <div>
              {isLoading ? (
                <Skeleton className="h-6 w-32" />
              ) : (
                <p className="text-sm text-muted-foreground">
                  {totalResults > 0 ? (
                    <>
                      <span className="font-medium text-foreground">{totalResults}</span>{" "}
                      results {query && <>for &quot;{query}&quot;</>}
                    </>
                  ) : query || imageSearchData ? (
                    "No results found"
                  ) : (
                    "Enter a search query to find products"
                  )}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2">
              {/* Mobile Filter Button */}
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline" size="sm" className="lg:hidden">
                    <SlidersHorizontal className="mr-2 h-4 w-4" />
                    Filters
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="w-80">
                  <SheetHeader>
                    <SheetTitle>Filters</SheetTitle>
                  </SheetHeader>
                  <div className="mt-4">
                    <FilterPanel
                      filters={filters}
                      onFiltersChange={handleFiltersChange}
                      sortOrder={sortOrder}
                      onSortChange={setSortOrder}
                      categories={[]}
                      brands={[]}
                    />
                  </div>
                </SheetContent>
              </Sheet>

              {/* View Mode Toggle */}
              <div className="flex rounded-lg border">
                <Button
                  variant={viewMode === "grid" ? "secondary" : "ghost"}
                  size="sm"
                  className="rounded-r-none"
                  onClick={() => setViewMode("grid")}
                  aria-label="Grid view"
                >
                  <Grid className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === "list" ? "secondary" : "ghost"}
                  size="sm"
                  className="rounded-l-none"
                  onClick={() => setViewMode("list")}
                  aria-label="List view"
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Active Filters */}
          {(filters.categories?.length ||
            filters.brands?.length ||
            filters.priceRange ||
            filters.minRating ||
            filters.inStock) && (
            <div className="mb-4 flex flex-wrap gap-2">
              {filters.categories?.map((cat) => (
                <Badge key={cat} variant="secondary" className="gap-1">
                  {cat}
                  <button
                    onClick={() =>
                      handleFiltersChange({
                        ...filters,
                        categories: filters.categories?.filter((c) => c !== cat),
                      })
                    }
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
              {filters.brands?.map((brand) => (
                <Badge key={brand} variant="secondary" className="gap-1">
                  {brand}
                  <button
                    onClick={() =>
                      handleFiltersChange({
                        ...filters,
                        brands: filters.brands?.filter((b) => b !== brand),
                      })
                    }
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
              {filters.priceRange && (
                <Badge variant="secondary" className="gap-1">
                  ${filters.priceRange.min || 0} - ${filters.priceRange.max || "∞"}
                  <button
                    onClick={() =>
                      handleFiltersChange({ ...filters, priceRange: undefined })
                    }
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {filters.minRating && (
                <Badge variant="secondary" className="gap-1">
                  {filters.minRating}+ stars
                  <button
                    onClick={() =>
                      handleFiltersChange({ ...filters, minRating: undefined })
                    }
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {filters.inStock && (
                <Badge variant="secondary" className="gap-1">
                  In Stock
                  <button
                    onClick={() =>
                      handleFiltersChange({ ...filters, inStock: false })
                    }
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFilters({ sortBy: "relevance" })}
                className="h-6 text-xs"
              >
                Clear all
              </Button>
            </div>
          )}

          {/* Results Grid/List */}
          {isLoading ? (
            <div
              className={
                viewMode === "grid"
                  ? "grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                  : "space-y-4"
              }
            >
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="rounded-lg border p-4">
                  <Skeleton className="aspect-square w-full" />
                  <Skeleton className="mt-4 h-4 w-3/4" />
                  <Skeleton className="mt-2 h-4 w-1/2" />
                  <Skeleton className="mt-2 h-6 w-1/4" />
                </div>
              ))}
            </div>
          ) : products.length > 0 ? (
            <div
              className={
                viewMode === "grid"
                  ? "grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                  : "space-y-4"
              }
            >
              {products.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  monthlyBudget={monthlyBudget}
                  onAddToCart={() => handleAddToCart(product.id)}
                  onAddToWishlist={() => handleAddToWishlist(product.id)}
                  className={viewMode === "list" ? "flex-row" : undefined}
                />
              ))}
            </div>
          ) : (query || imageSearchData) ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Search className="mb-4 h-12 w-12 text-muted-foreground" />
              <h3 className="mb-2 text-lg font-medium">No results found</h3>
              <p className="text-sm text-muted-foreground">
                Try adjusting your search or filters to find what you&apos;re looking for
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Search className="mb-4 h-12 w-12 text-muted-foreground" />
              <h3 className="mb-2 text-lg font-medium">Start searching</h3>
              <p className="text-sm text-muted-foreground">
                Enter a query above or try voice/image search
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <VoiceRecorder
        isOpen={showVoiceRecorder}
        onClose={() => setShowVoiceRecorder(false)}
        onResult={handleVoiceResult}
      />

      <ImageUploader
        isOpen={showImageUploader}
        onClose={() => setShowImageUploader(false)}
        onUpload={handleImageResult}
      />
    </div>
  );
}

function SearchPageFallback() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Skeleton className="h-12 w-full" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-80 w-full" />
        ))}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<SearchPageFallback />}>
      <SearchPageContent />
    </Suspense>
  );
}
