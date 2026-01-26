/**
 * Utility functions for class name merging and styling
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge class names with Tailwind CSS conflict resolution
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format currency value
 */
export function formatCurrency(
  value: number,
  currency: string = "USD",
  locale: string = "en-US"
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
  }).format(value);
}

/**
 * Format date to readable string
 */
export function formatDate(
  date: string | Date,
  options?: Intl.DateTimeFormatOptions
): string {
  const dateObj = typeof date === "string" ? new Date(date) : date;
  return dateObj.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    ...options,
  });
}

/**
 * Calculate affordability score
 */
export function calculateAffordability(
  price: number,
  monthlyBudget?: number
): {
  isAffordable: boolean;
  percentage: number;
  recommendation: string;
} {
  if (!monthlyBudget) {
    return {
      isAffordable: true,
      percentage: 0,
      recommendation: "No budget set",
    };
  }

  const percentage = (price / monthlyBudget) * 100;

  if (percentage <= 20) {
    return {
      isAffordable: true,
      percentage,
      recommendation: "Within budget - good fit!",
    };
  } else if (percentage <= 40) {
    return {
      isAffordable: true,
      percentage,
      recommendation: "Affordable - consider your priorities",
    };
  } else if (percentage <= 60) {
    return {
      isAffordable: false,
      percentage,
      recommendation: "Slightly over budget - look for alternatives",
    };
  } else {
    return {
      isAffordable: false,
      percentage,
      recommendation: "Over budget - consider saving up",
    };
  }
}

/**
 * Debounce function for search input
 */
export function debounce<T extends (...args: Parameters<T>) => ReturnType<T>>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      func(...args);
    }, wait);
  };
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}

/**
 * Generate star rating display
 */
export function getStarRating(rating: number): {
  full: number;
  half: boolean;
  empty: number;
} {
  const full = Math.floor(rating);
  const half = rating % 1 >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);
  return { full, half, empty };
}

/**
 * Convert file to base64
 */
export async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result as string;
      // Remove the data URL prefix (e.g., "data:image/png;base64,")
      const base64 = result.split(",")[1];
      resolve(base64);
    };
    reader.onerror = (error) => reject(error);
  });
}

/**
 * Validate image file
 */
export function validateImageFile(file: File): {
  valid: boolean;
  error?: string;
} {
  const validTypes = ["image/jpeg", "image/png", "image/webp", "image/gif"];
  const maxSize = 10 * 1024 * 1024; // 10MB

  if (!validTypes.includes(file.type)) {
    return {
      valid: false,
      error: "Please upload a valid image (JPEG, PNG, WebP, or GIF)",
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: "Image size must be less than 10MB",
    };
  }

  return { valid: true };
}

/**
 * Validate audio file
 */
export function validateAudioFile(file: File): {
  valid: boolean;
  error?: string;
} {
  const validTypes = [
    "audio/wav",
    "audio/mp3",
    "audio/mpeg",
    "audio/webm",
    "audio/ogg",
  ];
  const maxSize = 25 * 1024 * 1024; // 25MB

  if (!validTypes.includes(file.type)) {
    return {
      valid: false,
      error: "Please upload a valid audio file (WAV, MP3, WebM, or OGG)",
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: "Audio file size must be less than 25MB",
    };
  }

  return { valid: true };
}

/**
 * Generate unique ID
 */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Sleep function for delays
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Parse query string to object
 */
export function parseQueryString(query: string): Record<string, string> {
  const params = new URLSearchParams(query);
  const result: Record<string, string> = {};
  params.forEach((value, key) => {
    result[key] = value;
  });
  return result;
}

/**
 * Build query string from object
 */
export function buildQueryString(params: Record<string, string | number | boolean | undefined>): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.append(key, String(value));
    }
  });
  return searchParams.toString();
}
