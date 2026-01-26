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
  userId = "demo-user",
}: MainLayoutProps) {
  const [isDarkMode, setIsDarkMode] = React.useState(false);
  const [cartCount, setCartCount] = React.useState(0);
  const [wishlistCount, setWishlistCount] = React.useState(0);

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

  // Simulate cart/wishlist from localStorage
  React.useEffect(() => {
    const cart = JSON.parse(localStorage.getItem("cart") || "[]");
    const wishlist = JSON.parse(localStorage.getItem("wishlist") || "[]");
    setCartCount(cart.length);
    setWishlistCount(wishlist.length);
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      <Header
        cartItemCount={cartCount}
        wishlistCount={wishlistCount}
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
