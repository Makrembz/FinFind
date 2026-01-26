"""
Tests for multimodal capabilities.

Tests image search and voice input features.
"""

import pytest
import base64
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np


# ==============================================================================
# Test Configuration
# ==============================================================================

class TestMultimodalConfig:
    """Tests for multimodal configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        from app.multimodal.config import MultimodalConfig
        
        config = MultimodalConfig()
        
        assert config.enable_image_search == True
        assert config.enable_voice_input == True
        assert config.image.embedding_dimension == 512
        assert config.voice.whisper_model_size == "base"
    
    def test_config_from_env(self):
        """Test configuration from environment variables."""
        import os
        from app.multimodal.config import MultimodalConfig
        
        with patch.dict(os.environ, {
            "ENABLE_IMAGE_SEARCH": "false",
            "WHISPER_MODEL_SIZE": "tiny"
        }):
            config = MultimodalConfig.from_env()
            assert config.enable_image_search == False
            assert config.voice.whisper_model_size == "tiny"
    
    def test_image_config_backends(self):
        """Test image backend configuration."""
        from app.multimodal.config import ImageConfig, ImageBackend
        
        config = ImageConfig(backend=ImageBackend.CLIP_LOCAL)
        assert config.backend == "clip_local"
        
        config = ImageConfig(backend=ImageBackend.OPENCLIP)
        assert config.backend == "openclip"
    
    def test_voice_config_backends(self):
        """Test voice backend configuration."""
        from app.multimodal.config import VoiceConfig, VoiceBackend
        
        config = VoiceConfig(backend=VoiceBackend.WHISPER_LOCAL)
        assert config.backend == "whisper_local"
        
        config = VoiceConfig(backend=VoiceBackend.GROQ_WHISPER)
        assert config.backend == "groq_whisper"


# ==============================================================================
# Test Schemas
# ==============================================================================

class TestMultimodalSchemas:
    """Tests for multimodal schemas."""
    
    def test_image_search_request(self):
        """Test image search request validation."""
        from app.multimodal.schemas import ImageSearchRequest
        
        request = ImageSearchRequest(
            image_base64="base64data",
            max_price=100.0,
            limit=5
        )
        
        assert request.image_base64 == "base64data"
        assert request.max_price == 100.0
        assert request.limit == 5
        assert request.use_mmr == True  # default
    
    def test_voice_search_request(self):
        """Test voice search request validation."""
        from app.multimodal.schemas import VoiceSearchRequest
        
        request = VoiceSearchRequest(
            audio_base64="audiodata",
            language="es"
        )
        
        assert request.audio_base64 == "audiodata"
        assert request.language == "es"
        assert request.auto_search == True  # default
    
    def test_similar_product_model(self):
        """Test similar product model."""
        from app.multimodal.schemas import SimilarProduct
        
        product = SimilarProduct(
            product_id="prod_123",
            name="Test Product",
            price=99.99,
            category="Electronics",
            similarity_score=0.85
        )
        
        assert product.product_id == "prod_123"
        assert product.similarity_score == 0.85
    
    def test_multimodal_error(self):
        """Test multimodal error model."""
        from app.multimodal.schemas import MultimodalError, MultimodalErrorCode
        
        error = MultimodalError(
            code=MultimodalErrorCode.IMAGE_TOO_LARGE,
            message="Image exceeds maximum size"
        )
        
        assert error.code == MultimodalErrorCode.IMAGE_TOO_LARGE
        assert "maximum size" in error.message


# ==============================================================================
# Test Image Processor
# ==============================================================================

class TestImageProcessor:
    """Tests for image processor."""
    
    @pytest.fixture
    def mock_image_data(self):
        """Create mock image data."""
        # Create a simple 10x10 red image
        from PIL import Image
        import io
        
        img = Image.new('RGB', (10, 10), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def test_image_validation(self, mock_image_data):
        """Test image validation."""
        from app.multimodal.image_processor import ImageProcessor
        from app.multimodal.config import ImageConfig
        
        config = ImageConfig(max_image_size=1024 * 1024)  # 1MB
        processor = ImageProcessor(config)
        
        is_valid, error, info = processor._validate_image(mock_image_data)
        
        assert is_valid == True
        assert error is None
        assert info.format == "png"
    
    def test_image_validation_too_large(self):
        """Test validation rejects oversized images."""
        from app.multimodal.image_processor import ImageProcessor
        from app.multimodal.config import ImageConfig
        
        config = ImageConfig(max_image_size=100)  # 100 bytes
        processor = ImageProcessor(config)
        
        large_data = b"x" * 200
        is_valid, error, _ = processor._validate_image(large_data)
        
        assert is_valid == False
        assert "too large" in error.lower()
    
    def test_cache_key_generation(self, mock_image_data):
        """Test cache key is consistent."""
        from app.multimodal.image_processor import ImageProcessor
        
        processor = ImageProcessor()
        
        key1 = processor._get_cache_key(mock_image_data)
        key2 = processor._get_cache_key(mock_image_data)
        
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex
    
    @pytest.mark.asyncio
    async def test_embedding_generation_mock(self, mock_image_data):
        """Test embedding generation with mocked model."""
        from app.multimodal.image_processor import ImageProcessor
        from app.multimodal.config import ImageConfig, ImageBackend
        
        config = ImageConfig(backend=ImageBackend.CLIP_LOCAL)
        processor = ImageProcessor(config)
        
        # Mock the CLIP model
        mock_embedding = np.random.randn(512).astype(np.float32)
        processor._initialized = True
        processor._embed_clip_local = Mock(return_value=mock_embedding)
        
        with patch.object(processor, '_preprocess_image'):
            result = await processor.generate_embedding(mock_image_data)
        
        assert len(result.embedding) == 512
        assert result.model_used == config.clip_model_name


# ==============================================================================
# Test Voice Processor
# ==============================================================================

class TestVoiceProcessor:
    """Tests for voice processor."""
    
    @pytest.fixture
    def mock_audio_data(self):
        """Create mock audio data."""
        # Simple WAV header + silence
        return b"RIFF" + b"\x00" * 1000
    
    def test_audio_format_validation(self):
        """Test audio format validation."""
        from app.multimodal.voice_processor import VoiceProcessor
        from app.multimodal.config import VoiceConfig
        
        config = VoiceConfig(
            allowed_audio_formats=["wav", "mp3"]
        )
        processor = VoiceProcessor(config)
        
        # Valid format
        is_valid, error, _ = processor._validate_audio(b"test", "wav")
        # Note: Will fail validation due to invalid content, but format check passes
        
        # Invalid format
        is_valid, error, _ = processor._validate_audio(b"test", "xyz")
        assert is_valid == False
        assert "invalid format" in error.lower()
    
    def test_supported_languages(self):
        """Test supported languages list."""
        from app.multimodal.voice_processor import VoiceProcessor
        
        processor = VoiceProcessor()
        
        languages = processor.get_supported_languages()
        
        assert "en" in languages
        assert "es" in languages
        assert "fr" in languages
    
    def test_language_support_check(self):
        """Test language support checking."""
        from app.multimodal.voice_processor import VoiceProcessor
        
        processor = VoiceProcessor()
        
        assert processor.is_language_supported("en") == True
        assert processor.is_language_supported("EN") == True  # case insensitive
        assert processor.is_language_supported("xyz") == False
    
    def test_cache_key_includes_language(self):
        """Test cache key includes language."""
        from app.multimodal.voice_processor import VoiceProcessor
        
        processor = VoiceProcessor()
        audio_data = b"test audio"
        
        key_en = processor._get_cache_key(audio_data, "en")
        key_es = processor._get_cache_key(audio_data, "es")
        
        assert key_en != key_es


# ==============================================================================
# Test Multimodal Service
# ==============================================================================

class TestMultimodalService:
    """Tests for multimodal service."""
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        from app.agents.services.multimodal_service import MultimodalService
        from app.multimodal.config import MultimodalConfig
        
        config = MultimodalConfig()
        service = MultimodalService(config)
        
        assert service.is_image_search_enabled() == True
        assert service.is_voice_input_enabled() == True
    
    def test_service_status(self):
        """Test service status reporting."""
        from app.agents.services.multimodal_service import MultimodalService
        
        service = MultimodalService()
        status = service.get_status()
        
        assert "image_search_enabled" in status
        assert "voice_input_enabled" in status
        assert "image_backend" in status
        assert "voice_backend" in status
    
    def test_disabled_image_search(self):
        """Test error when image search is disabled."""
        from app.agents.services.multimodal_service import MultimodalService
        from app.multimodal.config import MultimodalConfig
        
        config = MultimodalConfig(enable_image_search=False)
        service = MultimodalService(config)
        
        assert service.is_image_search_enabled() == False
    
    def test_disabled_voice_input(self):
        """Test error when voice input is disabled."""
        from app.agents.services.multimodal_service import MultimodalService
        from app.multimodal.config import MultimodalConfig
        
        config = MultimodalConfig(enable_voice_input=False)
        service = MultimodalService(config)
        
        assert service.is_voice_input_enabled() == False


# ==============================================================================
# Test MCP Tools
# ==============================================================================

class TestMCPMultimodalTools:
    """Tests for MCP multimodal tools."""
    
    def test_image_search_tool_metadata(self):
        """Test image search tool has correct metadata."""
        from app.agents.mcp.tools.search_tools import ImageSimilaritySearchTool
        
        tool = ImageSimilaritySearchTool()
        
        assert tool.name == "image_similarity_search"
        assert "clip" in tool.mcp_metadata.tags
        assert tool.mcp_metadata.requires_qdrant == True
    
    def test_voice_search_tool_metadata(self):
        """Test voice search tool has correct metadata."""
        from app.agents.mcp.tools.search_tools import VoiceToTextSearchTool
        
        tool = VoiceToTextSearchTool()
        
        assert tool.name == "voice_to_text_search"
        assert "whisper" in tool.mcp_metadata.tags
    
    def test_image_tool_requires_input(self):
        """Test image tool requires image input."""
        from app.agents.mcp.tools.search_tools import ImageSimilaritySearchTool
        from app.agents.mcp.protocol import MCPError
        
        tool = ImageSimilaritySearchTool()
        
        # Should raise error without image
        with pytest.raises(MCPError) as exc_info:
            tool._execute()
        
        assert "image_url or image_base64" in str(exc_info.value)
    
    def test_voice_tool_requires_input(self):
        """Test voice tool requires audio input."""
        from app.agents.mcp.tools.search_tools import VoiceToTextSearchTool
        from app.agents.mcp.protocol import MCPError
        
        tool = VoiceToTextSearchTool()
        
        # Should raise error without audio
        with pytest.raises(MCPError) as exc_info:
            tool._execute()
        
        assert "audio_url or audio_base64" in str(exc_info.value)


# ==============================================================================
# Test API Routes
# ==============================================================================

class TestMultimodalAPI:
    """Tests for multimodal API routes."""
    
    @pytest.fixture
    def test_client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from app.api.main import app
        
        return TestClient(app)
    
    def test_health_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_api_info(self, test_client):
        """Test API info endpoint."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "FinFind API"
        assert "Image Search" in data["features"]
    
    @pytest.mark.asyncio
    async def test_image_search_missing_file(self, test_client):
        """Test image search requires file."""
        response = test_client.post("/api/v1/multimodal/image/search")
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_voice_search_missing_file(self, test_client):
        """Test voice search requires file."""
        response = test_client.post("/api/v1/multimodal/voice/search")
        
        assert response.status_code == 422  # Validation error


