"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { X, Clock, ChevronLeft, ChevronRight, Trash2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn, formatCurrency } from "@/lib/utils";
import { useRecentlyViewed, RecentlyViewedItem } from "@/hooks/useRecentlyViewed";

interface RecentlyViewedProps {
  className?: string;
  maxDisplay?: number;
  showClearButton?: boolean;
}

export function RecentlyViewed({
  className,
  maxDisplay = 6,
  showClearButton = true,
}: RecentlyViewedProps) {
  const { items, removeItem, clearAll, isLoaded } = useRecentlyViewed();
  const scrollRef = React.useRef<HTMLDivElement>(null);

  // Don't render if not loaded or no items
  if (!isLoaded || items.length === 0) {
    return null;
  }

  const displayItems = items.slice(0, maxDisplay);

  const scrollLeft = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: -200, behavior: "smooth" });
    }
  };

  const scrollRight = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: 200, behavior: "smooth" });
    }
  };

  return (
    <div className={cn("space-y-3", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-muted-foreground" />
          <h3 className="font-semibold">Recently Viewed</h3>
          <span className="text-sm text-muted-foreground">
            ({items.length})
          </span>
        </div>
        {showClearButton && items.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAll}
            className="text-muted-foreground hover:text-destructive"
          >
            <Trash2 className="mr-1 h-4 w-4" />
            Clear
          </Button>
        )}
      </div>

      {/* Scrollable Products */}
      <div className="relative group">
        {/* Left scroll button */}
        <Button
          variant="outline"
          size="icon"
          className="absolute -left-3 top-1/2 z-10 hidden h-8 w-8 -translate-y-1/2 rounded-full opacity-0 shadow-md transition-opacity group-hover:opacity-100 md:flex"
          onClick={scrollLeft}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        {/* Products scroll area */}
        <ScrollArea className="w-full" ref={scrollRef}>
          <div className="flex gap-4 pb-4">
            {displayItems.map((item) => (
              <RecentlyViewedCard
                key={item.id}
                item={item}
                onRemove={() => removeItem(item.id)}
              />
            ))}
          </div>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>

        {/* Right scroll button */}
        <Button
          variant="outline"
          size="icon"
          className="absolute -right-3 top-1/2 z-10 hidden h-8 w-8 -translate-y-1/2 rounded-full opacity-0 shadow-md transition-opacity group-hover:opacity-100 md:flex"
          onClick={scrollRight}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Show more link */}
      {items.length > maxDisplay && (
        <div className="text-center">
          <Link
            href="/profile?tab=history"
            className="text-sm text-primary hover:underline"
          >
            View all {items.length} recently viewed items →
          </Link>
        </div>
      )}
    </div>
  );
}

interface RecentlyViewedCardProps {
  item: RecentlyViewedItem;
  onRemove: () => void;
}

function RecentlyViewedCard({ item, onRemove }: RecentlyViewedCardProps) {
  return (
    <Card className="group/card relative w-40 flex-shrink-0 overflow-hidden transition-shadow hover:shadow-md">
      {/* Remove button */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute right-1 top-1 z-10 h-6 w-6 rounded-full bg-background/80 opacity-0 transition-opacity group-hover/card:opacity-100"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onRemove();
        }}
      >
        <X className="h-3 w-3" />
      </Button>

      <Link href={`/product/${item.id}`}>
        {/* Image */}
        <div className="relative aspect-square bg-muted">
          {item.imageUrl ? (
            <Image
              src={item.imageUrl}
              alt={item.name}
              fill
              className="object-cover"
              sizes="160px"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              No image
            </div>
          )}
        </div>

        <CardContent className="p-2">
          {/* Name */}
          <p className="line-clamp-2 text-xs font-medium leading-tight">
            {item.name}
          </p>
          
          {/* Price */}
          <p className="mt-1 font-semibold text-sm">
            {formatCurrency(item.price)}
          </p>

          {/* Category */}
          <p className="text-xs text-muted-foreground truncate">
            {item.category}
          </p>
        </CardContent>
      </Link>
    </Card>
  );
}
