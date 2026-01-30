"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  ArrowLeft,
  DollarSign,
  CreditCard,
  TrendingUp,
  Shield,
  Check,
  Wallet,
  PiggyBank,
  Target,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Slider } from "@/components/ui/slider";
import { formatCurrency } from "@/lib/utils";

const creditScoreOptions = [
  { id: "poor", label: "Poor", range: "300-579", color: "text-red-500" },
  { id: "fair", label: "Fair", range: "580-669", color: "text-orange-500" },
  { id: "good", label: "Good", range: "670-739", color: "text-yellow-500" },
  { id: "excellent", label: "Excellent", range: "740-850", color: "text-green-500" },
];

const riskToleranceOptions = [
  { id: "conservative", label: "Conservative", description: "Prefer safe, reliable products", icon: Shield },
  { id: "moderate", label: "Moderate", description: "Balance between value and quality", icon: TrendingUp },
  { id: "aggressive", label: "Aggressive", description: "Willing to try new, innovative products", icon: Target },
];

const paymentMethods = [
  { id: "credit_card", label: "Credit Card", icon: CreditCard },
  { id: "debit_card", label: "Debit Card", icon: Wallet },
  { id: "paypal", label: "PayPal", icon: DollarSign },
  { id: "crypto", label: "Cryptocurrency", icon: PiggyBank },
  { id: "installments", label: "Installments", icon: TrendingUp },
];

const priceSensitivityOptions = [
  { id: "low", label: "Not Price Sensitive", description: "Quality matters more than price" },
  { id: "medium", label: "Balanced", description: "Look for good value" },
  { id: "high", label: "Price Conscious", description: "Always hunting for deals" },
];

const qualityPreferenceOptions = [
  { id: "budget", label: "Budget", description: "Affordable essentials" },
  { id: "mid-range", label: "Mid-Range", description: "Good quality, fair price" },
  { id: "premium", label: "Premium", description: "Top-tier products" },
];

