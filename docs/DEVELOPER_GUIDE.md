# 🛠️ FinFind Developer Guide

This guide covers everything you need to know to contribute to FinFind, add new features, and extend the platform.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Architecture](#project-architecture)
3. [Adding New Agents](#adding-new-agents)
4. [Creating MCP Tools](#creating-mcp-tools)
5. [Adding Product Categories](#adding-product-categories)
6. [Frontend Development](#frontend-development)
7. [Testing](#testing)
8. [Code Style & Standards](#code-style--standards)
9. [Debugging](#debugging)
10. [Common Patterns](#common-patterns)

---

## Development Setup

### Prerequisites

```bash
# Required
- Python 3.11+
- Node.js 20+
- Git

# Optional but recommended
- Docker & Docker Compose
- VS Code with recommended extensions
```

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/finfind.git
cd finfind

# Create environment file
cp .env.example .env
# Edit .env with your API keys

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../Frontend
npm install
```

### VS Code Extensions

Recommended extensions for development:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-azuretools.vscode-docker"
  ]
}
```

---

## Project Architecture

### Backend Structure

```
backend/
├── app/
│   ├── agents/                 # Multi-agent system
│   │   ├── base/              # Base classes and interfaces
│   │   │   ├── base_agent.py  # Abstract agent class
│   │   │   ├── agent_state.py # Agent state management
│   │   │   └── context.py     # Conversation context
│   │   ├── search_agent/      # Search agent implementation
│   │   ├── recommendation_agent/
│   │   ├── alternative_agent/
│   │   ├── explainability_agent/
│   │   ├── orchestrator/      # Agent coordination
│   │   │   ├── coordinator.py # Main orchestrator
│   │   │   ├── workflows.py   # Workflow definitions
│   │   │   └── a2a_protocol.py # Agent-to-agent communication
│   │   └── mcp/               # Model Context Protocol
│   │       ├── tools/         # Tool implementations
│   │       ├── registry.py    # Tool registry
│   │       └── protocol.py    # MCP protocol handler
│   ├── api/                   # FastAPI application
│   │   ├── routes/            # API route handlers
│   │   ├── services/          # Business logic services
│   │   └── models.py          # Pydantic models
│   ├── learning/              # Continuous learning system
│   └── multimodal/            # Voice/image processing
└── data_generation/           # Synthetic data generators
```

### Key Design Patterns

1. **Agent Pattern**: Each agent is a specialized processor with defined capabilities
2. **Tool Pattern**: Tools are atomic operations that agents can invoke
3. **Orchestrator Pattern**: Central coordinator manages agent collaboration
4. **Repository Pattern**: Data access abstracted through services

---

## Adding New Agents

### Step 1: Create Agent Directory

```bash
mkdir backend/app/agents/my_new_agent
touch backend/app/agents/my_new_agent/__init__.py
touch backend/app/agents/my_new_agent/agent.py
touch backend/app/agents/my_new_agent/prompts.py
```

### Step 2: Implement Agent Class

```python
# backend/app/agents/my_new_agent/agent.py

from typing import Dict, Any, List, Optional
from ..base.base_agent import BaseAgent
from ..base.context import ConversationContext
from .prompts import SYSTEM_PROMPT, RESPONSE_TEMPLATE

class MyNewAgent(BaseAgent):
    """Description of what this agent does."""
    
    def __init__(self, groq_client, tools: List[Any] = None):
        super().__init__(
            name="my_new_agent",
            description="Handles specific functionality...",
            groq_client=groq_client,
            tools=tools or []
        )
        self.system_prompt = SYSTEM_PROMPT
    
    async def process(
        self,
        query: str,
        context: Optional[ConversationContext] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Process a query and return results."""
        
        # 1. Prepare context
        prepared_context = self._prepare_context(query, context)
        
        # 2. Call LLM
        response = await self._call_llm(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prepared_context}
            ]
        )
        
        # 3. Parse and validate response
        result = self._parse_response(response)
        
        # 4. Execute any tool calls
        if result.get("tool_calls"):
            tool_results = await self._execute_tools(result["tool_calls"])
            result["tool_results"] = tool_results
        
        return result
    
    def _prepare_context(
        self,
        query: str,
        context: Optional[ConversationContext]
    ) -> str:
        """Prepare the context for LLM processing."""
        context_parts = [f"User Query: {query}"]
        
        if context:
            if context.user_profile:
                context_parts.append(f"User Profile: {context.user_profile}")
            if context.previous_results:
                context_parts.append(f"Previous Results: {context.previous_results}")
        
        return "\n\n".join(context_parts)
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured data."""
        # Implement parsing logic
        return {"response": response}
    
    def can_handle(self, query: str, context: Optional[Dict] = None) -> float:
        """Return confidence score (0-1) for handling this query."""
        # Implement query matching logic
        keywords = ["my", "keyword", "list"]
        score = sum(1 for kw in keywords if kw in query.lower()) / len(keywords)
        return min(score, 1.0)
```

### Step 3: Define Prompts

```python
# backend/app/agents/my_new_agent/prompts.py

SYSTEM_PROMPT = """You are a specialized financial advisor assistant focused on [SPECIFIC AREA].

Your responsibilities:
1. [Responsibility 1]
2. [Responsibility 2]
3. [Responsibility 3]

Guidelines:
- Always consider user's financial profile
- Provide clear, actionable advice
- Cite specific product features

Available Tools:
{tools}

Response Format:
{format}
"""

RESPONSE_TEMPLATE = """
Based on your query about {topic}:

{main_response}

Key Points:
{key_points}

Recommended Actions:
{actions}
"""
```

### Step 4: Register Agent

```python
# backend/app/agents/orchestrator/coordinator.py

from ..my_new_agent.agent import MyNewAgent

class AgentCoordinator:
    def __init__(self, ...):
        # ... existing agents ...
        self.my_new_agent = MyNewAgent(
            groq_client=self.groq_client,
            tools=self._get_my_new_agent_tools()
        )
        
        self.agents["my_new_agent"] = self.my_new_agent
```

### Step 5: Add API Endpoint (if needed)

```python
# backend/app/api/routes/my_new_agent.py

from fastapi import APIRouter, Depends
from ..dependencies import get_coordinator

router = APIRouter(prefix="/my-new-agent", tags=["my-new-agent"])

@router.post("/process")
async def process_query(
    request: MyNewAgentRequest,
    coordinator = Depends(get_coordinator)
):
    result = await coordinator.my_new_agent.process(
        query=request.query,
        context=request.context
    )
    return result
```

---

## Creating MCP Tools

### Step 1: Create Tool File

```python
# backend/app/agents/mcp/tools/my_tool.py

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from ..protocol import MCPTool, ToolResult

class MyToolInput(BaseModel):
    """Input schema for MyTool."""
    query: str = Field(..., description="The query to process")
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional processing options"
    )

class MyTool(MCPTool):
    """
    Tool Name: my_tool
    Description: Describe what this tool does
    
    Use this tool when:
    - Condition 1
    - Condition 2
    """
    
    name: str = "my_tool"
    description: str = "Describe what this tool does"
    input_schema: type = MyToolInput
    
    def __init__(self, dependencies: Dict[str, Any]):
        self.service = dependencies.get("my_service")
    
    async def execute(self, input_data: MyToolInput) -> ToolResult:
        """Execute the tool and return results."""
        try:
            # Perform the tool's operation
            result = await self.service.process(
                query=input_data.query,
                options=input_data.options
            )
            
            return ToolResult(
                success=True,
                data=result,
                metadata={"tool": self.name}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"tool": self.name}
            )
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input before execution."""
        try:
            MyToolInput(**input_data)
            return True
        except Exception:
            return False
```

### Step 2: Register Tool

```python
# backend/app/agents/mcp/registry.py

from .tools.my_tool import MyTool

class ToolRegistry:
    def __init__(self, dependencies: Dict[str, Any]):
        self._tools = {}
        self._register_default_tools(dependencies)
    
    def _register_default_tools(self, dependencies: Dict[str, Any]):
        # ... existing tools ...
        
        # Register new tool
        self.register(MyTool(dependencies))
    
    def register(self, tool: MCPTool):
        self._tools[tool.name] = tool
```

### Step 3: Use Tool in Agent

```python
# In your agent's process method
tool_calls = [
    {
        "tool": "my_tool",
        "input": {
            "query": "processed query",
            "options": {"option1": "value1"}
        }
    }
]

tool_results = await self._execute_tools(tool_calls)
```

---

## Adding Product Categories

### Step 1: Update Data Models

```python
# backend/data_generation/models/product_models.py

class ProductCategory(str, Enum):
    # Existing categories
    SAVINGS = "savings"
    INVESTMENTS = "investments"
    # Add new category
    MY_NEW_CATEGORY = "my_new_category"

class MyNewCategoryProduct(BaseProduct):
    """Product model for new category."""
    category: Literal["my_new_category"] = "my_new_category"
    
    # Category-specific fields
    specific_field_1: str
    specific_field_2: float
    features: List[str]
```

### Step 2: Create Generator

```python
# backend/data_generation/generators/my_category_generator.py

from .base_generator import BaseGenerator
from ..models.product_models import MyNewCategoryProduct

class MyNewCategoryGenerator(BaseGenerator):
    """Generator for new category products."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.templates = self._load_templates()
    
    def generate(self, count: int = 100) -> List[MyNewCategoryProduct]:
        """Generate synthetic products."""
        products = []
        
        for i in range(count):
            product = MyNewCategoryProduct(
                id=f"my_cat_{i:04d}",
                name=self._generate_name(),
                description=self._generate_description(),
                specific_field_1=self._generate_specific_field_1(),
                specific_field_2=self._generate_specific_field_2(),
                features=self._generate_features()
            )
            products.append(product)
        
        return products
```

### Step 3: Update Search Filters

```python
# backend/app/agents/mcp/tools/search_tools.py

class ApplyFinancialFilters(MCPTool):
    # Add category-specific filter logic
    
    async def execute(self, input_data: FilterInput) -> ToolResult:
        filters = []
        
        if input_data.category == "my_new_category":
            # Apply category-specific filters
            if input_data.specific_filter:
                filters.append(
                    FieldCondition(
                        key="specific_field_1",
                        match=MatchValue(value=input_data.specific_filter)
                    )
                )
        
        # ... rest of filter logic
```

### Step 4: Update Frontend

```typescript
// Frontend/src/types/index.ts

export type ProductCategory = 
  | 'savings'
  | 'investments'
  | 'my_new_category';  // Add new category

export interface MyNewCategoryProduct extends BaseProduct {
  category: 'my_new_category';
  specificField1: string;
  specificField2: number;
  features: string[];
}
```

---

## Frontend Development

### Component Structure

```typescript
// Frontend/src/components/feature/MyComponent.tsx

import { useState, useEffect } from 'react';
import { useApi } from '@/hooks/useApi';

interface MyComponentProps {
  productId: string;
  onSelect?: (product: Product) => void;
}

export function MyComponent({ productId, onSelect }: MyComponentProps) {
  const { data, loading, error } = useApi<Product>(
    `/products/${productId}`
  );
  
  if (loading) return <Skeleton />;
  if (error) return <ErrorDisplay error={error} />;
  if (!data) return null;
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{data.name}</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Component content */}
      </CardContent>
    </Card>
  );
}
```

### Custom Hooks

```typescript
// Frontend/src/hooks/useProduct.ts

import { useCallback, useState } from 'react';
import { api } from '@/lib/api';

export function useProduct(productId: string) {
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const fetchProduct = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getProduct(productId);
      setProduct(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [productId]);
  
  const updateProduct = useCallback(async (updates: Partial<Product>) => {
    // Update logic
  }, [productId]);
  
  return {
    product,
    loading,
    error,
    fetchProduct,
    updateProduct
  };
}
```

### API Integration

```typescript
// Frontend/src/lib/api.ts

class ApiClient {
  private baseUrl: string;
  
  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }
  
  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
    }
    
    return response.json();
  }
  
  // Add new API methods
  async getMyNewResource(id: string): Promise<MyResource> {
    return this.request<MyResource>(`/my-resource/${id}`);
  }
}

export const api = new ApiClient();
```

---

## Testing

### Backend Unit Tests

```python
# backend/tests/unit/test_my_agent.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.my_new_agent.agent import MyNewAgent

@pytest.fixture
def mock_groq_client():
    client = MagicMock()
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="test response"))]
        )
    )
    return client

@pytest.fixture
def agent(mock_groq_client):
    return MyNewAgent(groq_client=mock_groq_client)

class TestMyNewAgent:
    @pytest.mark.asyncio
    async def test_process_basic_query(self, agent):
        result = await agent.process("test query")
        
        assert result is not None
        assert "response" in result
    
    @pytest.mark.asyncio
    async def test_process_with_context(self, agent):
        context = ConversationContext(
            user_id="test_user",
            user_profile={"risk_tolerance": "low"}
        )
        
        result = await agent.process("test query", context=context)
        
        assert result is not None
    
    def test_can_handle_relevant_query(self, agent):
        score = agent.can_handle("my keyword query")
        
        assert score > 0.5
    
    def test_can_handle_irrelevant_query(self, agent):
        score = agent.can_handle("completely unrelated")
        
        assert score < 0.3
```

### Frontend Tests

```typescript
// Frontend/__tests__/components/MyComponent.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MyComponent } from '@/components/feature/MyComponent';

// Mock API
jest.mock('@/lib/api', () => ({
  api: {
    getProduct: jest.fn()
  }
}));

describe('MyComponent', () => {
  const mockProduct = {
    id: 'prod_001',
    name: 'Test Product',
    description: 'Test description'
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('renders product information', async () => {
    (api.getProduct as jest.Mock).mockResolvedValue(mockProduct);
    
    render(<MyComponent productId="prod_001" />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });
  });
  
  it('calls onSelect when clicked', async () => {
    const onSelect = jest.fn();
    (api.getProduct as jest.Mock).mockResolvedValue(mockProduct);
    
    render(<MyComponent productId="prod_001" onSelect={onSelect} />);
    
    await waitFor(() => {
      fireEvent.click(screen.getByRole('button'));
    });
    
    expect(onSelect).toHaveBeenCalledWith(mockProduct);
  });
  
  it('displays error state', async () => {
    (api.getProduct as jest.Mock).mockRejectedValue(new Error('API Error'));
    
    render(<MyComponent productId="prod_001" />);
    
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app --cov-report=html

# Frontend tests
cd Frontend
npm test                  # Run all tests
npm test -- --watch      # Watch mode
npm run test:coverage    # With coverage
```

---

## Code Style & Standards

### Python (Backend)

```python
# Use type hints
def process_query(query: str, limit: int = 10) -> List[Product]:
    ...

# Use async/await for I/O operations
async def fetch_products() -> List[Product]:
    ...

# Use Pydantic for data validation
class ProductRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[Dict[str, Any]] = None

# Use docstrings
def calculate_score(product: Product, user: User) -> float:
    """
    Calculate match score between product and user.
    
    Args:
        product: The product to score
        user: The user profile
    
    Returns:
        Score between 0 and 1
    """
    ...
```

### TypeScript (Frontend)

```typescript
// Use interfaces for props
interface ComponentProps {
  /** Product ID to display */
  productId: string;
  /** Callback when product is selected */
  onSelect?: (product: Product) => void;
}

// Use proper typing
const products: Product[] = [];
const handleClick = (id: string): void => { ... };

// Use functional components
export function MyComponent({ productId, onSelect }: ComponentProps) {
  ...
}

// Use custom hooks for logic
const { data, loading, error } = useProduct(productId);
```

### Commit Messages

```
feat: Add new recommendation algorithm
fix: Resolve search timeout issue
docs: Update API documentation
test: Add unit tests for search agent
refactor: Simplify agent orchestration
chore: Update dependencies
```

---

## Debugging

### Backend Debugging

```python
# Add logging
import logging
logger = logging.getLogger(__name__)

async def process(self, query: str) -> Dict:
    logger.debug(f"Processing query: {query}")
    logger.info(f"User context: {self.context}")
    
    try:
        result = await self._execute()
        logger.debug(f"Result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing: {e}", exc_info=True)
        raise

# Use debugger
import pdb; pdb.set_trace()  # Sync code
import asyncio; asyncio.get_event_loop().set_debug(True)  # Async debugging
```

### Frontend Debugging

```typescript
// React DevTools
// Install browser extension

// Console logging
console.log('State:', state);
console.table(products);

// Debug hooks
useEffect(() => {
  console.log('Effect triggered, deps:', { productId, filters });
}, [productId, filters]);

// Error boundaries
class ErrorBoundary extends React.Component {
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('Error:', error, info);
  }
}
```

### VS Code Launch Config

```json
// .vscode/launch.json
{
  "configurations": [
    {
      "name": "Backend: Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.api.main:app", "--reload", "--port", "8000"],
      "cwd": "${workspaceFolder}/backend"
    },
    {
      "name": "Frontend: Debug",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "cwd": "${workspaceFolder}/Frontend"
    }
  ]
}
```

---

## Common Patterns

### Async Context Manager

```python
class DatabaseSession:
    async def __aenter__(self):
        self.connection = await create_connection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.connection.close()

# Usage
async with DatabaseSession() as session:
    await session.query(...)
```

### Result Pattern

```python
@dataclass
class Result(Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None

def process() -> Result[Product]:
    try:
        product = fetch_product()
        return Result(success=True, data=product)
    except Exception as e:
        return Result(success=False, error=str(e))
```

### React Query Pattern

```typescript
function useProducts(filters: Filters) {
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => api.getProducts(filters),
    staleTime: 5 * 60 * 1000,  // 5 minutes
  });
}
```

---

## Next Steps

1. Read the [API Documentation](API.md)
2. Review existing agents for patterns
3. Check [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines
4. Join our Discord for questions

---

## Support

- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Real-time community support
- **Email**: dev-support@finfind.com
