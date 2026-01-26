"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { Star, Heart, ShoppingCart, Info, TrendingDown } from "lucide-react";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn, formatCurrency, getStarRating, calculateAffordability } from "@/lib/utils";
import type { ProductSearchResult } from "@/types";

interface ProductCardProps {
  product: ProductSearchResult;
  monthlyBudget?: number;
  showExplanation?: boolean;
  onAddToCart?: () => void;
  onAddToWishlist?: () => void;
  onShowAlternatives?: () => void;
  className?: string;
}

export function ProductCard({
  product,
  monthlyBudget,
  showExplanation = true,
  onAddToCart,
  onAddToWishlist,
  onShowAlternatives,
  className,
}: ProductCardProps) {
  const affordability = calculateAffordability(product.price, monthlyBudget);
  const starRating = getStarRating(product.rating ?? 0);
  const hasDiscount = product.originalPrice && product.originalPrice > product.price;
  const discountPercent = hasDiscount
    ? Math.round((1 - product.price / product.originalPrice!) * 100)
    : 0;

  return (
    <Card
      className={cn(
        "group relative flex flex-col overflow-hidden transition-shadow hover:shadow-lg",
        className
      )}
    >
      {/* Image */}
      <Link href={`/product/${product.id}`} className="relative aspect-square">
        <div className="relative h-full w-full bg-muted">
          {product.imageUrl ? (
            <Image
              src={product.imageUrl}
              alt={product.name}
              fill
              className="object-cover transition-transform group-hover:scale-105"
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <ShoppingCart className="h-12 w-12 text-muted-foreground" />
            </div>
          )}
        </div>

        {/* Badges */}
        <div className="absolute left-2 top-2 flex flex-col gap-1">
          {hasDiscount && (
            <Badge variant="destructive" className="text-xs">
              -{discountPercent}%
            </Badge>
          )}
          {!product.inStock && (
            <Badge variant="secondary" className="text-xs">
              Out of Stock
            </Badge>
          )}
        </div>

        {/* Wishlist button */}
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-2 top-2 h-8 w-8 bg-white/80 opacity-0 transition-opacity group-hover:opacity-100 dark:bg-black/80"
          onClick={(e) => {
            e.preventDefault();
            onAddToWishlist?.();
          }}
          aria-label="Add to wishlist"
        >
          <Heart className="h-4 w-4" />
        </Button>
      </Link>

      <CardContent className="flex flex-1 flex-col gap-2 p-4">
        {/* Category & Brand */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{product.category}</span>
          {product.brand && (
            <>
              <span>•</span>
              <span>{product.brand}</span>
            </>
          )}
        </div>

        {/* Title */}
        <Link
          href={`/product/${product.id}`}
          className="line-clamp-2 font-medium hover:underline"
        >
          {product.name}
        </Link>

        {/* Rating */}
        {product.rating !== undefined && (
          <div className="flex items-center gap-1">
            <div className="flex">
              {Array.from({ length: starRating.full }).map((_, i) => (
                <Star
                  key={`full-${i}`}
                  className="h-4 w-4 fill-yellow-400 text-yellow-400"
                />
              ))}
              {starRating.half && (
                <Star className="h-4 w-4 fill-yellow-400/50 text-yellow-400" />
              )}
              {Array.from({ length: starRating.empty }).map((_, i) => (
                <Star key={`empty-${i}`} className="h-4 w-4 text-muted" />
              ))}
            </div>
            <span className="text-xs text-muted-foreground">
              ({product.reviewCount ?? 0})
            </span>
          </div>
        )}

        {/* Price */}
        <div className="mt-auto flex items-baseline gap-2">
          <span className="text-lg font-bold">
            {formatCurrency(product.price)}
          </span>
          {hasDiscount && (
            <span className="text-sm text-muted-foreground line-through">
              {formatCurrency(product.originalPrice!)}
            </span>
          )}
        </div>

        {/* Affordability indicator */}
        {monthlyBudget && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div
                  className={cn(
                    "flex items-center gap-1 rounded-full px-2 py-1 text-xs",
                    affordability.isAffordable
                      ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                      : "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400"
                  )}
                >
                  <Info className="h-3 w-3" />
                  <span>{affordability.percentage.toFixed(0)}% of budget</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>{affordability.recommendation}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {/* Match explanation */}
        {showExplanation && product.matchExplanation && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge variant="outline" className="cursor-help text-xs">
                  <Info className="mr-1 h-3 w-3" />
                  Why this?
                </Badge>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>{product.matchExplanation}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </CardContent>

      <CardFooter className="flex gap-2 p-4 pt-0">
        {/* Add to cart */}
        <Button
          className="flex-1"
          disabled={!product.inStock}
          onClick={onAddToCart}
        >
          <ShoppingCart className="mr-2 h-4 w-4" />
          {product.inStock ? "Add to Cart" : "Out of Stock"}
        </Button>

        {/* Show alternatives */}
        {!affordability.isAffordable && onShowAlternatives && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={onShowAlternatives}
                  aria-label="Show cheaper alternatives"
                >
                  <TrendingDown className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Find cheaper alternatives</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </CardFooter>
    </Card>
  );
}
