"use client";

import * as React from "react";
import { Mic, MicOff, Loader2, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { useTranscribeAudio } from "@/hooks/useApi";

interface VoiceRecorderProps {
  isOpen: boolean;
  onClose: () => void;
  onResult: (transcript: string) => void;
  isProcessing?: boolean;
}

export function VoiceRecorder({
  isOpen,
  onClose,
  onResult,
  isProcessing: externalProcessing = false,
}: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = React.useState(false);
  const [recordingTime, setRecordingTime] = React.useState(0);
  const [audioLevel, setAudioLevel] = React.useState(0);
  const [error, setError] = React.useState<string | null>(null);

  const mediaRecorderRef = React.useRef<MediaRecorder | null>(null);
  const audioChunksRef = React.useRef<Blob[]>([]);
  const analyserRef = React.useRef<AnalyserNode | null>(null);
  const animationRef = React.useRef<number | null>(null);
  const timerRef = React.useRef<NodeJS.Timeout | null>(null);

  const transcribeAudio = useTranscribeAudio();
  const isProcessing = externalProcessing || transcribeAudio.isPending;

  // Handle recording complete - transcribe and call onResult
  const handleRecordingComplete = async (audioBlob: Blob) => {
    try {
      const result = await transcribeAudio.mutateAsync(audioBlob);
      if (result.text) {
        onResult(result.text);
      }
    } catch (err) {
      setError("Failed to transcribe audio. Please try again.");
    }
  };

  // Start recording
  const startRecording = async () => {
    try {
      setError(null);
      audioChunksRef.current = [];

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Set up audio analysis for visualization
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : "audio/mp4",
      });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType,
        });
        handleRecordingComplete(audioBlob);

        // Clean up
        stream.getTracks().forEach((track) => track.stop());
        audioContext.close();
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          if (prev >= 60) {
            stopRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);

      // Start audio level visualization
      updateAudioLevel();
    } catch (err) {
      console.error("Error starting recording:", err);
      setError("Could not access microphone. Please check permissions.");
    }
  };

  // Update audio level for visualization
  const updateAudioLevel = () => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
    setAudioLevel(average / 255);

    animationRef.current = requestAnimationFrame(updateAudioLevel);
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      // Clear timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      // Stop animation
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
    }
  };

  // Cancel recording
  const cancelRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stream
        .getTracks()
        .forEach((track) => track.stop());
    }
    setIsRecording(false);
    setRecordingTime(0);
    setAudioLevel(0);

    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    onClose();
  };

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Clean up on unmount
  React.useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, []);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && cancelRecording()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Voice Search</DialogTitle>
          <DialogDescription>
            {isRecording
              ? "Speak your search query..."
              : isProcessing
              ? "Processing your voice..."
              : "Click the microphone to start recording"}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col items-center gap-6 py-6">
          {/* Recording indicator */}
          <div className="relative">
            {/* Pulse animation when recording */}
            {isRecording && (
              <>
                <div
                  className="absolute inset-0 rounded-full bg-red-500 opacity-20"
                  style={{
                    transform: `scale(${1 + audioLevel * 0.5})`,
                    transition: "transform 100ms",
                  }}
                />
                <div
                  className="absolute inset-0 rounded-full bg-red-500 opacity-10"
                  style={{
                    transform: `scale(${1.2 + audioLevel * 0.3})`,
                    transition: "transform 100ms",
                  }}
                />
              </>
            )}

            {/* Main button */}
            <Button
              size="icon"
              variant={isRecording ? "destructive" : "default"}
              className={cn(
                "relative h-20 w-20 rounded-full transition-all",
                isRecording && "animate-pulse"
              )}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isProcessing}
              aria-label={isRecording ? "Stop recording" : "Start recording"}
            >
              {isProcessing ? (
                <Loader2 className="h-8 w-8 animate-spin" />
              ) : isRecording ? (
                <Square className="h-8 w-8" />
              ) : (
                <Mic className="h-8 w-8" />
              )}
            </Button>
          </div>

          {/* Timer */}
          {isRecording && (
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 animate-pulse rounded-full bg-red-500" />
              <span className="text-lg font-mono">
                {formatTime(recordingTime)}
              </span>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="flex items-center gap-2 text-destructive">
              <MicOff className="h-4 w-4" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {/* Instructions */}
          <p className="text-center text-sm text-muted-foreground">
            {isRecording
              ? "Tap the button to stop recording"
              : "Maximum recording time: 60 seconds"}
          </p>
        </div>

        {/* Cancel button */}
        <div className="flex justify-center">
          <Button
            variant="outline"
            onClick={cancelRecording}
            disabled={isProcessing}
          >
            Cancel
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
