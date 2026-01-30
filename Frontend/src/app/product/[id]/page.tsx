"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import {
  Star,
  Heart,
  ShoppingCart,
  Share2,
  ChevronLeft,
  ChevronRight,
  Check,
  Truck,
  RefreshCcw,
  Shield,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ExplanationTooltip } from "@/components/product/ExplanationTooltip";
import { AffordabilityIndicator } from "@/components/product/AffordabilityIndicator";
import { AlternativeSuggestion } from "@/components/product/AlternativeSuggestion";
import { ProductCard } from "@/components/product/ProductCard";
import { useProduct, useProductReviews, useRelatedProducts, useLogProductInteraction } from "@/hooks/useApi";
import { useRecentlyViewed } from "@/hooks/useRecentlyViewed";
import { cn, formatCurrency, getStarRating } from "@/lib/utils";
import type { Review, ProductSearchResult } from "@/types";

// Default user ID for demo purposes
const DEFAULT_USER_ID = "013c3cb2-482a-55b0-9559-6688c3b78313";

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params.id as string;

  const [selectedImage, setSelectedImage] = React.useState(0);
  const [quantity, setQuantity] = React.useState(1);

  // Demo user budget (in production, this would come from user profile)
  const monthlyBudget = 1000;
  
  // Track recently viewed products
  const { addItem: addToRecentlyViewed } = useRecentlyViewed();
  
  // Track interactions for learning
  const logInteraction = useLogProductInteraction();

  const { data: productData, isLoading, error } = useProduct(productId);
  const { data: reviewsData } = useProductReviews(productId);
  const { data: relatedProducts } = useRelatedProducts(productId);

  const product = productData?.product;
  const reviews = reviewsData?.reviews || [];
  const alternatives = (relatedProducts || []).filter(
    (p: ProductSearchResult) => product && p.price < product.price
  );

  // Log view interaction when product loads
  React.useEffect(() => {
    if (product) {
      // Track view interaction for learning
      logInteraction.mutate({
        productId: product.id,
        interactionType: "view",
        metadata: { 
          user_id: DEFAULT_USER_ID,
          source: "product_detail",
          category: product.category,
          brand: product.brand,
          price: product.price
        }
      });
      
      addToRecentlyViewed({
        id: product.id,
        name: product.name,
        price: product.price,
        imageUrl: product.imageUrl,
        category: product.category,
        brand: product.brand,
        viewedAt: Date.now(),
      });
    }
  }, [product?.id]); // Only trigger on product ID change

  const handleAddToCart = () => {
    const cart = JSON.parse(localStorage.getItem("cart") || "[]");
    for (let i = 0; i < quantity; i++) {
      if (!cart.includes(productId)) {
        cart.push(productId);
      }
    }
    localStorage.setItem("cart", JSON.stringify(cart));
    window.dispatchEvent(new Event("cartUpdated"));
    
    // Log add_to_cart interaction
    logInteraction.mutate({
      productId,
      interactionType: "add_to_cart",
      metadata: { user_id: DEFAULT_USER_ID, quantity }
    });
    
    // Show toast or notification in production
    alert(`Added ${quantity} item(s) to cart`);
  };

  const handleAddToWishlist = () => {
    const wishlist = JSON.parse(localStorage.getItem("wishlist") || "[]");
    if (!wishlist.includes(productId)) {
      wishlist.push(productId);
      localStorage.setItem("wishlist", JSON.stringify(wishlist));
      window.dispatchEvent(new Event("wishlistUpdated"));
      
      // Log wishlist interaction
      logInteraction.mutate({
        productId,
        interactionType: "wishlist",
        metadata: { user_id: DEFAULT_USER_ID }
      });
      
      alert("Added to wishlist");
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      await navigator.share({
        title: product?.name,
        text: product?.description,
        url: window.location.href,
      });
    } else {
      await navigator.clipboard.writeText(window.location.href);
      alert("Link copied to clipboard!");
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="grid gap-8 lg:grid-cols-2">
          <div className="space-y-4">
            <Skeleton className="aspect-square w-full rounded-lg" />
            <div className="flex gap-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-20 rounded-lg" />
              ))}
            </div>
          </div>
          <div className="space-y-6">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-6 w-1/2" />
            <Skeleton className="h-10 w-1/4" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="container mx-auto flex flex-col items-center justify-center px-4 py-16">
        <h1 className="mb-4 text-2xl font-bold">Product not found</h1>
        <p className="mb-8 text-muted-foreground">
          The product you're looking for doesn't exist or has been removed.
        </p>
        <Button onClick={() => router.push("/")}>Back to Home</Button>
      </div>
    );
  }

  const starRating = getStarRating(product.rating ?? 0);
  const hasDiscount =
    product.originalPrice && product.originalPrice > product.price;
  const discountPercent = hasDiscount
    ? Math.round((1 - product.price / product.originalPrice!) * 100)
    : 0;

  // Mock multiple images (in production, these would come from the API)
  const images = product.imageUrl
    ? [product.imageUrl, product.imageUrl, product.imageUrl, product.imageUrl]
    : [];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/" className="hover:text-foreground">
          Home
        </Link>
        <span>/</span>
        <Link href="/search" className="hover:text-foreground">
          Search
        </Link>
        <span>/</span>
        <Link
          href={`/search?q=${encodeURIComponent(product.category)}`}
          className="hover:text-foreground"
        >
          {product.category}
        </Link>
        <span>/</span>
        <span className="text-foreground">{product.name}</span>
      </nav>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Image Gallery */}
        <div className="space-y-4">
          <div className="relative aspect-square overflow-hidden rounded-lg bg-muted">
            {images.length > 0 ? (
              <>
                <Image
                  src={images[selectedImage]}
                  alt={product.name}
                  fill
                  className="object-cover"
                  priority
                />
                {images.length > 1 && (
                  <>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white"
                      onClick={() =>
                        setSelectedImage((prev) =>
                          prev === 0 ? images.length - 1 : prev - 1
                        )
                      }
                      aria-label="Previous image"
                    >
                      <ChevronLeft className="h-5 w-5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white"
                      onClick={() =>
                        setSelectedImage((prev) =>
                          prev === images.length - 1 ? 0 : prev + 1
                        )
                      }
                      aria-label="Next image"
                    >
                      <ChevronRight className="h-5 w-5" />
                    </Button>
                  </>
                )}
              </>
            ) : (
              <div className="flex h-full items-center justify-center">
                <ShoppingCart className="h-24 w-24 text-muted-foreground" />
              </div>
            )}

            {/* Badges */}
            <div className="absolute left-4 top-4 flex flex-col gap-2">
              {hasDiscount && (
                <Badge variant="destructive">-{discountPercent}%</Badge>
              )}
              {!product.inStock && <Badge variant="secondary">Out of Stock</Badge>}
            </div>
          </div>

          {/* Thumbnails */}
          {images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto">
              {images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(idx)}
                  className={cn(
                    "relative h-20 w-20 flex-shrink-0 overflow-hidden rounded-lg border-2",
                    selectedImage === idx
                      ? "border-primary"
                      : "border-transparent opacity-70"
                  )}
                >
                  <Image
                    src={img}
                    alt={`${product.name} ${idx + 1}`}
                    fill
                    className="object-cover"
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="space-y-6">
          {/* Title & Brand */}
          <div>
            <div className="mb-2 flex items-center gap-2">
              {product.brand && (
                <Badge variant="outline">{product.brand}</Badge>
              )}
              <Badge variant="secondary">{product.category}</Badge>
            </div>
            <h1 className="text-2xl font-bold sm:text-3xl">{product.name}</h1>
          </div>

          {/* Rating */}
          {product.rating !== undefined && (
            <div className="flex items-center gap-3">
              <div className="flex">
                {Array.from({ length: starRating.full }).map((_, i) => (
                  <Star
                    key={`full-${i}`}
                    className="h-5 w-5 fill-yellow-400 text-yellow-400"
                  />
                ))}
                {starRating.half && (
                  <Star className="h-5 w-5 fill-yellow-400/50 text-yellow-400" />
                )}
                {Array.from({ length: starRating.empty }).map((_, i) => (
                  <Star key={`empty-${i}`} className="h-5 w-5 text-muted" />
                ))}
              </div>
              <span className="text-sm">
                {product.rating.toFixed(1)} ({product.reviewCount ?? 0} reviews)
              </span>
            </div>
          )}

          {/* Price */}
          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-bold">
              {formatCurrency(product.price)}
            </span>
            {hasDiscount && (
              <span className="text-xl text-muted-foreground line-through">
                {formatCurrency(product.originalPrice!)}
              </span>
            )}
          </div>

          {/* Affordability */}
          <AffordabilityIndicator
            price={product.price}
            monthlyBudget={monthlyBudget}
            variant="detailed"
          />

          {/* Stock Status */}
          <div className="flex items-center gap-2">
            {product.inStock ? (
              <>
                <Check className="h-5 w-5 text-green-500" />
                <span className="text-green-600 dark:text-green-400">In Stock</span>
              </>
            ) : (
              <span className="text-red-600 dark:text-red-400">Out of Stock</span>
            )}
          </div>

          {/* Quantity & Actions */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center rounded-lg border">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                disabled={quantity <= 1}
              >
                -
              </Button>
              <span className="w-12 text-center">{quantity}</span>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setQuantity((q) => q + 1)}
              >
                +
              </Button>
            </div>

            <Button
              size="lg"
              className="flex-1"
              disabled={!product.inStock}
              onClick={handleAddToCart}
            >
              <ShoppingCart className="mr-2 h-5 w-5" />
              Add to Cart
            </Button>

            <Button variant="outline" size="icon" onClick={handleAddToWishlist}>
              <Heart className="h-5 w-5" />
            </Button>

            <Button variant="outline" size="icon" onClick={handleShare}>
              <Share2 className="h-5 w-5" />
            </Button>
          </div>

          {/* Features */}
          <div className="grid gap-4 rounded-lg border p-4 sm:grid-cols-3">
            <div className="flex items-center gap-3">
              <Truck className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Free Shipping</p>
                <p className="text-xs text-muted-foreground">On orders over $50</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <RefreshCcw className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Easy Returns</p>
                <p className="text-xs text-muted-foreground">30-day return policy</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Shield className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Secure Payment</p>
                <p className="text-xs text-muted-foreground">SSL encryption</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs Section */}
      <Tabs defaultValue="description" className="mt-12">
        <TabsList className="w-full justify-start">
          <TabsTrigger value="description">Description</TabsTrigger>
          <TabsTrigger value="specifications">Specifications</TabsTrigger>
          <TabsTrigger value="reviews">
            Reviews ({product.reviewCount ?? 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="description" className="mt-6">
          <Card>
            <CardContent className="prose prose-sm max-w-none p-6 dark:prose-invert">
              <p>{product.description || "No description available."}</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="specifications" className="mt-6">
          <Card>
            <CardContent className="p-6">
              <dl className="grid gap-4 sm:grid-cols-2">
                <div className="flex justify-between border-b pb-2">
                  <dt className="text-muted-foreground">Category</dt>
                  <dd className="font-medium">{product.category}</dd>
                </div>
                {product.brand && (
                  <div className="flex justify-between border-b pb-2">
                    <dt className="text-muted-foreground">Brand</dt>
                    <dd className="font-medium">{product.brand}</dd>
                  </div>
                )}
                <div className="flex justify-between border-b pb-2">
                  <dt className="text-muted-foreground">SKU</dt>
                  <dd className="font-medium">{product.id}</dd>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <dt className="text-muted-foreground">Availability</dt>
                  <dd className="font-medium">
                    {product.inStock ? "In Stock" : "Out of Stock"}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reviews" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Customer Reviews</CardTitle>
            </CardHeader>
            <CardContent>
              {reviews.length > 0 ? (
                <div className="space-y-6">
                  {reviews.map((review: Review) => (
                    <div key={review.id} className="border-b pb-6 last:border-0">
                      <div className="mb-2 flex items-center gap-3">
                        <Avatar>
                          <AvatarFallback>
                            {review.userName?.charAt(0) || "U"}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{review.userName}</p>
                          <div className="flex items-center gap-2">
                            <div className="flex">
                              {Array.from({ length: 5 }).map((_, i) => (
                                <Star
                                  key={i}
                                  className={cn(
                                    "h-4 w-4",
                                    i < review.rating
                                      ? "fill-yellow-400 text-yellow-400"
                                      : "text-muted"
                                  )}
                                />
                              ))}
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {new Date(review.createdAt || review.date || Date.now()).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {review.comment}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">
                  No reviews yet. Be the first to review this product!
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Alternatives Section */}
      {alternatives.length > 0 && (
        <div className="mt-12">
          <AlternativeSuggestion
            originalPrice={product.price}
            alternatives={alternatives}
            title="More affordable alternatives"
          />
        </div>
      )}

      {/* Related Products */}
      {relatedProducts && relatedProducts.length > 0 && (
        <div className="mt-12">
          <h2 className="mb-6 text-2xl font-bold">You might also like</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {relatedProducts.slice(0, 4).map((relatedProduct: ProductSearchResult) => (
              <ProductCard
                key={relatedProduct.id}
                product={{
                  ...relatedProduct,
                  matchScore: undefined,
                  matchExplanation: undefined,
                }}
                monthlyBudget={monthlyBudget}
                showExplanation={false}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
