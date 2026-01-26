"use client";

import * as React from "react";
import { DollarSign, TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn, formatCurrency, calculateAffordability } from "@/lib/utils";

interface AffordabilityIndicatorProps {
  price: number;
  monthlyBudget?: number;
  variant?: "badge" | "bar" | "detailed";
  showRecommendation?: boolean;
  className?: string;
}

export function AffordabilityIndicator({
  price,
  monthlyBudget,
  variant = "badge",
  showRecommendation = true,
  className,
}: AffordabilityIndicatorProps) {
  if (!monthlyBudget) {
    return null;
  }

  const affordability = calculateAffordability(price, monthlyBudget);
  const percentage = Math.min(affordability.percentage, 100);

  const getStatusColor = () => {
    if (affordability.percentage <= 10) return "green";
    if (affordability.percentage <= 20) return "emerald";
    if (affordability.percentage <= 30) return "yellow";
    if (affordability.percentage <= 50) return "orange";
    return "red";
  };

  const statusColor = getStatusColor();

  const colorClasses = {
    green: {
      bg: "bg-green-100 dark:bg-green-900/30",
      text: "text-green-700 dark:text-green-400",
      border: "border-green-200 dark:border-green-800",
      progress: "bg-green-500",
    },
    emerald: {
      bg: "bg-emerald-100 dark:bg-emerald-900/30",
      text: "text-emerald-700 dark:text-emerald-400",
      border: "border-emerald-200 dark:border-emerald-800",
      progress: "bg-emerald-500",
    },
    yellow: {
      bg: "bg-yellow-100 dark:bg-yellow-900/30",
      text: "text-yellow-700 dark:text-yellow-400",
      border: "border-yellow-200 dark:border-yellow-800",
      progress: "bg-yellow-500",
    },
    orange: {
      bg: "bg-orange-100 dark:bg-orange-900/30",
      text: "text-orange-700 dark:text-orange-400",
      border: "border-orange-200 dark:border-orange-800",
      progress: "bg-orange-500",
    },
    red: {
      bg: "bg-red-100 dark:bg-red-900/30",
      text: "text-red-700 dark:text-red-400",
      border: "border-red-200 dark:border-red-800",
      progress: "bg-red-500",
    },
  };

  const colors = colorClasses[statusColor];

  const Icon = affordability.isAffordable ? CheckCircle : AlertTriangle;
  const TrendIcon = affordability.percentage <= 20 ? TrendingDown : TrendingUp;

  if (variant === "badge") {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge
              variant="outline"
              className={cn(
                "cursor-help gap-1",
                colors.bg,
                colors.text,
                colors.border,
                className
              )}
            >
              <DollarSign className="h-3 w-3" />
              {affordability.percentage.toFixed(0)}% of budget
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1">
              <p className="font-medium">
                {formatCurrency(price)} of {formatCurrency(monthlyBudget)}/month
              </p>
              {showRecommendation && (
                <p className="text-sm text-muted-foreground">
                  {affordability.recommendation}
                </p>
              )}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  if (variant === "bar") {
    return (
      <div className={cn("space-y-2", className)}>
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-1 text-muted-foreground">
            <TrendIcon className="h-4 w-4" />
            Budget impact
          </span>
          <span className={colors.text}>
            {affordability.percentage.toFixed(0)}%
          </span>
        </div>
        <Progress
          value={percentage}
          className="h-2"
          indicatorClassName={colors.progress}
        />
        {showRecommendation && (
          <p className={cn("text-xs", colors.text)}>
            {affordability.recommendation}
          </p>
        )}
      </div>
    );
  }

  // Detailed variant
  return (
    <div
      className={cn(
        "rounded-lg border p-4",
        colors.bg,
        colors.border,
        className
      )}
    >
      <div className="flex items-start gap-3">
        <Icon className={cn("h-5 w-5 mt-0.5", colors.text)} />
        <div className="flex-1 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-medium">Affordability Analysis</span>
            <Badge variant="outline" className={cn(colors.text, colors.border)}>
              {affordability.percentage.toFixed(0)}% of budget
            </Badge>
          </div>
          
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Product price:</span>
              <span className="font-medium">{formatCurrency(price)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Monthly budget:</span>
              <span className="font-medium">{formatCurrency(monthlyBudget)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Remaining after:</span>
              <span className="font-medium">
                {formatCurrency(Math.max(0, monthlyBudget - price))}
              </span>
            </div>
          </div>

          {showRecommendation && (
            <p className={cn("text-sm font-medium mt-2", colors.text)}>
              💡 {affordability.recommendation}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
