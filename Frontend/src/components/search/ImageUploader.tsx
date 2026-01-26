"use client";

import * as React from "react";
import Image from "next/image";
import { Upload, X, Camera, ImageIcon, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { cn, validateImageFile, fileToBase64 } from "@/lib/utils";

interface ImageUploaderProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (imageData: string) => void;
  isProcessing?: boolean;
}

export function ImageUploader({
  isOpen,
  onClose,
  onUpload,
  isProcessing = false,
}: ImageUploaderProps) {
  const [preview, setPreview] = React.useState<string | null>(null);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [isDragging, setIsDragging] = React.useState(false);
  const [isConverting, setIsConverting] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Handle file selection
  const handleFileSelect = (file: File) => {
    setError(null);

    const validation = validateImageFile(file);
    if (!validation.valid) {
      setError(validation.error || "Invalid file");
      return;
    }

    setSelectedFile(file);

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  // Handle file input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  // Handle drag events
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  // Handle search
  const handleSearch = async () => {
    if (selectedFile && preview) {
      setIsConverting(true);
      try {
        // Use the preview (data URL) directly
        onUpload(preview);
      } finally {
        setIsConverting(false);
      }
    }
  };

  // Clear selection
  const handleClear = () => {
    setPreview(null);
    setSelectedFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Handle close
  const handleClose = () => {
    handleClear();
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Image Search</DialogTitle>
          <DialogDescription>
            Upload an image to find similar products
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Upload area */}
          {!preview && (
            <div
              className={cn(
                "relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors",
                isDragging
                  ? "border-primary bg-primary/5"
                  : "border-muted-foreground/25 hover:border-primary/50",
                error && "border-destructive"
              )}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                onChange={handleInputChange}
                className="absolute inset-0 cursor-pointer opacity-0"
                aria-label="Upload image"
              />

              <div className="flex flex-col items-center gap-4">
                <div className="rounded-full bg-muted p-4">
                  <ImageIcon className="h-8 w-8 text-muted-foreground" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium">
                    Drag and drop an image here
                  </p>
                  <p className="text-sm text-muted-foreground">
                    or click to browse
                  </p>
                </div>
                <p className="text-xs text-muted-foreground">
                  Supports: JPEG, PNG, WebP, GIF (max 10MB)
                </p>
              </div>
            </div>
          )}

          {/* Preview */}
          {preview && (
            <div className="relative">
              <div className="relative aspect-video overflow-hidden rounded-lg bg-muted">
                <Image
                  src={preview}
                  alt="Upload preview"
                  fill
                  className="object-contain"
                />
              </div>
              <Button
                variant="destructive"
                size="icon"
                className="absolute right-2 top-2"
                onClick={handleClear}
                disabled={isProcessing}
                aria-label="Remove image"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Error message */}
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isProcessing || isConverting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSearch}
              disabled={!selectedFile || isProcessing || isConverting}
            >
              {isProcessing || isConverting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Camera className="mr-2 h-4 w-4" />
                  Search
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
