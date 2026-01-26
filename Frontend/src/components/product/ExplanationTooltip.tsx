"use client";

import * as React from "react";
import { Info, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface ExplanationTooltipProps {
  explanation: string;
  title?: string;
  variant?: "inline" | "icon" | "badge";
  className?: string;
}

export function ExplanationTooltip({
  explanation,
  title = "Why this?",
  variant = "icon",
  className,
}: ExplanationTooltipProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  // Split explanation into bullet points if it contains multiple sentences
  const explanationPoints = explanation
    .split(/[.!?]+/)
    .filter((point) => point.trim().length > 0)
    .map((point) => point.trim());

  if (variant === "inline") {
    return (
      <div className={cn("rounded-lg border bg-muted/50 p-3", className)}>
        <button
          className="flex w-full items-center justify-between text-left"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
        >
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-blue-500" />
            <span className="text-sm font-medium">{title}</span>
          </div>
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>
        {isExpanded && (
          <div className="mt-2 text-sm text-muted-foreground">
            {explanationPoints.length > 1 ? (
              <ul className="list-inside list-disc space-y-1">
                {explanationPoints.map((point, index) => (
                  <li key={index}>{point}</li>
                ))}
              </ul>
            ) : (
              <p>{explanation}</p>
            )}
          </div>
        )}
      </div>
    );
  }

  if (variant === "badge") {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              className={cn(
                "inline-flex items-center gap-1 rounded-full border px-2 py-1 text-xs transition-colors hover:bg-muted",
                className
              )}
            >
              <Info className="h-3 w-3 text-blue-500" />
              <span>{title}</span>
            </button>
          </TooltipTrigger>
          <TooltipContent className="max-w-xs">
            {explanationPoints.length > 1 ? (
              <ul className="list-inside list-disc space-y-1">
                {explanationPoints.map((point, index) => (
                  <li key={index}>{point}</li>
                ))}
              </ul>
            ) : (
              <p>{explanation}</p>
            )}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Default: icon variant
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className={cn("h-6 w-6", className)}
            aria-label="Show explanation"
          >
            <Info className="h-4 w-4 text-blue-500" />
          </Button>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <div className="space-y-2">
            <p className="font-medium">{title}</p>
            {explanationPoints.length > 1 ? (
              <ul className="list-inside list-disc space-y-1 text-sm">
                {explanationPoints.map((point, index) => (
                  <li key={index}>{point}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm">{explanation}</p>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
