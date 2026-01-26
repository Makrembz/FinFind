"use client";

import * as React from "react";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { X, SlidersHorizontal, ChevronDown, ChevronUp } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import type { SearchFilters, SortOrder } from "@/types";

interface FilterPanelProps {
  filters: SearchFilters;
  onFiltersChange: (filters: SearchFilters) => void;
  sortOrder: SortOrder;
  onSortChange: (sort: SortOrder) => void;
  categories?: string[];
  brands?: string[];
  priceRange?: { min: number; max: number };
  className?: string;
}

export function FilterPanel({
  filters,
  onFiltersChange,
  sortOrder,
  onSortChange,
  categories = [],
  brands = [],
  priceRange = { min: 0, max: 1000 },
  className,
}: FilterPanelProps) {
  const [isExpanded, setIsExpanded] = React.useState(true);
  const [localPriceRange, setLocalPriceRange] = React.useState<[number, number]>([
    filters.priceRange?.min ?? priceRange.min,
    filters.priceRange?.max ?? priceRange.max,
  ]);

  // Count active filters
  const activeFilterCount = [
    filters.categories?.length ?? 0,
    filters.brands?.length ?? 0,
    filters.priceRange ? 1 : 0,
    filters.minRating ? 1 : 0,
    filters.inStock !== undefined ? 1 : 0,
  ].reduce((a, b) => a + b, 0);

  // Handle price range change with debounce
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (
        localPriceRange[0] !== priceRange.min ||
        localPriceRange[1] !== priceRange.max
      ) {
        onFiltersChange({
          ...filters,
          priceRange: {
            min: localPriceRange[0],
            max: localPriceRange[1],
          },
        });
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [localPriceRange]);

  // Toggle category filter
  const toggleCategory = (category: string) => {
    const current = filters.categories ?? [];
    const updated = current.includes(category)
      ? current.filter((c) => c !== category)
      : [...current, category];
    onFiltersChange({
      ...filters,
      categories: updated.length > 0 ? updated : undefined,
    });
  };

  // Toggle brand filter
  const toggleBrand = (brand: string) => {
    const current = filters.brands ?? [];
    const updated = current.includes(brand)
      ? current.filter((b) => b !== brand)
      : [...current, brand];
    onFiltersChange({
      ...filters,
      brands: updated.length > 0 ? updated : undefined,
    });
  };

  // Set rating filter
  const setRating = (rating: number | undefined) => {
    onFiltersChange({
      ...filters,
      minRating: rating,
    });
  };

  // Toggle in stock filter
  const toggleInStock = () => {
    onFiltersChange({
      ...filters,
      inStock: filters.inStock === undefined ? true : undefined,
    });
  };

  // Clear all filters
  const clearFilters = () => {
    setLocalPriceRange([priceRange.min, priceRange.max]);
    onFiltersChange({});
  };

  return (
    <div className={cn("rounded-lg border bg-card", className)}>
      {/* Header */}
      <div
        className="flex cursor-pointer items-center justify-between p-4"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="h-5 w-5" />
          <span className="font-medium">Filters</span>
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="ml-2">
              {activeFilterCount}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {activeFilterCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                clearFilters();
              }}
            >
              Clear all
            </Button>
          )}
          {isExpanded ? (
            <ChevronUp className="h-5 w-5" />
          ) : (
            <ChevronDown className="h-5 w-5" />
          )}
        </div>
      </div>

      {/* Filter content */}
      {isExpanded && (
        <div className="space-y-6 border-t p-4">
          {/* Sort order */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Sort by</label>
            <Select value={sortOrder} onValueChange={(v) => onSortChange(v as SortOrder)}>
              <SelectTrigger>
                <SelectValue placeholder="Select sort order" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="relevance">Relevance</SelectItem>
                <SelectItem value="price_low">Price: Low to High</SelectItem>
                <SelectItem value="price_high">Price: High to Low</SelectItem>
                <SelectItem value="rating">Rating</SelectItem>
                <SelectItem value="newest">Newest</SelectItem>
                <SelectItem value="popularity">Popularity</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Price range */}
          <div className="space-y-4">
            <label className="text-sm font-medium">Price Range</label>
            <Slider
              min={priceRange.min}
              max={priceRange.max}
              step={10}
              value={localPriceRange}
              onValueChange={(value) => setLocalPriceRange(value as [number, number])}
              className="w-full"
            />
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>{formatCurrency(localPriceRange[0])}</span>
              <span>{formatCurrency(localPriceRange[1])}</span>
            </div>
          </div>

          {/* Categories */}
          {categories.length > 0 && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Categories</label>
              <div className="flex flex-wrap gap-2">
                {categories.map((category) => (
                  <Badge
                    key={category}
                    variant={
                      filters.categories?.includes(category)
                        ? "default"
                        : "outline"
                    }
                    className="cursor-pointer"
                    onClick={() => toggleCategory(category)}
                  >
                    {category}
                    {filters.categories?.includes(category) && (
                      <X className="ml-1 h-3 w-3" />
                    )}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Brands */}
          {brands.length > 0 && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Brands</label>
              <div className="flex flex-wrap gap-2">
                {brands.slice(0, 10).map((brand) => (
                  <Badge
                    key={brand}
                    variant={
                      filters.brands?.includes(brand) ? "default" : "outline"
                    }
                    className="cursor-pointer"
                    onClick={() => toggleBrand(brand)}
                  >
                    {brand}
                    {filters.brands?.includes(brand) && (
                      <X className="ml-1 h-3 w-3" />
                    )}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Rating */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Minimum Rating</label>
            <div className="flex gap-2">
              {[4, 3, 2, 1].map((rating) => (
                <Button
                  key={rating}
                  variant={filters.minRating === rating ? "default" : "outline"}
                  size="sm"
                  onClick={() =>
                    setRating(filters.minRating === rating ? undefined : rating)
                  }
                >
                  {rating}+ ★
                </Button>
              ))}
            </div>
          </div>

          {/* In Stock */}
          <div className="flex items-center gap-2">
            <Button
              variant={filters.inStock ? "default" : "outline"}
              size="sm"
              onClick={toggleInStock}
            >
              {filters.inStock && <span className="mr-1">✓</span>}
              In Stock Only
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
