"""
Voice processor for speech-to-text conversion.

Supports multiple backends:
- Whisper local (via openai-whisper package)
- OpenAI Whisper API
- Groq Whisper API (fast inference)

Provides:
- Speech-to-text transcription
- Language detection
- Optional translation
- Audio preprocessing and validation
"""

import io
import base64
import hashlib
import logging
import tempfile
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
from functools import lru_cache
import numpy as np

from .config import VoiceConfig, VoiceBackend, get_multimodal_config
from .schemas import (
    VoiceTranscriptionResult,
    WordTimestamp,
    ProcessedAudio,
    MultimodalError,
    MultimodalErrorCode
)

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """
    Process voice input and convert to text.
    
    Supports multiple backends:
    - Whisper local: OpenAI's Whisper model running locally
    - OpenAI Whisper API: Cloud-based Whisper
    - Groq Whisper: Fast cloud inference
    """
    
    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or get_multimodal_config().voice
        self._model = None
        self._initialized = False
        self._transcription_cache: dict = {}
    
    def _initialize_whisper_local(self) -> None:
        """Initialize local Whisper model."""
        try:
            import whisper
            
            logger.info(f"Loading Whisper model: {self.config.whisper_model_size}")
            
            self._model = whisper.load_model(
                self.config.whisper_model_size,
                device=self.config.whisper_device
            )
            
            self._initialized = True
            logger.info("Whisper model initialized successfully")
            
        except ImportError as e:
            logger.error(f"whisper not installed: {e}")
            raise RuntimeError(
                "openai-whisper package required for local Whisper. "
                "Install with: pip install openai-whisper"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Whisper: {e}")
            raise
    
    def _initialize(self) -> None:
        """Initialize the appropriate backend."""
        if self._initialized:
            return
        
        if self.config.backend == VoiceBackend.WHISPER_LOCAL:
            self._initialize_whisper_local()
        elif self.config.backend in [VoiceBackend.WHISPER_API, VoiceBackend.GROQ_WHISPER]:
            # API backends don't need local initialization
            self._initialized = True
        else:
            raise ValueError(f"Unknown backend: {self.config.backend}")
    
    def _validate_audio(
        self,
        audio_data: bytes,
        audio_format: str
    ) -> Tuple[bool, Optional[str], Optional[ProcessedAudio]]:
        """Validate audio data."""
        try:
            # Check size
            if len(audio_data) > self.config.max_audio_size:
                return False, f"Audio too large: {len(audio_data)} bytes", None
            
            # Check format
            format_lower = audio_format.lower()
            if format_lower not in self.config.allowed_audio_formats:
                return False, f"Invalid format: {format_lower}", None
            
            # Try to get audio info
            try:
                import soundfile as sf
                
                with io.BytesIO(audio_data) as audio_io:
                    info = sf.info(audio_io)
                    duration = info.duration
                    sample_rate = info.samplerate
                    channels = info.channels
                    
            except ImportError:
                # soundfile not available, estimate duration
                # Rough estimate: assume 16-bit, mono, 16kHz
                duration = len(audio_data) / (16000 * 2)
                sample_rate = 16000
                channels = 1
            except Exception:
                # Can't read audio info, continue anyway
                duration = 0
                sample_rate = 16000
                channels = 1
            
            # Check duration
            if self.config.max_audio_duration > 0 and duration > self.config.max_audio_duration:
                return False, f"Audio too long: {duration:.1f}s (max: {self.config.max_audio_duration}s)", None
            
            processed = ProcessedAudio(
                duration_seconds=duration,
                sample_rate=sample_rate,
                channels=channels,
                format=format_lower,
                file_size_bytes=len(audio_data),
                is_valid=True
            )
            
            return True, None, processed
            
        except Exception as e:
            return False, f"Invalid audio: {str(e)}", None
    
    def _get_cache_key(self, audio_data: bytes, language: Optional[str]) -> str:
        """Generate cache key for audio data."""
        lang_str = language or "auto"
        content_hash = hashlib.sha256(audio_data).hexdigest()
        return f"{content_hash}_{lang_str}"
    
    def _transcribe_whisper_local(
        self,
        audio_path: str,
        language: Optional[str] = None,
        translate: bool = False
    ) -> Dict[str, Any]:
        """Transcribe using local Whisper model."""
        task = "translate" if translate else "transcribe"
        
        options = {
            "task": task,
            "language": language,
            "fp16": self.config.whisper_device == "cuda",
        }
        
        if self.config.enable_timestamps:
            options["word_timestamps"] = True
        
        result = self._model.transcribe(audio_path, **options)
        return result
    
    async def _transcribe_whisper_api(
        self,
        audio_data: bytes,
        audio_format: str,
        language: Optional[str] = None,
        translate: bool = False
    ) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper API."""
        import httpx
        
        if not self.config.whisper_api_key:
            raise RuntimeError("OpenAI API key not configured")
        
        endpoint = "translations" if translate else "transcriptions"
        
        files = {
            "file": (f"audio.{audio_format}", audio_data, f"audio/{audio_format}"),
            "model": (None, "whisper-1"),
        }
        
        if language and not translate:
            files["language"] = (None, language)
        
        if self.config.enable_timestamps:
            files["response_format"] = (None, "verbose_json")
            files["timestamp_granularities[]"] = (None, "word")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.openai.com/v1/audio/{endpoint}",
                headers={
                    "Authorization": f"Bearer {self.config.whisper_api_key}"
                },
                files=files,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
        
        return result
    
    async def _transcribe_groq_whisper(
        self,
        audio_data: bytes,
        audio_format: str,
        language: Optional[str] = None,
        translate: bool = False
    ) -> Dict[str, Any]:
        """Transcribe using Groq Whisper API."""
        import httpx
        
        if not self.config.groq_api_key:
            raise RuntimeError("Groq API key not configured")
        
        # Groq uses the same API format as OpenAI
        files = {
            "file": (f"audio.{audio_format}", audio_data, f"audio/{audio_format}"),
            "model": (None, "whisper-large-v3"),
        }
        
        if language:
            files["language"] = (None, language)
        
        if self.config.enable_timestamps:
            files["response_format"] = (None, "verbose_json")
        
        # Determine endpoint - Groq typically only supports transcription
        endpoint = "transcriptions"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.groq_api_base}/audio/{endpoint}",
                headers={
                    "Authorization": f"Bearer {self.config.groq_api_key}"
                },
                files=files,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
        
        return result
    
    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        language: Optional[str] = None,
        translate: bool = False,
        use_cache: bool = True
    ) -> VoiceTranscriptionResult:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (wav, mp3, etc.)
            language: Language code (e.g., 'en') or None for auto-detect
            translate: Whether to translate to English
            use_cache: Whether to use transcription cache
            
        Returns:
            VoiceTranscriptionResult with transcribed text
        """
        import time
        start_time = time.time()
        
        # Override with default language if not specified
        if language is None and self.config.default_language:
            language = self.config.default_language
        
        # Check cache
        cache_key = self._get_cache_key(audio_data, language)
        if use_cache and cache_key in self._transcription_cache:
            cached = self._transcription_cache[cache_key]
            logger.debug(f"Transcription cache hit: {cache_key[:16]}...")
            return cached
        
        # Validate audio
        is_valid, error_msg, audio_info = self._validate_audio(audio_data, audio_format)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Initialize backend
        self._initialize()
        
        # Transcribe based on backend
        word_timestamps = None
        detected_language = language or "en"
        original_text = None
        
        if self.config.backend == VoiceBackend.WHISPER_LOCAL:
            # Write to temp file for local Whisper
            with tempfile.NamedTemporaryFile(
                suffix=f".{audio_format}",
                delete=False
            ) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name
            
            try:
                result = self._transcribe_whisper_local(
                    tmp_path, language, translate
                )
                text = result["text"].strip()
                detected_language = result.get("language", language or "en")
                
                # Extract word timestamps if available
                if self.config.enable_timestamps and "segments" in result:
                    word_timestamps = []
                    for segment in result["segments"]:
                        if "words" in segment:
                            for word_info in segment["words"]:
                                word_timestamps.append(WordTimestamp(
                                    word=word_info["word"],
                                    start=word_info["start"],
                                    end=word_info["end"],
                                    confidence=word_info.get("probability")
                                ))
            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)
                
        elif self.config.backend == VoiceBackend.WHISPER_API:
            result = await self._transcribe_whisper_api(
                audio_data, audio_format, language, translate
            )
            
            if isinstance(result, dict):
                text = result.get("text", "").strip()
                detected_language = result.get("language", language or "en")
                
                if "words" in result:
                    word_timestamps = [
                        WordTimestamp(
                            word=w["word"],
                            start=w["start"],
                            end=w["end"]
                        )
                        for w in result["words"]
                    ]
            else:
                text = result.strip()
                
        elif self.config.backend == VoiceBackend.GROQ_WHISPER:
            result = await self._transcribe_groq_whisper(
                audio_data, audio_format, language, translate
            )
            
            if isinstance(result, dict):
                text = result.get("text", "").strip()
                detected_language = result.get("language", language or "en")
            else:
                text = result.strip()
        else:
            raise ValueError(f"Unsupported backend: {self.config.backend}")
        
        processing_time = (time.time() - start_time) * 1000
        
        # Handle translation
        was_translated = translate and detected_language != "en"
        if was_translated:
            original_text = text  # In a real scenario, we'd have the original
        
        result = VoiceTranscriptionResult(
            text=text,
            detected_language=detected_language,
            language_confidence=None,  # Would need model-specific extraction
            original_text=original_text,
            was_translated=was_translated,
            word_timestamps=word_timestamps,
            audio_duration_seconds=audio_info.duration_seconds if audio_info else 0,
            processing_time_ms=processing_time,
            model_used=self._get_model_name(),
            overall_confidence=None
        )
        
        # Cache result
        if use_cache:
            self._transcription_cache[cache_key] = result
        
        return result
    
    def _get_model_name(self) -> str:
        """Get the current model name."""
        if self.config.backend == VoiceBackend.WHISPER_LOCAL:
            return f"whisper-{self.config.whisper_model_size}"
        elif self.config.backend == VoiceBackend.WHISPER_API:
            return "whisper-1"
        elif self.config.backend == VoiceBackend.GROQ_WHISPER:
            return "whisper-large-v3"
        return "unknown"
    
    async def transcribe_from_base64(
        self,
        audio_base64: str,
        audio_format: str = "wav",
        language: Optional[str] = None,
        translate: bool = False,
        use_cache: bool = True
    ) -> VoiceTranscriptionResult:
        """Transcribe from base64-encoded audio."""
        try:
            audio_data = base64.b64decode(audio_base64)
        except Exception as e:
            raise ValueError(f"Invalid base64 audio data: {e}")
        
        return await self.transcribe(
            audio_data, audio_format, language, translate, use_cache
        )
    
    async def detect_language(
        self,
        audio_data: bytes,
        audio_format: str = "wav"
    ) -> Tuple[str, float]:
        """
        Detect the language of audio without full transcription.
        
        Returns:
            Tuple of (language_code, confidence)
        """
        # For now, do a full transcription and extract language
        result = await self.transcribe(
            audio_data, audio_format, language=None, use_cache=False
        )
        
        return result.detected_language, result.language_confidence or 0.0
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return self.config.supported_languages
    
    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported."""
        return language.lower() in [lang.lower() for lang in self.config.supported_languages]
    
    def clear_cache(self) -> int:
        """Clear the transcription cache."""
        count = len(self._transcription_cache)
        self._transcription_cache.clear()
        return count


# Singleton instance
_voice_processor: Optional[VoiceProcessor] = None


def get_voice_processor(config: Optional[VoiceConfig] = None) -> VoiceProcessor:
    """Get singleton voice processor instance."""
    global _voice_processor
    if _voice_processor is None:
        _voice_processor = VoiceProcessor(config)
    return _voice_processor
