"use client";

import * as React from "react";
import {
  User,
  Mail,
  DollarSign,
  Heart,
  ShoppingBag,
  Settings,
  Bell,
  Shield,
  LogOut,
  Edit,
  Save,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Slider } from "@/components/ui/slider";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useUser, useUpdateUserPreferences, useUpdateFinancialProfile } from "@/hooks/useApi";
import { formatCurrency } from "@/lib/utils";
import type { UserPreferences, FinancialProfile } from "@/types";

export default function ProfilePage() {
  // Demo user ID (in production, this would come from auth context)
  const userId = "013c3cb2-482a-55b0-9559-6688c3b78313";

  const { data: userData, isLoading } = useUser(userId);
  const updatePreferences = useUpdateUserPreferences(userId);
  const updateFinancialProfile = useUpdateFinancialProfile(userId);

  const user = userData?.profile;

  const [isEditing, setIsEditing] = React.useState(false);
  const [editedBudget, setEditedBudget] = React.useState(1000);
  const [editedCategories, setEditedCategories] = React.useState<string[]>([]);
  const [editedBrands, setEditedBrands] = React.useState<string[]>([]);

  // Initialize edited values when user data loads
  React.useEffect(() => {
    if (user) {
      setEditedBudget(user.financialProfile?.monthlyBudget || 1000);
      setEditedCategories(user.preferences?.favoriteCategories || []);
      setEditedBrands(user.preferences?.favoriteBrands || []);
    }
  }, [user]);

  const handleSavePreferences = () => {
    updatePreferences.mutate({
      favoriteCategories: editedCategories,
      favoriteBrands: editedBrands,
    });
    updateFinancialProfile.mutate({
      monthlyBudget: editedBudget,
    });
    setIsEditing(false);
  };

  const allCategories = [
    "Electronics",
    "Fashion",
    "Home & Garden",
    "Sports",
    "Books",
    "Beauty",
    "Toys",
    "Automotive",
    "Health",
    "Food",
  ];

  const allBrands = [
    "Apple",
    "Samsung",
    "Nike",
    "Adidas",
    "Sony",
    "LG",
    "Dell",
    "HP",
    "Amazon",
    "Google",
  ];

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 lg:px-6">
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Skeleton className="h-24 w-24 rounded-2xl" />
            <div className="space-y-2">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-32" />
            </div>
          </div>
          <Skeleton className="h-64 w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  const displayUser = user || {
    id: userId,
    name: "Demo User",
    email: "demo@finfind.com",
    avatarUrl: undefined,
    financialProfile: { monthlyBudget: 1000 },
    preferences: { favoriteCategories: [] as string[], favoriteBrands: [] as string[] },
  };

  return (
    <div className="container mx-auto px-4 py-8 lg:px-6">
      {/* Profile Header */}
      <div className="mb-8 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-5">
          <Avatar className="h-24 w-24 rounded-2xl border-2 border-border/60 shadow-lg shadow-black/5">
            <AvatarImage src={displayUser.avatarUrl} className="rounded-2xl" />
            <AvatarFallback className="text-2xl rounded-2xl bg-gradient-to-br from-primary to-primary/60 text-primary-foreground">
              {displayUser.name?.charAt(0) || "U"}
            </AvatarFallback>
          </Avatar>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{displayUser.name}</h1>
            <p className="text-muted-foreground">{displayUser.email}</p>
            <Badge variant="secondary" className="mt-2 rounded-full">
              Member since {new Date().getFullYear()}
            </Badge>
          </div>
        </div>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button onClick={handleSavePreferences} disabled={updatePreferences.isPending}>
                <Save className="mr-2 h-4 w-4" />
                Save Changes
              </Button>
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                <X className="mr-2 h-4 w-4" />
                Cancel
              </Button>
            </>
          ) : (
            <Button onClick={() => setIsEditing(true)}>
              <Edit className="mr-2 h-4 w-4" />
              Edit Profile
            </Button>
          )}
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="bg-muted/50 border border-border/60 rounded-xl p-1">
          <TabsTrigger value="overview" className="rounded-lg">Overview</TabsTrigger>
          <TabsTrigger value="preferences" className="rounded-lg">Preferences</TabsTrigger>
          <TabsTrigger value="financial" className="rounded-lg">Financial</TabsTrigger>
          <TabsTrigger value="activity" className="rounded-lg">Activity</TabsTrigger>
          <TabsTrigger value="settings" className="rounded-lg">Settings</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-border/60">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Monthly Budget</CardTitle>
                <div className="h-8 w-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                  <DollarSign className="h-4 w-4 text-emerald-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-semibold tracking-tight">
                  {formatCurrency(displayUser.financialProfile?.monthlyBudget || 0)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Available for shopping
                </p>
              </CardContent>
            </Card>

            <Card className="border-border/60">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Wishlist Items</CardTitle>
                <div className="h-8 w-8 rounded-lg bg-rose-500/10 flex items-center justify-center">
                  <Heart className="h-4 w-4 text-rose-500" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-semibold tracking-tight">
                  {JSON.parse(localStorage.getItem("wishlist") || "[]").length}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Products saved
                </p>
              </CardContent>
            </Card>

            <Card className="border-border/60">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Cart Items</CardTitle>
                <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                  <ShoppingBag className="h-4 w-4 text-primary" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-semibold tracking-tight">
                  {JSON.parse(localStorage.getItem("cart") || "[]").length}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Ready to checkout
                </p>
              </CardContent>
            </Card>

            <Card className="border-border/60">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Categories</CardTitle>
                <div className="h-8 w-8 rounded-lg bg-violet-500/10 flex items-center justify-center">
                  <Settings className="h-4 w-4 text-violet-500" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-semibold tracking-tight">
                  {displayUser.preferences?.favoriteCategories?.length || 0}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Favorites set
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Quick Stats */}
          <Card className="border-border/60">
            <CardHeader>
              <CardTitle className="text-lg">Budget Usage</CardTitle>
              <CardDescription>
                Track your spending against your monthly budget
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Spent this month</span>
                  <span className="font-medium">$0 of {formatCurrency(displayUser.financialProfile?.monthlyBudget || 0)}</span>
                </div>
                <Progress value={0} className="h-2" />
              </div>
              <p className="text-sm text-muted-foreground">
                You have your full budget available. Start shopping to see usage stats!
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences" className="space-y-6">
          <Card className="border-border/60">
            <CardHeader>
              <CardTitle className="text-lg">Favorite Categories</CardTitle>
              <CardDescription>
                Select categories you're interested in for better recommendations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {allCategories.map((category) => {
                  const isSelected = isEditing
                    ? editedCategories.includes(category)
                    : displayUser.preferences?.favoriteCategories?.includes(category);
                  return (
                    <Badge
                      key={category}
                      variant={isSelected ? "default" : "outline"}
                      className={`cursor-pointer rounded-full transition-all duration-200 ${isEditing ? "hover:bg-primary/80" : ""}`}
                      onClick={() => {
                        if (isEditing) {
                          setEditedCategories((prev) =>
                            prev.includes(category)
                              ? prev.filter((c) => c !== category)
                              : [...prev, category]
                          );
                        }
                      }}
                    >
                      {category}
                    </Badge>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/60">
            <CardHeader>
              <CardTitle className="text-lg">Favorite Brands</CardTitle>
              <CardDescription>
                Select brands you prefer for personalized results
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {allBrands.map((brand) => {
                  const isSelected = isEditing
                    ? editedBrands.includes(brand)
                    : displayUser.preferences?.favoriteBrands?.includes(brand);
                  return (
                    <Badge
                      key={brand}
                      variant={isSelected ? "default" : "outline"}
                      className={`cursor-pointer ${isEditing ? "hover:bg-primary/80" : ""}`}
                      onClick={() => {
                        if (isEditing) {
                          setEditedBrands((prev) =>
                            prev.includes(brand)
                              ? prev.filter((b) => b !== brand)
                              : [...prev, brand]
                          );
                        }
                      }}
                    >
                      {brand}
                    </Badge>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Financial Tab */}
        <TabsContent value="financial" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Monthly Budget</CardTitle>
              <CardDescription>
                Set your monthly shopping budget for better affordability insights
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Budget amount</span>
                  <span className="text-2xl font-bold">
                    {formatCurrency(isEditing ? editedBudget : displayUser.financialProfile?.monthlyBudget || 0)}
                  </span>
                </div>
                {isEditing && (
                  <Slider
                    value={[editedBudget]}
                    onValueChange={(value) => setEditedBudget(value[0])}
                    min={100}
                    max={10000}
                    step={50}
                    className="w-full"
                  />
                )}
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>$100</span>
                  <span>$10,000</span>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-lg border p-4 text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency((isEditing ? editedBudget : displayUser.financialProfile?.monthlyBudget || 0) * 0.2)}
                  </p>
                  <p className="text-sm text-muted-foreground">Affordable range (20%)</p>
                </div>
                <div className="rounded-lg border p-4 text-center">
                  <p className="text-2xl font-bold text-yellow-600">
                    {formatCurrency((isEditing ? editedBudget : displayUser.financialProfile?.monthlyBudget || 0) * 0.5)}
                  </p>
                  <p className="text-sm text-muted-foreground">Consider range (50%)</p>
                </div>
                <div className="rounded-lg border p-4 text-center">
                  <p className="text-2xl font-bold text-red-600">
                    {formatCurrency((isEditing ? editedBudget : displayUser.financialProfile?.monthlyBudget || 0) * 1)}
                  </p>
                  <p className="text-sm text-muted-foreground">Full budget (100%)</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Price Alerts</CardTitle>
              <CardDescription>
                Get notified when products in your wishlist drop in price
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Price drop notifications</p>
                  <p className="text-sm text-muted-foreground">
                    Receive alerts when items go on sale
                  </p>
                </div>
                <Badge variant="outline">Coming soon</Badge>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Activity Tab */}
        <TabsContent value="activity" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Your recent searches and interactions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <ShoppingBag className="mb-4 h-12 w-12 text-muted-foreground" />
                <h3 className="mb-2 font-medium">No recent activity</h3>
                <p className="text-sm text-muted-foreground">
                  Your browsing history and purchases will appear here
                </p>
                <Button className="mt-4" onClick={() => window.location.href = "/"}>
                  Start Shopping
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Account Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between py-2">
                <div className="flex items-center gap-3">
                  <Bell className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Notifications</p>
                    <p className="text-sm text-muted-foreground">
                      Manage email and push notifications
                    </p>
                  </div>
                </div>
                <Button variant="outline" size="sm">Manage</Button>
              </div>

              <div className="flex items-center justify-between border-t py-2 pt-4">
                <div className="flex items-center gap-3">
                  <Shield className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Privacy</p>
                    <p className="text-sm text-muted-foreground">
                      Control your data and privacy settings
                    </p>
                  </div>
                </div>
                <Button variant="outline" size="sm">Manage</Button>
              </div>

              <div className="flex items-center justify-between border-t py-2 pt-4">
                <div className="flex items-center gap-3">
                  <LogOut className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Sign Out</p>
                    <p className="text-sm text-muted-foreground">
                      Sign out of your account
                    </p>
                  </div>
                </div>
                <Button variant="outline" size="sm">Sign Out</Button>
              </div>
            </CardContent>
          </Card>

          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="text-destructive">Danger Zone</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Delete Account</p>
                  <p className="text-sm text-muted-foreground">
                    Permanently delete your account and all data
                  </p>
                </div>
                <Button variant="destructive" size="sm">Delete</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