export default function FinancialPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = React.useState(false);

  // Financial profile state
  const [monthlyIncome, setMonthlyIncome] = React.useState(5000);
  const [monthlyBudget, setMonthlyBudget] = React.useState(1000);
  const [savingsGoal] = React.useState(500);
  const [creditScore, setCreditScore] = React.useState<string>("good");
  const [riskTolerance, setRiskTolerance] = React.useState<string>("moderate");
  const [selectedPaymentMethods, setSelectedPaymentMethods] = React.useState<string[]>(["credit_card"]);
  const [priceSensitivity, setPriceSensitivity] = React.useState<string>("medium");
  const [qualityPreference, setQualityPreference] = React.useState<string>("mid-range");
  const [ecoFriendly, setEcoFriendly] = React.useState(false);
  const [localPreference, setLocalPreference] = React.useState(false);

  // Check if user is logged in
  React.useEffect(() => {
    const isLoggedIn = localStorage.getItem("isLoggedIn");
    if (isLoggedIn !== "true") {
      router.push("/login");
    }
  }, [router]);

  const togglePaymentMethod = (methodId: string) => {
    setSelectedPaymentMethods((prev) =>
      prev.includes(methodId)
        ? prev.filter((id) => id !== methodId)
        : [...prev, methodId]
    );
  };

  const handleBack = () => {
    router.push("/onboarding/interests");
  };

  const handleComplete = async () => {
    setIsLoading(true);

    // Get previously saved interests
    const categories = JSON.parse(localStorage.getItem("userCategories") || "[]");
    const brands = JSON.parse(localStorage.getItem("userBrands") || "[]");

    // Save complete profile
    const userProfile = {
      id: "demo-user-001",
      name: localStorage.getItem("userName") || "Demo User",
      email: localStorage.getItem("userEmail") || "demo@finfind.com",
      financialProfile: {
        monthlyIncome,
        monthlyBudget,
        savingsGoal,
        creditScoreRange: creditScore,
        riskTolerance,
        preferredPaymentMethods: selectedPaymentMethods,
      },
      preferences: {
        favoriteCategories: categories,
        favoriteBrands: brands,
        priceSensitivity,
        qualityPreference,
        ecoFriendly,
        localPreference,
      },
    };

    localStorage.setItem("userProfile", JSON.stringify(userProfile));
    localStorage.setItem("onboardingComplete", "true");

    // Simulate saving delay
    await new Promise((resolve) => setTimeout(resolve, 800));

    // Dispatch event for profile update
    window.dispatchEvent(new Event("profileUpdated"));

    router.push("/");
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary/5 via-background to-background px-4 py-8">
      <div className="mx-auto max-w-3xl">
        {/* Progress Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Step 2 of 2</span>
            <span className="text-sm text-muted-foreground">100%</span>
          </div>
          <Progress value={100} className="h-2" />
        </div>

        <Card>
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-green-500 to-green-600">
              <DollarSign className="h-8 w-8 text-white" />
            </div>
            <CardTitle className="text-2xl">Tell us about your finances</CardTitle>
            <CardDescription>
              This helps us recommend products that fit your budget and financial goals.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-8">
            {/* Income & Budget Section */}
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-3">
                <label className="font-medium flex items-center gap-2">
                  <Wallet className="h-4 w-4" />
                  Monthly Income
                </label>
                <div className="flex items-center gap-4">
                  <Slider
                    value={[monthlyIncome]}
                    onValueChange={([value]) => setMonthlyIncome(value)}
                    min={1000}
                    max={20000}
                    step={500}
                    className="flex-1"
                  />
                  <span className="text-lg font-semibold w-24 text-right">
                    {formatCurrency(monthlyIncome)}
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                <label className="font-medium flex items-center gap-2">
                  <PiggyBank className="h-4 w-4" />
                  Monthly Shopping Budget
                </label>
                <div className="flex items-center gap-4">
                  <Slider
                    value={[monthlyBudget]}
                    onValueChange={([value]) => setMonthlyBudget(value)}
                    min={100}
                    max={5000}
                    step={100}
                    className="flex-1"
                  />
                  <span className="text-lg font-semibold w-24 text-right">
                    {formatCurrency(monthlyBudget)}
                  </span>
                </div>
              </div>
            </div>

            {/* Credit Score */}
            <div className="space-y-3">
              <label className="font-medium">Credit Score Range</label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {creditScoreOptions.map((option) => (
                  <button
                    key={option.id}
                    onClick={() => setCreditScore(option.id)}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      creditScore === option.id
                        ? "border-primary bg-primary/10"
                        : "border-border hover:border-primary/50"
                    }`}
                  >
                    <div className={`font-semibold ${option.color}`}>
                      {option.label}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {option.range}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Risk Tolerance */}
            <div className="space-y-3">
              <label className="font-medium">Shopping Risk Tolerance</label>
              <div className="grid gap-3 md:grid-cols-3">
                {riskToleranceOptions.map((option) => {
                  const Icon = option.icon;
                  return (
                    <button
                      key={option.id}
                      onClick={() => setRiskTolerance(option.id)}
                      className={`p-4 rounded-lg border-2 transition-all text-left ${
                        riskTolerance === option.id
                          ? "border-primary bg-primary/10"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Icon className="h-4 w-4" />
                        <span className="font-semibold">{option.label}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {option.description}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Payment Methods */}
            <div className="space-y-3">
              <label className="font-medium">Preferred Payment Methods</label>
              <div className="flex flex-wrap gap-2">
                {paymentMethods.map((method) => {
                  const Icon = method.icon;
                  const isSelected = selectedPaymentMethods.includes(method.id);
                  return (
                    <button
                      key={method.id}
                      onClick={() => togglePaymentMethod(method.id)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-full border-2 transition-all ${
                        isSelected
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {method.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Price Sensitivity & Quality */}
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-3">
                <label className="font-medium">Price Sensitivity</label>
                <div className="space-y-2">
                  {priceSensitivityOptions.map((option) => (
                    <button
                      key={option.id}
                      onClick={() => setPriceSensitivity(option.id)}
                      className={`w-full p-3 rounded-lg border-2 text-left transition-all ${
                        priceSensitivity === option.id
                          ? "border-primary bg-primary/10"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      <div className="font-semibold">{option.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {option.description}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="font-medium">Quality Preference</label>
                <div className="space-y-2">
                  {qualityPreferenceOptions.map((option) => (
                    <button
                      key={option.id}
                      onClick={() => setQualityPreference(option.id)}
                      className={`w-full p-3 rounded-lg border-2 text-left transition-all ${
                        qualityPreference === option.id
                          ? "border-primary bg-primary/10"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      <div className="font-semibold">{option.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {option.description}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Additional Preferences */}
            <div className="space-y-3">
              <label className="font-medium">Additional Preferences</label>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => setEcoFriendly(!ecoFriendly)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full border-2 transition-all ${
                    ecoFriendly
                      ? "border-green-500 bg-green-500/10 text-green-600"
                      : "border-border hover:border-green-500/50"
                  }`}
                >
                  {ecoFriendly && <Check className="h-4 w-4" />}
                  🌱 Eco-Friendly Products
                </button>
                <button
                  onClick={() => setLocalPreference(!localPreference)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full border-2 transition-all ${
                    localPreference
                      ? "border-blue-500 bg-blue-500/10 text-blue-600"
                      : "border-border hover:border-blue-500/50"
                  }`}
                >
                  {localPreference && <Check className="h-4 w-4" />}
                  📍 Local Products
                </button>
              </div>
            </div>

            {/* Navigation Buttons */}
            <div className="pt-4 flex justify-between">
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button
                onClick={handleComplete}
                size="lg"
                disabled={isLoading}
                className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
              >
                {isLoading ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent mr-2" />
                    Setting up your profile...
                  </>
                ) : (
                  <>
                    Complete Setup
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
