"""
Tests for Workflow API Routes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator."""
    orchestrator = MagicMock()
    orchestrator._initialized = True
    orchestrator._workflow_executor = MagicMock()
    
    # Mock execute_workflow
    async def mock_execute_workflow(*args, **kwargs):
        return {
            "success": True,
            "workflow_id": kwargs.get("workflow_id", "search_recommend"),
            "execution_id": "exec-123",
            "output": "Found products for you",
            "products": [
                {"id": "prod-1", "name": "Test Product", "price": 99.99}
            ],
            "explanations": {},
            "alternatives": [],
            "agents_used": ["SearchAgent", "RecommendationAgent"],
            "execution_time_ms": 1500.0,
            "errors": [],
            "warnings": []
        }
    
    orchestrator.execute_workflow = AsyncMock(side_effect=mock_execute_workflow)
    
    # Mock convenience methods
    orchestrator.search_and_personalize = AsyncMock(side_effect=mock_execute_workflow)
    orchestrator.recommend_with_explanation = AsyncMock(side_effect=mock_execute_workflow)
    orchestrator.search_with_budget_fallback = AsyncMock(side_effect=mock_execute_workflow)
    orchestrator.full_discovery_pipeline = AsyncMock(side_effect=mock_execute_workflow)
    
    # Mock get_status
    orchestrator.get_status.return_value = {
        "initialized": True,
        "agents": {"SearchAgent": {}, "RecommendationAgent": {}},
        "available_workflows": ["search_recommend", "recommend_explain"],
        "active_workflow_executions": 0,
        "pending_tasks": 0
    }
    
    return orchestrator


@pytest.fixture
def client(mock_orchestrator):
    """Create test client with mocked dependencies."""
    from backend.app.api.main import create_app
    from backend.app.api.dependencies import get_orchestrator
    
    app = create_app()
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    
    return TestClient(app)


class TestWorkflowList:
    """Tests for listing workflows."""
    
    def test_list_workflows_success(self, client):
        """Test listing available workflows."""
        response = client.get("/api/v1/workflows/")
        
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert len(data["workflows"]) >= 4  # At least 4 predefined workflows
    
    def test_list_workflows_structure(self, client):
        """Test workflow list structure."""
        response = client.get("/api/v1/workflows/")
        
        data = response.json()
        for workflow in data["workflows"]:
            assert "id" in workflow
            assert "name" in workflow
            assert "description" in workflow
            assert "type" in workflow
            assert "steps" in workflow


class TestWorkflowExecution:
    """Tests for workflow execution."""
    
    def test_execute_workflow_success(self, client, mock_orchestrator):
        """Test executing a predefined workflow."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "workflow_id": "search_recommend",
                "query": "savings account",
                "user_id": "user-123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["workflow_id"] == "search_recommend"
        assert "execution_id" in data
        assert "products" in data
    
    def test_execute_workflow_with_budget(self, client, mock_orchestrator):
        """Test workflow with budget constraint."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "workflow_id": "search_alternative",
                "query": "credit card",
                "budget_max": 500.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_execute_invalid_workflow(self, client, mock_orchestrator):
        """Test executing non-existent workflow."""
        mock_orchestrator.execute_workflow = AsyncMock(
            side_effect=ValueError("Unknown workflow: invalid")
        )
        
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "workflow_id": "invalid",
                "query": "test query"
            }
        )
        
        assert response.status_code == 400
    
    def test_execute_workflow_missing_query(self, client):
        """Test workflow without query."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "workflow_id": "search_recommend"
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestCustomWorkflow:
    """Tests for custom workflow execution."""
    
    def test_execute_custom_workflow_success(self, client, mock_orchestrator):
        """Test executing a custom workflow."""
        # Mock custom workflow execution
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.workflow_id = "custom"
        mock_result.execution_id = "exec-custom-123"
        mock_result.output = "Custom workflow complete"
        mock_result.products = []
        mock_result.explanations = {}
        mock_result.alternatives = []
        mock_result.agents_used = ["SearchAgent"]
        mock_result.execution_time_ms = 1000.0
        mock_result.errors = []
        mock_result.warnings = []
        
        mock_orchestrator._workflow_executor.execute_custom_workflow = AsyncMock(
            return_value=mock_result
        )
        
        response = client.post(
            "/api/v1/workflows/execute/custom",
            json={
                "steps": [
                    {
                        "name": "Search products",
                        "agent": "SearchAgent",
                        "task": "Find products matching query"
                    }
                ],
                "query": "test query"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_custom_workflow_invalid_agent(self, client):
        """Test custom workflow with invalid agent."""
        response = client.post(
            "/api/v1/workflows/execute/custom",
            json={
                "steps": [
                    {
                        "name": "Test step",
                        "agent": "InvalidAgent",
                        "task": "Do something"
                    }
                ],
                "query": "test"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid agent" in response.json()["detail"]


class TestConvenienceEndpoints:
    """Tests for convenience workflow endpoints."""
    
    def test_search_and_personalize(self, client, mock_orchestrator):
        """Test search and personalize endpoint."""
        response = client.post(
            "/api/v1/workflows/search-and-personalize",
            params={
                "query": "savings account",
                "user_id": "user-123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["workflow_id"] == "search_recommend"
    
    def test_recommend_with_explanation(self, client, mock_orchestrator):
        """Test recommend with explanation endpoint."""
        response = client.post(
            "/api/v1/workflows/recommend-with-explanation",
            params={
                "user_id": "user-123",
                "query": "investment"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["workflow_id"] == "recommend_explain"
    
    def test_search_with_budget_fallback(self, client, mock_orchestrator):
        """Test search with budget fallback endpoint."""
        response = client.post(
            "/api/v1/workflows/search-with-fallback",
            params={
                "query": "premium card",
                "budget_max": 200.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["workflow_id"] == "search_alternative"
    
    def test_full_discovery_pipeline(self, client, mock_orchestrator):
        """Test full discovery pipeline endpoint."""
        response = client.post(
            "/api/v1/workflows/full-discovery",
            params={
                "query": "financial products",
                "user_id": "user-123",
                "budget_max": 1000.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["workflow_id"] == "full_pipeline"


class TestWorkflowStatus:
    """Tests for workflow status endpoint."""
    
    def test_get_workflow_status(self, client, mock_orchestrator):
        """Test getting workflow system status."""
        response = client.get("/api/v1/workflows/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "initialized" in data
        assert "agents" in data
        assert "available_workflows" in data


# Integration tests (would need real infrastructure)
class TestWorkflowIntegration:
    """Integration tests for workflow system."""
    
    @pytest.mark.skip(reason="Requires real infrastructure")
    def test_real_search_recommend_workflow(self):
        """Test real search and recommend workflow."""
        pass
    
    @pytest.mark.skip(reason="Requires real infrastructure")
    def test_real_full_pipeline(self):
        """Test real full pipeline execution."""
        pass
