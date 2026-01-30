"use client";

import * as React from "react";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { ChatInterface } from "@/components/product/ChatInterface";

interface MainLayoutProps {
  children: React.ReactNode;
  showChat?: boolean;
  userId?: string;
}

export function MainLayout({
  children,
  showChat = true,
  userId = "013c3cb2-482a-55b0-9559-6688c3b78313",
}: MainLayoutProps) {
  const [isDarkMode, setIsDarkMode] = React.useState(false);
  const [cartCount, setCartCount] = React.useState(0);
  const [wishlistCount, setWishlistCount] = React.useState(0);
  const [isMounted, setIsMounted] = React.useState(false);

  // Function to update counts from localStorage
  const updateCounts = React.useCallback(() => {
    if (typeof window === 'undefined') return;
    try {
      const cartData = localStorage.getItem("cart");
      const wishlistData = localStorage.getItem("wishlist");
      const cart = cartData ? JSON.parse(cartData) : [];
      const wishlist = wishlistData ? JSON.parse(wishlistData) : [];
      // Ensure we count unique items only
      const uniqueCart = [...new Set(cart)];
      const uniqueWishlist = [...new Set(wishlist)];
      setCartCount(uniqueCart.length);
      setWishlistCount(uniqueWishlist.length);
    } catch (e) {
      console.error('Error reading cart/wishlist from localStorage:', e);
      setCartCount(0);
      setWishlistCount(0);
    }
  }, []);

  // Set mounted state on client
  React.useEffect(() => {
    setIsMounted(true);
  }, []);

  // Initialize dark mode from localStorage or system preference
  React.useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    
    if (savedTheme === "dark" || (!savedTheme && systemPrefersDark)) {
      setIsDarkMode(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleTheme = () => {
    setIsDarkMode((prev) => {
      const newValue = !prev;
      if (newValue) {
        document.documentElement.classList.add("dark");
        localStorage.setItem("theme", "dark");
      } else {
        document.documentElement.classList.remove("dark");
        localStorage.setItem("theme", "light");
      }
      return newValue;
    });
  };

  // Initialize and listen for cart/wishlist updates
  React.useEffect(() => {
    // Initial load
    updateCounts();

    // Listen for storage events (cross-tab)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "cart" || e.key === "wishlist") {
        updateCounts();
      }
    };

    // Listen for custom events (same-tab)
    const handleCartUpdate = () => updateCounts();

    window.addEventListener("storage", handleStorageChange);
    window.addEventListener("cartUpdated", handleCartUpdate);
    window.addEventListener("wishlistUpdated", handleCartUpdate);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
      window.removeEventListener("cartUpdated", handleCartUpdate);
      window.removeEventListener("wishlistUpdated", handleCartUpdate);
    };
  }, [updateCounts]);

  return (
    <div className="flex min-h-screen flex-col">
      <Header
        cartItemCount={isMounted ? cartCount : 0}
        wishlistCount={isMounted ? wishlistCount : 0}
        isLoggedIn={!!userId}
        onToggleTheme={toggleTheme}
        isDarkMode={isDarkMode}
      />
      <main className="flex-1">{children}</main>
      <Footer />
      
      {/* Floating chat */}
      {showChat && userId && (
        <ChatInterface
          userId={userId}
          variant="floating"
          monthlyBudget={1000} // Default budget, would come from user profile
        />
      )}
    </div>
  );
}
