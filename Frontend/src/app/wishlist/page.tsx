"use client";

import * as React from "react";
import Link from "next/link";
import Image from "next/image";
import { Heart, Trash2, ShoppingCart, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useProduct } from "@/hooks/useApi";
import { formatCurrency } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

interface WishlistItemProps {
  productId: string;
  onRemove: (id: string) => void;
  onMoveToCart: (id: string) => void;
}

function WishlistItem({ productId, onRemove, onMoveToCart }: WishlistItemProps) {
  const { data, isLoading, isError } = useProduct(productId);
  const product = data?.product;

  // Auto-remove invalid products from wishlist
  React.useEffect(() => {
    if (!isLoading && (isError || !product)) {
      // Product doesn't exist, remove from wishlist
      onRemove(productId);
    }
  }, [isLoading, isError, product, productId, onRemove]);

  if (isLoading) {
    return (
      <Card className="border-border/60">
        <CardContent className="p-4">
          <div className="flex gap-4">
            <Skeleton className="h-32 w-32 rounded-xl" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-16" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!product) {
    return null;
  }

  return (
    <Card className="border-border/60 transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
      <CardContent className="p-5">
        <div className="flex gap-4">
          <div className="relative h-32 w-32 flex-shrink-0 overflow-hidden rounded-xl bg-muted">
            {product.imageUrl ? (
              <Image
                src={product.imageUrl}
                alt={product.name}
                fill
                className="object-cover transition-transform duration-300 group-hover:scale-105"
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <Heart className="h-8 w-8 text-muted-foreground" />
              </div>
            )}
          </div>
          <div className="flex flex-1 flex-col justify-between">
            <div>
              <div className="flex items-start justify-between">
                <div>
                  <Link
                    href={`/product/${product.id}`}
                    className="font-medium hover:text-primary transition-colors"
                  >
                    {product.name}
                  </Link>
                  <p className="text-sm text-muted-foreground">{product.brand}</p>
                </div>
                <p className="text-lg font-semibold">{formatCurrency(product.price)}</p>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <Badge variant={product.inStock ? "default" : "secondary"} className="rounded-full">
                  {product.inStock ? "In Stock" : "Out of Stock"}
                </Badge>
                {product.category && (
                  <Badge variant="outline" className="rounded-full">{product.category}</Badge>
                )}
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2">
              <Button
                size="sm"
                onClick={() => onMoveToCart(productId)}
                disabled={!product.inStock}
              >
                <ShoppingCart className="mr-2 h-4 w-4" />
                Move to Cart
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-destructive"
                onClick={() => onRemove(productId)}
              >
                <Trash2 className="mr-1 h-4 w-4" />
                Remove
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function WishlistPage() {
  const [wishlistItems, setWishlistItems] = React.useState<string[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    const wishlist = JSON.parse(localStorage.getItem("wishlist") || "[]");
    setWishlistItems(wishlist);
    setIsLoading(false);
  }, []);

  const handleRemove = (productId: string) => {
    const updated = wishlistItems.filter((id) => id !== productId);
    setWishlistItems(updated);
    localStorage.setItem("wishlist", JSON.stringify(updated));
    window.dispatchEvent(new Event("wishlistUpdated"));
  };

  const handleMoveToCart = (productId: string) => {
    // Add to cart
    const cart = JSON.parse(localStorage.getItem("cart") || "[]");
    if (!cart.includes(productId)) {
      cart.push(productId);
      localStorage.setItem("cart", JSON.stringify(cart));
      window.dispatchEvent(new Event("cartUpdated"));
    }
    
    // Remove from wishlist
    handleRemove(productId);
  };

  const clearWishlist = () => {
    setWishlistItems([]);
    localStorage.setItem("wishlist", JSON.stringify([]));
    window.dispatchEvent(new Event("wishlistUpdated"));
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-10 w-48 mb-6" />
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 lg:px-6">
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/search">
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Continue Shopping
            </Button>
          </Link>
          <h1 className="text-2xl font-semibold tracking-tight">My Wishlist</h1>
          {wishlistItems.length > 0 && (
            <Badge variant="secondary" className="rounded-full">{wishlistItems.length} items</Badge>
          )}
        </div>
        {wishlistItems.length > 0 && (
          <Button variant="outline" size="sm" onClick={clearWishlist}>
            Clear Wishlist
          </Button>
        )}
      </div>

      {wishlistItems.length === 0 ? (
        <Card className="border-border/60 shadow-xl shadow-black/5">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="h-20 w-20 rounded-full bg-rose-500/10 flex items-center justify-center mb-6">
              <Heart className="h-10 w-10 text-rose-500" />
            </div>
            <h2 className="text-xl font-semibold tracking-tight mb-2">Your wishlist is empty</h2>
            <p className="text-muted-foreground mb-6">
              Save items you love by clicking the heart icon on products.
            </p>
            <Link href="/search">
              <Button>Discover Products</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {wishlistItems.map((productId) => (
            <WishlistItem
              key={productId}
              productId={productId}
              onRemove={handleRemove}
              onMoveToCart={handleMoveToCart}
            />
          ))}
        </div>
      )}
    </div>
  );
}