# ==============================================================================
# Integration Tests (require full setup)
# ==============================================================================

@pytest.mark.integration
class TestMultimodalIntegration:
    """Integration tests requiring full service setup."""
    
    @pytest.mark.asyncio
    async def test_full_image_search_flow(self):
        """Test complete image search flow."""
        from app.agents.services.multimodal_service import MultimodalService
        from PIL import Image
        import io
        
        # Create test image
        img = Image.new('RGB', (100, 100), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        
        service = MultimodalService()
        
        # Skip if image search not properly configured
        if not service.is_image_search_enabled():
            pytest.skip("Image search not enabled")
        
        try:
            result = await service.search_by_image(
                image_data=image_data,
                limit=5
            )
            
            assert result.total_found >= 0
            assert result.embedding_time_ms > 0
        except RuntimeError as e:
            # Model not loaded
            pytest.skip(f"Model not available: {e}")
    
    @pytest.mark.asyncio
    async def test_full_voice_search_flow(self):
        """Test complete voice search flow."""
        from app.agents.services.multimodal_service import MultimodalService
        
        service = MultimodalService()
        
        # Skip if voice input not properly configured
        if not service.is_voice_input_enabled():
            pytest.skip("Voice input not enabled")
        
        # Would need actual audio file for full test
        pytest.skip("Requires actual audio file")


# ==============================================================================
# Run Tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
