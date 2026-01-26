"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { TrendingDown, ChevronLeft, ChevronRight, Star } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, formatCurrency, getStarRating } from "@/lib/utils";
import type { Product, ProductSearchResult } from "@/types";

// Accept either Product or ProductSearchResult
type AlternativeProduct = Product | ProductSearchResult;

interface AlternativeSuggestionProps {
  originalPrice: number;
  alternatives: AlternativeProduct[];
  isLoading?: boolean;
  title?: string;
  className?: string;
}

export function AlternativeSuggestion({
  originalPrice,
  alternatives,
  isLoading = false,
  title = "More affordable alternatives",
  className,
}: AlternativeSuggestionProps) {
  const scrollContainerRef = React.useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = React.useState(false);
  const [canScrollRight, setCanScrollRight] = React.useState(true);

  const checkScrollButtons = () => {
    const container = scrollContainerRef.current;
    if (container) {
      setCanScrollLeft(container.scrollLeft > 0);
      setCanScrollRight(
        container.scrollLeft < container.scrollWidth - container.clientWidth - 10
      );
    }
  };

  const scroll = (direction: "left" | "right") => {
    const container = scrollContainerRef.current;
    if (container) {
      const scrollAmount = container.clientWidth * 0.8;
      container.scrollBy({
        left: direction === "left" ? -scrollAmount : scrollAmount,
        behavior: "smooth",
      });
    }
  };

  React.useEffect(() => {
    checkScrollButtons();
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener("scroll", checkScrollButtons);
      window.addEventListener("resize", checkScrollButtons);
      return () => {
        container.removeEventListener("scroll", checkScrollButtons);
        window.removeEventListener("resize", checkScrollButtons);
      };
    }
  }, [alternatives]);

  if (isLoading) {
    return (
      <div className={cn("space-y-4", className)}>
        <div className="flex items-center gap-2">
          <TrendingDown className="h-5 w-5 text-green-500" />
          <span className="font-medium">{title}</span>
        </div>
        <div className="flex gap-4 overflow-hidden">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} className="w-48 flex-shrink-0">
              <CardContent className="p-3">
                <Skeleton className="aspect-square w-full" />
                <Skeleton className="mt-2 h-4 w-full" />
                <Skeleton className="mt-1 h-4 w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (alternatives.length === 0) {
    return null;
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingDown className="h-5 w-5 text-green-500" />
          <span className="font-medium">{title}</span>
          <Badge variant="secondary" className="text-xs">
            {alternatives.length} found
          </Badge>
        </div>
        
        {/* Scroll buttons */}
        <div className="flex gap-1">
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            disabled={!canScrollLeft}
            onClick={() => scroll("left")}
            aria-label="Scroll left"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            disabled={!canScrollRight}
            onClick={() => scroll("right")}
            aria-label="Scroll right"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Horizontal scrolling alternatives */}
      <div
        ref={scrollContainerRef}
        className="flex gap-4 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-muted-foreground/20"
        style={{ scrollbarWidth: "thin" }}
      >
        {alternatives.map((product) => {
          const savings = originalPrice - product.price;
          const savingsPercent = Math.round((savings / originalPrice) * 100);
          const starRating = getStarRating(product.rating ?? 0);

          return (
            <Link
              key={product.id}
              href={`/product/${product.id}`}
              className="group flex-shrink-0"
            >
              <Card className="w-48 transition-shadow hover:shadow-md">
                <CardContent className="p-3">
                  {/* Image */}
                  <div className="relative aspect-square overflow-hidden rounded-md bg-muted">
                    {product.imageUrl ? (
                      <Image
                        src={product.imageUrl}
                        alt={product.name}
                        fill
                        className="object-cover transition-transform group-hover:scale-105"
                        sizes="192px"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center text-muted-foreground">
                        No image
                      </div>
                    )}
                    
                    {/* Savings badge */}
                    <Badge
                      className="absolute right-1 top-1 bg-green-500 text-xs text-white"
                    >
                      Save {savingsPercent}%
                    </Badge>
                  </div>

                  {/* Product info */}
                  <div className="mt-3 space-y-1">
                    <h4 className="line-clamp-2 text-sm font-medium group-hover:underline">
                      {product.name}
                    </h4>
                    
                    {/* Rating */}
                    {product.rating !== undefined && (
                      <div className="flex items-center gap-1">
                        {Array.from({ length: starRating.full }).map((_, i) => (
                          <Star
                            key={i}
                            className="h-3 w-3 fill-yellow-400 text-yellow-400"
                          />
                        ))}
                        {Array.from({ length: 5 - starRating.full }).map((_, i) => (
                          <Star key={`e-${i}`} className="h-3 w-3 text-muted" />
                        ))}
                        <span className="text-xs text-muted-foreground">
                          ({product.reviewCount ?? 0})
                        </span>
                      </div>
                    )}

                    {/* Price */}
                    <div className="flex items-baseline gap-2">
                      <span className="font-bold text-green-600 dark:text-green-400">
                        {formatCurrency(product.price)}
                      </span>
                    </div>

                    {/* Savings amount */}
                    <p className="text-xs text-muted-foreground">
                      Save {formatCurrency(savings)} vs original
                    </p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
