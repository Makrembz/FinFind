"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { LogIn, Mail, Lock, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);

  // Check if user is already logged in
  React.useEffect(() => {
    const isLoggedIn = localStorage.getItem("isLoggedIn");
    const onboardingComplete = localStorage.getItem("onboardingComplete");
    
    if (isLoggedIn === "true") {
      if (onboardingComplete === "true") {
        router.push("/");
      } else {
        router.push("/onboarding/interests");
      }
    }
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    // Simulate login delay
    await new Promise((resolve) => setTimeout(resolve, 800));

    // Static credentials check
    if (email.toLowerCase() === "demo@finfind.com" && password === "demo") {
      // Set user session
      localStorage.setItem("isLoggedIn", "true");
      localStorage.setItem("userId", "demo-user-001");
      localStorage.setItem("userName", "Demo User");
      localStorage.setItem("userEmail", "demo@finfind.com");
      
      // Check if onboarding is complete
      const onboardingComplete = localStorage.getItem("onboardingComplete");
      if (onboardingComplete === "true") {
        router.push("/");
      } else {
        router.push("/onboarding/interests");
      }
    } else {
      setError("Invalid email or password");
    }

    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-muted/30 via-background to-background px-4">
      {/* Subtle background elements */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute left-1/4 top-1/4 h-[400px] w-[400px] rounded-full bg-primary/5 blur-[120px]" />
        <div className="absolute right-1/4 bottom-1/4 h-[300px] w-[300px] rounded-full bg-blue-500/5 blur-[100px]" />
      </div>

      <Card className="w-full max-w-md border-border/60 shadow-xl shadow-black/5">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-primary/80 shadow-lg shadow-primary/20">
            <Sparkles className="h-8 w-8 text-primary-foreground" />
          </div>
          <CardTitle className="text-2xl font-semibold tracking-tight">Welcome back</CardTitle>
          <CardDescription className="text-muted-foreground">
            Sign in to access personalized recommendations
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <form onSubmit={handleLogin} className="space-y-5">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground" htmlFor="email">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/60" />
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-11"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground" htmlFor="password">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/60" />
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-11"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="rounded-xl bg-destructive/10 border border-destructive/20 p-3.5 text-sm text-destructive">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" size="lg" disabled={isLoading}>
              {isLoading ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <LogIn className="h-4 w-4" />
                </>
              )}
            </Button>

            <div className="mt-6 p-4 bg-muted/50 border border-border/60 rounded-xl">
              <p className="text-sm text-muted-foreground text-center">
                <span className="font-medium text-foreground">Demo credentials</span><br />
                <span className="mt-1 inline-block">
                  <code className="bg-background border border-border/60 px-2 py-0.5 rounded-md text-xs">demo@finfind.com</code>
                  {" / "}
                  <code className="bg-background border border-border/60 px-2 py-0.5 rounded-md text-xs">demo</code>
                </span>
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
