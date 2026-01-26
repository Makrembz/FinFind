"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Search,
  User,
  ShoppingCart,
  Heart,
  Menu,
  X,
  Sun,
  Moon,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface HeaderProps {
  cartItemCount?: number;
  wishlistCount?: number;
  isLoggedIn?: boolean;
  onToggleTheme?: () => void;
  isDarkMode?: boolean;
}

const navLinks = [
  { href: "/", label: "Home", icon: Search },
  { href: "/recommendations", label: "For You", icon: Sparkles },
];

export function Header({
  cartItemCount = 0,
  wishlistCount = 0,
  isLoggedIn = false,
  onToggleTheme,
  isDarkMode = false,
}: HeaderProps) {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <span className="text-lg font-bold text-primary-foreground">F</span>
          </div>
          <span className="text-xl font-bold">FinFind</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden items-center gap-6 md:flex">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            const Icon = link.icon;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary",
                  isActive ? "text-primary" : "text-muted-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Desktop Actions */}
        <div className="hidden items-center gap-2 md:flex">
          {/* Theme toggle */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onToggleTheme}
                  aria-label="Toggle theme"
                >
                  {isDarkMode ? (
                    <Sun className="h-5 w-5" />
                  ) : (
                    <Moon className="h-5 w-5" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{isDarkMode ? "Light mode" : "Dark mode"}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {/* Wishlist */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Link href="/wishlist">
                  <Button variant="ghost" size="icon" className="relative">
                    <Heart className="h-5 w-5" />
                    {wishlistCount > 0 && (
                      <Badge
                        className="absolute -right-1 -top-1 h-5 w-5 rounded-full p-0 text-xs"
                        variant="destructive"
                      >
                        {wishlistCount > 9 ? "9+" : wishlistCount}
                      </Badge>
                    )}
                  </Button>
                </Link>
              </TooltipTrigger>
              <TooltipContent>
                <p>Wishlist</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {/* Cart */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Link href="/cart">
                  <Button variant="ghost" size="icon" className="relative">
                    <ShoppingCart className="h-5 w-5" />
                    {cartItemCount > 0 && (
                      <Badge
                        className="absolute -right-1 -top-1 h-5 w-5 rounded-full p-0 text-xs"
                        variant="default"
                      >
                        {cartItemCount > 9 ? "9+" : cartItemCount}
                      </Badge>
                    )}
                  </Button>
                </Link>
              </TooltipTrigger>
              <TooltipContent>
                <p>Cart</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {/* Profile/Login */}
          {isLoggedIn ? (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link href="/profile">
                    <Button variant="ghost" size="icon">
                      <User className="h-5 w-5" />
                    </Button>
                  </Link>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Profile</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ) : (
            <Link href="/login">
              <Button variant="default" size="sm">
                Sign In
              </Button>
            </Link>
          )}
        </div>

        {/* Mobile Menu Button */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
        >
          {isMobileMenuOpen ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
        </Button>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="border-t md:hidden">
          <nav className="container mx-auto flex flex-col gap-2 p-4">
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg p-3 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
                  )}
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <Icon className="h-5 w-5" />
                  {link.label}
                </Link>
              );
            })}

            <div className="my-2 h-px bg-border" />

            {/* Mobile actions */}
            <Link
              href="/wishlist"
              className="flex items-center gap-3 rounded-lg p-3 text-sm font-medium hover:bg-muted"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              <Heart className="h-5 w-5" />
              Wishlist
              {wishlistCount > 0 && (
                <Badge variant="secondary" className="ml-auto">
                  {wishlistCount}
                </Badge>
              )}
            </Link>

            <Link
              href="/cart"
              className="flex items-center gap-3 rounded-lg p-3 text-sm font-medium hover:bg-muted"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              <ShoppingCart className="h-5 w-5" />
              Cart
              {cartItemCount > 0 && (
                <Badge variant="secondary" className="ml-auto">
                  {cartItemCount}
                </Badge>
              )}
            </Link>

            <Link
              href={isLoggedIn ? "/profile" : "/login"}
              className="flex items-center gap-3 rounded-lg p-3 text-sm font-medium hover:bg-muted"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              <User className="h-5 w-5" />
              {isLoggedIn ? "Profile" : "Sign In"}
            </Link>

            <button
              className="flex items-center gap-3 rounded-lg p-3 text-sm font-medium hover:bg-muted"
              onClick={() => {
                onToggleTheme?.();
                setIsMobileMenuOpen(false);
              }}
            >
              {isDarkMode ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
              {isDarkMode ? "Light Mode" : "Dark Mode"}
            </button>
          </nav>
        </div>
      )}
    </header>
  );
}
