"use client";

import * as React from "react";
import {
  Send,
  Bot,
  User,
  Loader2,
  MessageSquare,
  X,
  Minimize2,
  Maximize2,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useSendMessage, useChatHistory, useCreateSession } from "@/hooks/useApi";
import type { ChatMessage, ProductSearchResult } from "@/types";
import { ProductCard } from "./ProductCard";

interface ChatInterfaceProps {
  userId: string;
  sessionId?: string;
  monthlyBudget?: number;
  variant?: "full" | "floating";
  className?: string;
}

export function ChatInterface({
  userId,
  sessionId: initialSessionId,
  monthlyBudget,
  variant = "full",
  className,
}: ChatInterfaceProps) {
  const [isOpen, setIsOpen] = React.useState(variant === "full");
  const [isMinimized, setIsMinimized] = React.useState(false);
  const [inputValue, setInputValue] = React.useState("");
  const [sessionId, setSessionId] = React.useState(initialSessionId);
  const [localMessages, setLocalMessages] = React.useState<ChatMessage[]>([]);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const createSession = useCreateSession();
  const sendMessage = useSendMessage(sessionId ?? "");
  const { data: chatHistory, isLoading: isLoadingHistory } = useChatHistory(sessionId);

  // Initialize session
  React.useEffect(() => {
    if (!sessionId && userId) {
      createSession.mutate(userId, {
        onSuccess: (data) => {
          setSessionId(data.sessionId);
        },
      });
    }
  }, [sessionId, userId]);

  // Update local messages when history loads
  React.useEffect(() => {
    if (chatHistory?.messages) {
      setLocalMessages(chatHistory.messages);
    }
  }, [chatHistory]);

  // Scroll to bottom on new messages
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [localMessages]);

  // Focus input when opened
  React.useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !sessionId || sendMessage.isPending) return;

    const userMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date().toISOString(),
    };

    setLocalMessages((prev) => [...prev, userMessage]);
    setInputValue("");

    sendMessage.mutate(
      { message: inputValue.trim() },
      {
        onSuccess: (response) => {
          const assistantMessage: ChatMessage = {
            id: `resp-${Date.now()}`,
            role: "assistant",
            content: response.message,
            timestamp: new Date().toISOString(),
            products: response.products,
          };
          setLocalMessages((prev) => [...prev, assistantMessage]);
        },
        onError: () => {
          // Remove the optimistic user message on error
          setLocalMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
          // Add error message
          setLocalMessages((prev) => [
            ...prev,
            {
              id: `error-${Date.now()}`,
              role: "assistant",
              content: "Sorry, I encountered an error. Please try again.",
              timestamp: new Date().toISOString(),
            },
          ]);
        },
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewSession = () => {
    setLocalMessages([]);
    setSessionId(undefined);
    createSession.mutate(userId, {
      onSuccess: (data) => {
        setSessionId(data.sessionId);
      },
    });
  };

  // Message component
  const Message = ({ message }: { message: ChatMessage }) => {
    const isUser = message.role === "user";

    return (
      <div
        className={cn(
          "flex gap-3",
          isUser ? "flex-row-reverse" : "flex-row"
        )}
      >
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className={isUser ? "bg-primary text-primary-foreground" : "bg-muted"}>
            {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
          </AvatarFallback>
        </Avatar>
        <div
          className={cn(
            "max-w-[80%] space-y-2",
            isUser ? "items-end" : "items-start"
          )}
        >
          <div
            className={cn(
              "rounded-lg px-3 py-2 text-sm",
              isUser
                ? "bg-primary text-primary-foreground"
                : "bg-muted"
            )}
          >
            {message.content}
          </div>

          {/* Product recommendations */}
          {message.products && message.products.length > 0 && (
            <div className="mt-3 space-y-2">
              <Badge variant="outline" className="text-xs">
                {message.products.length} product{message.products.length > 1 ? "s" : ""} found
              </Badge>
              <div className="grid gap-2">
                {message.products.slice(0, 3).map((product: ProductSearchResult) => (
                  <MiniProductCard
                    key={product.id}
                    product={product}
                    monthlyBudget={monthlyBudget}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Mini product card for chat
  const MiniProductCard = ({
    product,
    monthlyBudget,
  }: {
    product: ProductSearchResult;
    monthlyBudget?: number;
  }) => (
    <a
      href={`/product/${product.id}`}
      className="flex gap-3 rounded-lg border bg-background p-2 transition-colors hover:bg-muted"
    >
      <div className="h-16 w-16 flex-shrink-0 overflow-hidden rounded bg-muted">
        {product.imageUrl ? (
          <img
            src={product.imageUrl}
            alt={product.name}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
            No img
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col justify-center overflow-hidden">
        <p className="truncate text-sm font-medium">{product.name}</p>
        <p className="text-sm font-bold">${product.price.toFixed(2)}</p>
        {product.matchScore !== undefined && (
          <Badge variant="secondary" className="mt-1 w-fit text-xs">
            {Math.round(product.matchScore * 100)}% match
          </Badge>
        )}
      </div>
    </a>
  );

  // Floating chat button
  if (variant === "floating" && !isOpen) {
    return (
      <Button
        className={cn(
          "fixed bottom-4 right-4 h-14 w-14 rounded-full shadow-lg",
          className
        )}
        onClick={() => setIsOpen(true)}
        aria-label="Open chat"
      >
        <MessageSquare className="h-6 w-6" />
      </Button>
    );
  }

  // Chat window
  const chatContent = (
    <>
      {/* Header */}
      <CardHeader className="flex flex-row items-center justify-between border-b p-3">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          <CardTitle className="text-base">FinFind Assistant</CardTitle>
          {sendMessage.isPending && (
            <Badge variant="secondary" className="text-xs">
              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              Thinking...
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleNewSession}
            aria-label="New conversation"
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
          {variant === "floating" && (
            <>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setIsMinimized(!isMinimized)}
                aria-label={isMinimized ? "Maximize" : "Minimize"}
              >
                {isMinimized ? (
                  <Maximize2 className="h-4 w-4" />
                ) : (
                  <Minimize2 className="h-4 w-4" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setIsOpen(false)}
                aria-label="Close chat"
              >
                <X className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>
      </CardHeader>

      {/* Messages */}
      {!isMinimized && (
        <>
          <CardContent className="flex-1 overflow-y-auto p-4">
            {isLoadingHistory ? (
              <div className="space-y-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="flex gap-3">
                    <Skeleton className="h-8 w-8 rounded-full" />
                    <div className="space-y-2">
                      <Skeleton className="h-4 w-48" />
                      <Skeleton className="h-4 w-32" />
                    </div>
                  </div>
                ))}
              </div>
            ) : localMessages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <Bot className="h-12 w-12 text-muted-foreground" />
                <h3 className="mt-4 font-medium">Hi! I&apos;m your FinFind assistant</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Ask me anything about products, recommendations, or help finding what you need.
                </p>
                <div className="mt-4 flex flex-wrap justify-center gap-2">
                  {[
                    "What's trending?",
                    "Help me find a laptop",
                    "Budget recommendations",
                  ].map((suggestion) => (
                    <Button
                      key={suggestion}
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setInputValue(suggestion);
                        inputRef.current?.focus();
                      }}
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {localMessages.map((message) => (
                  <Message key={message.id} message={message} />
                ))}
                {sendMessage.isPending && (
                  <div className="flex gap-3">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="bg-muted">
                        <Bot className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex items-center gap-1 rounded-lg bg-muted px-3 py-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm text-muted-foreground">Thinking...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </CardContent>

          {/* Input */}
          <div className="border-t p-3">
            <form
              className="flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
            >
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message..."
                disabled={!sessionId || sendMessage.isPending}
                className="flex-1"
              />
              <Button
                type="submit"
                size="icon"
                disabled={!inputValue.trim() || !sessionId || sendMessage.isPending}
                aria-label="Send message"
              >
                {sendMessage.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </form>
          </div>
        </>
      )}
    </>
  );

  if (variant === "floating") {
    return (
      <Card
        className={cn(
          "fixed bottom-4 right-4 flex w-96 flex-col shadow-xl",
          isMinimized ? "h-auto" : "h-[500px]",
          className
        )}
      >
        {chatContent}
      </Card>
    );
  }

  return (
    <Card className={cn("flex h-full flex-col", className)}>
      {chatContent}
    </Card>
  );
}
