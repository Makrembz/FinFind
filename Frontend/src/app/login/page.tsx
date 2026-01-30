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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-primary/5 via-background to-background px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-primary to-primary/60">
            <Sparkles className="h-8 w-8 text-primary-foreground" />
          </div>
          <CardTitle className="text-2xl">Welcome to FinFind</CardTitle>
          <CardDescription>
            Sign in to access personalized product recommendations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="email">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="password">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" size="lg" disabled={isLoading}>
              {isLoading ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent mr-2" />
                  Signing in...
                </>
              ) : (
                <>
                  <LogIn className="mr-2 h-4 w-4" />
                  Sign In
                </>
              )}
            </Button>

            <div className="mt-4 p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground text-center">
                <strong>Demo credentials:</strong><br />
                Email: <code className="bg-background px-1 rounded">demo@finfind.com</code><br />
                Password: <code className="bg-background px-1 rounded">demo</code>
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
