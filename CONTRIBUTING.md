# Contributing to FinFind

Thank you for your interest in contributing to FinFind! This document provides guidelines and steps for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. We expect all contributors to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or hate speech
- Trolling or insulting comments
- Public or private harassment
- Publishing others' private information

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Git
- Docker (recommended)

### Setting Up Your Development Environment

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/finfind.git
   cd finfind
   ```

2. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/original/finfind.git
   ```

3. **Set up backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Set up frontend**
   ```bash
   cd ../Frontend
   npm install
   ```

5. **Copy environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your development API keys
   ```

## Development Process

### Branching Strategy

We use the following branch naming conventions:

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test additions/changes

### Creating a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-new-feature
```

### Making Changes

1. Make your changes in small, focused commits
2. Write meaningful commit messages
3. Add tests for new functionality
4. Update documentation as needed

### Commit Message Format

```
type(scope): Short description

Longer description if needed.

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```
feat(search): Add voice search support

Implement voice-to-text search using Web Speech API.
Includes fallback for unsupported browsers.

Fixes #45
```

## Pull Request Process

### Before Submitting

1. **Ensure tests pass**
   ```bash
   # Backend
   cd backend
   pytest tests/ -v
   
   # Frontend
   cd Frontend
   npm test
   ```

2. **Run linting**
   ```bash
   # Backend
   black . && flake8 .
   
   # Frontend
   npm run lint
   ```

3. **Update documentation** if needed

4. **Rebase on main**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

### Submitting a PR

1. Push your branch to your fork
   ```bash
   git push origin feature/my-new-feature
   ```

2. Open a Pull Request on GitHub

3. Fill out the PR template completely

4. Link any related issues

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe tests run

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where needed
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests
- [ ] All tests pass locally
```

### Review Process

1. A maintainer will review your PR
2. Address any requested changes
3. Once approved, a maintainer will merge your PR

## Coding Standards

### Python (Backend)

```python
# Use type hints
def process_query(query: str, limit: int = 10) -> List[Product]:
    pass

# Use async/await for I/O
async def fetch_data() -> Dict[str, Any]:
    pass

# Use descriptive names
user_financial_profile = get_user_profile(user_id)

# Document complex functions
def calculate_match_score(product: Product, user: User) -> float:
    """
    Calculate the match score between a product and user.
    
    Args:
        product: The product to evaluate
        user: The user's profile
    
    Returns:
        A score between 0 and 1 indicating match quality
    
    Raises:
        ValueError: If product or user is invalid
    """
    pass
```

### TypeScript (Frontend)

```typescript
// Use interfaces for props
interface ProductCardProps {
  product: Product;
  onSelect: (product: Product) => void;
}

// Use functional components
export function ProductCard({ product, onSelect }: ProductCardProps) {
  return (
    <div onClick={() => onSelect(product)}>
      {product.name}
    </div>
  );
}

// Use proper typing
const [products, setProducts] = useState<Product[]>([]);
```

### Formatting

- **Python**: Use `black` with default settings
- **TypeScript/JavaScript**: Use Prettier with project config
- **Line length**: 100 characters (Python), 80 characters (JS/TS)

## Testing Guidelines

### Backend Tests

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestSearchAgent:
    @pytest.fixture
    def agent(self):
        return SearchAgent(mock_client)
    
    @pytest.mark.asyncio
    async def test_process_returns_results(self, agent):
        """Test that process returns expected results."""
        result = await agent.process("test query")
        
        assert result is not None
        assert "products" in result
    
    @pytest.mark.asyncio
    async def test_handles_empty_query(self, agent):
        """Test that empty query raises error."""
        with pytest.raises(ValueError):
            await agent.process("")
```

### Frontend Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductCard } from './ProductCard';

describe('ProductCard', () => {
  const mockProduct = {
    id: '1',
    name: 'Test Product',
  };
  
  it('renders product name', () => {
    render(<ProductCard product={mockProduct} />);
    expect(screen.getByText('Test Product')).toBeInTheDocument();
  });
  
  it('calls onSelect when clicked', () => {
    const onSelect = jest.fn();
    render(<ProductCard product={mockProduct} onSelect={onSelect} />);
    
    fireEvent.click(screen.getByText('Test Product'));
    
    expect(onSelect).toHaveBeenCalledWith(mockProduct);
  });
});
```

### Test Coverage

- Aim for 80%+ code coverage
- Focus on critical paths and edge cases
- Write both unit and integration tests

## Documentation

### Code Documentation

- Add docstrings to all public functions/classes
- Use JSDoc for TypeScript/JavaScript
- Keep comments up to date with code changes

### README Updates

Update README.md when:
- Adding new features
- Changing setup process
- Modifying API endpoints
- Updating dependencies

### API Documentation

- Document all new endpoints
- Include request/response examples
- Note any breaking changes

## Questions?

- Open a GitHub issue
- Join our Discord community
- Email: contributors@finfind.com

Thank you for contributing to FinFind! 🎉
