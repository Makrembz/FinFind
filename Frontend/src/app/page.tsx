"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Sparkles } from "lucide-react";
import { SearchBar } from "@/components/search/SearchBar";
import { VoiceRecorder } from "@/components/search/VoiceRecorder";
import { ImageUploader } from "@/components/search/ImageUploader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const features = [
  {
    icon: "✨",
    title: "AI-Powered Search",
    description: "Natural language queries powered by advanced AI understanding",
  },
  {
    icon: "📈",
    title: "Personalized Recommendations",
    description: "Get product suggestions tailored to your preferences and budget",
  },
  {
    icon: "⚡",
    title: "Multimodal Search",
    description: "Search by text, voice, or image - whatever works best for you",
  },
  {
    icon: "🛡️",
    title: "Budget-Aware",
    description: "Smart affordability analysis to help you stay within budget",
  },
];

const trendingSearches = [
  "wireless earbuds under $100",
  "gaming laptop 2024",
  "smart home devices",
  "fitness tracker waterproof",
  "mechanical keyboard",
  "portable charger",
];

const categories = [
  { name: "Electronics", emoji: "📱", count: "10K+" },
  { name: "Fashion", emoji: "👕", count: "25K+" },
  { name: "Home & Garden", emoji: "🏠", count: "15K+" },
  { name: "Sports", emoji: "⚽", count: "8K+" },
  { name: "Books", emoji: "📚", count: "50K+" },
  { name: "Beauty", emoji: "💄", count: "12K+" },
];

export default function HomePage() {
  const router = useRouter();
  const [showVoiceRecorder, setShowVoiceRecorder] = React.useState(false);
  const [showImageUploader, setShowImageUploader] = React.useState(false);

  const handleSearch = (query: string) => {
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  const handleVoiceResult = (transcript: string) => {
    setShowVoiceRecorder(false);
    if (transcript.trim()) {
      router.push(`/search?q=${encodeURIComponent(transcript.trim())}&source=voice`);
    }
  };

  const handleImageResult = (imageData: string) => {
    setShowImageUploader(false);
    sessionStorage.setItem("searchImage", imageData);
    router.push(`/search?source=image`);
  };

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-primary/5 via-background to-background py-20 lg:py-32">
        <div className="absolute inset-0 -z-10">
          <div className="absolute left-1/4 top-1/4 h-64 w-64 rounded-full bg-primary/10 blur-3xl" />
          <div className="absolute right-1/4 top-1/2 h-64 w-64 rounded-full bg-blue-500/10 blur-3xl" />
        </div>

        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-3xl text-center">
            <Badge variant="secondary" className="mb-4">
              <Sparkles className="mr-1 h-3 w-3" />
              AI-Powered Shopping
            </Badge>

            <h1 className="mb-4 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
              Find products that fit{" "}
              <span className="text-primary">your budget</span>
            </h1>

            <p className="mb-8 text-lg text-muted-foreground sm:text-xl">
              Discover products with AI-powered search. Use text, voice, or image to
              find exactly what you need, with personalized recommendations and
              affordability insights.
            </p>

            <div className="mx-auto max-w-2xl">
              <SearchBar
                onSearch={handleSearch}
                onVoiceClick={() => setShowVoiceRecorder(true)}
                onImageClick={() => setShowImageUploader(true)}
                placeholder="Search for products, categories, or describe what you're looking for..."
                className="shadow-lg"
              />
            </div>

            <div className="mt-6">
              <p className="mb-3 text-sm text-muted-foreground">Trending searches:</p>
              <div className="flex flex-wrap justify-center gap-2">
                {trendingSearches.map((search) => (
                  <button
                    key={search}
                    onClick={() => handleSearch(search)}
                    className="rounded-full border bg-background px-3 py-1 text-sm transition-colors hover:bg-muted"
                  >
                    {search}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="mb-8 text-center">
            <h2 className="mb-2 text-2xl font-bold sm:text-3xl">Browse Categories</h2>
            <p className="text-muted-foreground">
              Explore products across popular categories
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            {categories.map((category) => (
              <Card
                key={category.name}
                className="cursor-pointer transition-shadow hover:shadow-md"
                onClick={() => handleSearch(category.name)}
              >
                <CardContent className="flex flex-col items-center p-6 text-center">
                  <span className="mb-2 text-4xl">{category.emoji}</span>
                  <h3 className="font-medium">{category.name}</h3>
                  <p className="text-sm text-muted-foreground">{category.count} products</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="border-t bg-muted/30 py-16">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="mb-2 text-2xl font-bold sm:text-3xl">Why FinFind?</h2>
            <p className="text-muted-foreground">
              The smartest way to discover and shop for products
            </p>
          </div>

          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => (
              <Card key={feature.title} className="border-none bg-transparent shadow-none">
                <CardContent className="flex flex-col items-center p-6 text-center">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-2xl">
                    {feature.icon}
                  </div>
                  <h3 className="mb-2 font-semibold">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="border-t py-16">
        <div className="container mx-auto px-4">
          <div className="grid gap-8 text-center sm:grid-cols-3">
            <div>
              <div className="mb-2 text-4xl font-bold text-primary">100K+</div>
              <div className="text-muted-foreground">Products indexed</div>
            </div>
            <div>
              <div className="mb-2 text-4xl font-bold text-primary">50K+</div>
              <div className="text-muted-foreground">Happy customers</div>
            </div>
            <div>
              <div className="mb-2 text-4xl font-bold text-primary">99%</div>
              <div className="text-muted-foreground">Search accuracy</div>
            </div>
          </div>
        </div>
      </section>

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
