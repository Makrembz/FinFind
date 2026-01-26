"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Search, Mic, Camera, X, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn, debounce } from "@/lib/utils";
import { useSearchSuggestions } from "@/hooks/useApi";

interface SearchBarProps {
  initialQuery?: string;
  placeholder?: string;
  onSearch?: (query: string) => void;
  onVoiceClick?: () => void;
  onImageClick?: () => void;
  showVoiceButton?: boolean;
  showImageButton?: boolean;
  autoFocus?: boolean;
  className?: string;
}

export function SearchBar({
  initialQuery = "",
  placeholder = "Search for products...",
  onSearch,
  onVoiceClick,
  onImageClick,
  showVoiceButton = true,
  showImageButton = true,
  autoFocus = false,
  className,
}: SearchBarProps) {
  const router = useRouter();
  const [query, setQuery] = React.useState(initialQuery);
  const [showSuggestions, setShowSuggestions] = React.useState(false);
  const [selectedIndex, setSelectedIndex] = React.useState(-1);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const suggestionsRef = React.useRef<HTMLDivElement>(null);

  // Debounced query for suggestions
  const [debouncedQuery, setDebouncedQuery] = React.useState("");
  
  const debouncedSetQuery = React.useMemo(
    () =>
      debounce((q: string) => {
        setDebouncedQuery(q);
      }, 300),
    []
  );

  const { data: suggestionsData, isLoading: suggestionsLoading } =
    useSearchSuggestions(debouncedQuery);

  const suggestions = suggestionsData?.suggestions || [];

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    debouncedSetQuery(value);
    setShowSuggestions(true);
    setSelectedIndex(-1);
  };

  // Handle form submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setShowSuggestions(false);
      if (onSearch) {
        onSearch(query.trim());
      } else {
        router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      }
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    if (onSearch) {
      onSearch(suggestion);
    } else {
      router.push(`/search?q=${encodeURIComponent(suggestion)}`);
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case "Enter":
        if (selectedIndex >= 0) {
          e.preventDefault();
          handleSuggestionClick(suggestions[selectedIndex]);
        }
        break;
      case "Escape":
        setShowSuggestions(false);
        break;
    }
  };

  // Close suggestions on click outside
  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Clear input
  const handleClear = () => {
    setQuery("");
    setDebouncedQuery("");
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  return (
    <div className={cn("relative w-full", className)}>
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          {/* Search icon */}
          <Search className="absolute left-3 h-5 w-5 text-muted-foreground" />

          {/* Input */}
          <Input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => query.length >= 2 && setShowSuggestions(true)}
            placeholder={placeholder}
            autoFocus={autoFocus}
            className="pl-10 pr-24 h-12 text-base"
            aria-label="Search products"
            aria-autocomplete="list"
            aria-controls="search-suggestions"
            aria-expanded={showSuggestions}
          />

          {/* Action buttons */}
          <div className="absolute right-2 flex items-center gap-1">
            {query && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={handleClear}
                aria-label="Clear search"
              >
                <X className="h-4 w-4" />
              </Button>
            )}

            {showVoiceButton && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-primary hover:text-primary"
                onClick={onVoiceClick}
                aria-label="Voice search"
              >
                <Mic className="h-4 w-4" />
              </Button>
            )}

            {showImageButton && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-primary hover:text-primary"
                onClick={onImageClick}
                aria-label="Image search"
              >
                <Camera className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </form>

      {/* Suggestions dropdown */}
      {showSuggestions && (query.length >= 2 || suggestions.length > 0) && (
        <div
          ref={suggestionsRef}
          id="search-suggestions"
          className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-lg"
          role="listbox"
        >
          {suggestionsLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : suggestions.length > 0 ? (
            <ul className="py-1">
              {suggestions.map((suggestion, index) => (
                <li
                  key={suggestion}
                  role="option"
                  aria-selected={selectedIndex === index}
                  className={cn(
                    "flex cursor-pointer items-center gap-2 px-4 py-2 text-sm transition-colors",
                    selectedIndex === index
                      ? "bg-accent text-accent-foreground"
                      : "hover:bg-accent hover:text-accent-foreground"
                  )}
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  <Search className="h-4 w-4 text-muted-foreground" />
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          ) : debouncedQuery.length >= 2 ? (
            <div className="px-4 py-3 text-sm text-muted-foreground">
              No suggestions found
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
