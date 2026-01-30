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
      {/* Hero Section - Premium Design */}
      <section className="relative overflow-hidden bg-gradient-to-b from-background via-background to-muted/30 py-24 lg:py-36">
        {/* Subtle background elements */}
        <div className="absolute inset-0 -z-10 overflow-hidden">
          <div className="absolute -left-1/4 top-0 h-[500px] w-[500px] rounded-full bg-primary/5 blur-[120px]" />
          <div className="absolute -right-1/4 bottom-0 h-[400px] w-[400px] rounded-full bg-blue-500/5 blur-[100px]" />
        </div>

        <div className="container mx-auto px-4 lg:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
              <Sparkles className="h-3.5 w-3.5" />
              AI-Powered Shopping
            </div>

            <h1 className="mb-6 text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              Find products that fit{" "}
              <span className="bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent">
                your budget
              </span>
            </h1>

            <p className="mx-auto mb-10 max-w-2xl text-lg text-muted-foreground sm:text-xl">
              Discover products with AI-powered search. Use text, voice, or image to
              find exactly what you need.
            </p>

            <div className="mx-auto max-w-2xl">
              <SearchBar
                onSearch={handleSearch}
                onVoiceClick={() => setShowVoiceRecorder(true)}
                onImageClick={() => setShowImageUploader(true)}
                placeholder="Search for products, categories, or describe what you're looking for..."
                className="shadow-xl shadow-black/5"
              />
            </div>

            <div className="mt-8">
              <p className="mb-4 text-sm font-medium text-muted-foreground">Popular searches</p>
              <div className="flex flex-wrap justify-center gap-2">
                {trendingSearches.map((search) => (
                  <button
                    key={search}
                    onClick={() => handleSearch(search)}
                    className="rounded-full border border-border/60 bg-background px-4 py-2 text-sm font-medium text-muted-foreground transition-all duration-200 hover:border-primary/30 hover:bg-primary/5 hover:text-foreground"
                  >
                    {search}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Categories Section - Clean Grid */}
      <section className="py-20 lg:py-24">
        <div className="container mx-auto px-4 lg:px-6">
          <div className="mb-12 text-center">
            <h2 className="mb-3 text-2xl font-semibold tracking-tight sm:text-3xl">Browse Categories</h2>
            <p className="text-muted-foreground">
              Explore products across popular categories
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6 lg:gap-6">
            {categories.map((category) => (
              <Card
                key={category.name}
                className="group cursor-pointer border-border/60 bg-background transition-all duration-300 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 card-hover"
                onClick={() => handleSearch(category.name)}
              >
                <CardContent className="flex flex-col items-center p-6 text-center">
                  <span className="mb-3 text-4xl transition-transform duration-300 group-hover:scale-110">{category.emoji}</span>
                  <h3 className="font-medium text-foreground">{category.name}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{category.count} products</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section - Minimalist */}
      <section className="border-t border-border/40 bg-muted/20 py-20 lg:py-24">
        <div className="container mx-auto px-4 lg:px-6">
          <div className="mb-16 text-center">
            <h2 className="mb-3 text-2xl font-semibold tracking-tight sm:text-3xl">Why FinFind?</h2>
            <p className="text-muted-foreground">
              The smartest way to discover and shop for products
            </p>
          </div>

          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, index) => (
              <div 
                key={feature.title} 
                className="group flex flex-col items-center text-center"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-2xl transition-all duration-300 group-hover:bg-primary/15 group-hover:scale-105">
                  {feature.icon}
                </div>
                <h3 className="mb-2 font-semibold text-foreground">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section - Clean and Bold */}
      <section className="border-t border-border/40 py-20 lg:py-24">
        <div className="container mx-auto px-4 lg:px-6">
          <div className="grid gap-12 text-center sm:grid-cols-3">
            <div className="group">
              <div className="mb-2 text-4xl font-bold tracking-tight text-foreground lg:text-5xl">100K+</div>
              <div className="text-sm font-medium text-muted-foreground">Products indexed</div>
            </div>
            <div className="group">
              <div className="mb-2 text-4xl font-bold tracking-tight text-foreground lg:text-5xl">50K+</div>
              <div className="text-sm font-medium text-muted-foreground">Happy customers</div>
            </div>
            <div className="group">
              <div className="mb-2 text-4xl font-bold tracking-tight text-foreground lg:text-5xl">99%</div>
              <div className="text-sm font-medium text-muted-foreground">Search accuracy</div>
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
