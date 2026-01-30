"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Check, Sparkles, Tag } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

const categories = [
  { id: "electronics", name: "Electronics", emoji: "📱", description: "Phones, laptops, gadgets" },
  { id: "fashion", name: "Fashion", emoji: "👕", description: "Clothing, shoes, accessories" },
  { id: "home", name: "Home & Garden", emoji: "🏠", description: "Furniture, decor, tools" },
  { id: "sports", name: "Sports & Outdoors", emoji: "⚽", description: "Fitness, camping, sports gear" },
  { id: "books", name: "Books", emoji: "📚", description: "Fiction, non-fiction, educational" },
  { id: "beauty", name: "Beauty & Health", emoji: "💄", description: "Skincare, makeup, wellness" },
  { id: "toys", name: "Toys & Games", emoji: "🎮", description: "Video games, board games, toys" },
  { id: "automotive", name: "Automotive", emoji: "🚗", description: "Car parts, accessories" },
  { id: "food", name: "Food & Grocery", emoji: "🍎", description: "Groceries, gourmet, snacks" },
  { id: "office", name: "Office Supplies", emoji: "📎", description: "Stationery, furniture, tech" },
  { id: "pets", name: "Pets", emoji: "🐾", description: "Food, toys, accessories" },
  { id: "music", name: "Music & Instruments", emoji: "🎸", description: "Instruments, audio equipment" },
];

const brands = [
  { id: "apple", name: "Apple" },
  { id: "samsung", name: "Samsung" },
  { id: "nike", name: "Nike" },
  { id: "adidas", name: "Adidas" },
  { id: "sony", name: "Sony" },
  { id: "lg", name: "LG" },
  { id: "dell", name: "Dell" },
  { id: "hp", name: "HP" },
  { id: "amazon", name: "Amazon Basics" },
  { id: "google", name: "Google" },
  { id: "microsoft", name: "Microsoft" },
  { id: "lenovo", name: "Lenovo" },
  { id: "bose", name: "Bose" },
  { id: "jbl", name: "JBL" },
  { id: "puma", name: "Puma" },
  { id: "reebok", name: "Reebok" },
];

export default function InterestsPage() {
  const router = useRouter();
  const [selectedCategories, setSelectedCategories] = React.useState<string[]>([]);
  const [selectedBrands, setSelectedBrands] = React.useState<string[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);

  // Check if user is logged in
  React.useEffect(() => {
    const isLoggedIn = localStorage.getItem("isLoggedIn");
    if (isLoggedIn !== "true") {
      router.push("/login");
    }
  }, [router]);

  const toggleCategory = (categoryId: string) => {
    setSelectedCategories((prev) =>
      prev.includes(categoryId)
        ? prev.filter((id) => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const toggleBrand = (brandId: string) => {
    setSelectedBrands((prev) =>
      prev.includes(brandId)
        ? prev.filter((id) => id !== brandId)
        : [...prev, brandId]
    );
  };

  const handleContinue = async () => {
    setIsLoading(true);

    // Save preferences to localStorage
    localStorage.setItem("userCategories", JSON.stringify(selectedCategories));
    localStorage.setItem("userBrands", JSON.stringify(selectedBrands));

    // Simulate saving delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    router.push("/onboarding/financial");
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary/5 via-background to-background px-4 py-8">
      <div className="mx-auto max-w-3xl">
        {/* Progress Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Step 1 of 2</span>
            <span className="text-sm text-muted-foreground">50%</span>
          </div>
          <Progress value={50} className="h-2" />
        </div>

        <Card>
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-primary to-primary/60">
              <Tag className="h-8 w-8 text-primary-foreground" />
            </div>
            <CardTitle className="text-2xl">What are you interested in?</CardTitle>
            <CardDescription>
              Select categories and brands you love. This helps us personalize your experience.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-8">
            {/* Categories Section */}
            <div>
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                Categories ({selectedCategories.length} selected)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {categories.map((category) => {
                  const isSelected = selectedCategories.includes(category.id);
                  return (
                    <button
                      key={category.id}
                      onClick={() => toggleCategory(category.id)}
                      className={`relative flex flex-col items-center p-4 rounded-lg border-2 transition-all hover:scale-105 ${
                        isSelected
                          ? "border-primary bg-primary/10"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      {isSelected && (
                        <div className="absolute -top-2 -right-2 h-6 w-6 rounded-full bg-primary flex items-center justify-center">
                          <Check className="h-4 w-4 text-primary-foreground" />
                        </div>
                      )}
                      <span className="text-3xl mb-2">{category.emoji}</span>
                      <span className="font-medium text-sm text-center">
                        {category.name}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Brands Section */}
            <div>
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Tag className="h-4 w-4" />
                Favorite Brands ({selectedBrands.length} selected)
              </h3>
              <div className="flex flex-wrap gap-2">
                {brands.map((brand) => {
                  const isSelected = selectedBrands.includes(brand.id);
                  return (
                    <button
                      key={brand.id}
                      onClick={() => toggleBrand(brand.id)}
                      className={`px-4 py-2 rounded-full border-2 transition-all ${
                        isSelected
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      {brand.name}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Continue Button */}
            <div className="pt-4 flex justify-end">
              <Button
                onClick={handleContinue}
                size="lg"
                disabled={isLoading || selectedCategories.length === 0}
              >
                {isLoading ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent mr-2" />
                    Saving...
                  </>
                ) : (
                  <>
                    Continue
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>

            {selectedCategories.length === 0 && (
              <p className="text-sm text-muted-foreground text-center">
                Please select at least one category to continue
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
