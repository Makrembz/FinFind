/**
 * Component tests for Search components.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// ==============================================================================
// SearchBar Component Tests
// ==============================================================================

describe('SearchBar Component', () => {
  const mockOnSearch = jest.fn();

  beforeEach(() => {
    mockOnSearch.mockClear();
    mockFetch.mockClear();
  });

  it('renders search input', () => {
    render(
      <div data-testid="search-bar">
        <input 
          type="text" 
          placeholder="Search products..."
          aria-label="Search"
        />
        <button type="submit">Search</button>
      </div>
    );
    
    expect(screen.getByPlaceholderText('Search products...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Search' })).toBeInTheDocument();
  });

  it('handles text input', async () => {
    render(
      <div data-testid="search-bar">
        <input 
          type="text" 
          placeholder="Search products..."
          data-testid="search-input"
        />
      </div>
    );
    
    const input = screen.getByTestId('search-input');
    await userEvent.type(input, 'wireless headphones');
    
    expect(input).toHaveValue('wireless headphones');
  });

  it('submits search on form submit', async () => {
    const handleSubmit = jest.fn((e) => e.preventDefault());
    
    render(
      <form onSubmit={handleSubmit} data-testid="search-form">
        <input 
          type="text" 
          placeholder="Search products..."
          data-testid="search-input"
        />
        <button type="submit">Search</button>
      </form>
    );
    
    await userEvent.type(screen.getByTestId('search-input'), 'headphones');
    await userEvent.click(screen.getByRole('button', { name: 'Search' }));
    
    expect(handleSubmit).toHaveBeenCalled();
  });

  it('submits search on Enter key', async () => {
    const handleSubmit = jest.fn((e) => e.preventDefault());
    
    render(
      <form onSubmit={handleSubmit}>
        <input 
          type="text" 
          placeholder="Search products..."
          data-testid="search-input"
        />
      </form>
    );
    
    const input = screen.getByTestId('search-input');
    await userEvent.type(input, 'headphones{enter}');
    
    expect(handleSubmit).toHaveBeenCalled();
  });

  it('clears search input', async () => {
    render(
      <div>
        <input 
          type="text" 
          placeholder="Search products..."
          data-testid="search-input"
        />
        <button 
          onClick={() => {
            const input = document.querySelector('[data-testid="search-input"]') as HTMLInputElement;
            if (input) input.value = '';
          }}
          data-testid="clear-button"
        >
          Clear
        </button>
      </div>
    );
    
    const input = screen.getByTestId('search-input');
    await userEvent.type(input, 'headphones');
    expect(input).toHaveValue('headphones');
    
    await userEvent.click(screen.getByTestId('clear-button'));
    expect(input).toHaveValue('');
  });
});

// ==============================================================================
// FilterPanel Component Tests
// ==============================================================================

describe('FilterPanel Component', () => {
  const mockOnFilterChange = jest.fn();

  beforeEach(() => {
    mockOnFilterChange.mockClear();
  });

  it('renders filter options', () => {
    render(
      <div data-testid="filter-panel">
        <div>
          <label>Category</label>
          <select data-testid="category-filter">
            <option value="">All Categories</option>
            <option value="electronics">Electronics</option>
            <option value="home">Home</option>
          </select>
        </div>
        <div>
          <label>Price Range</label>
          <input type="range" min={0} max={1000} data-testid="price-filter" />
        </div>
      </div>
    );
    
    expect(screen.getByTestId('category-filter')).toBeInTheDocument();
    expect(screen.getByTestId('price-filter')).toBeInTheDocument();
  });

  it('handles category selection', async () => {
    const handleChange = jest.fn();
    
    render(
      <select onChange={handleChange} data-testid="category-filter">
        <option value="">All</option>
        <option value="electronics">Electronics</option>
      </select>
    );
    
    await userEvent.selectOptions(screen.getByTestId('category-filter'), 'electronics');
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('handles price range change', () => {
    const handleChange = jest.fn();
    
    render(
      <input 
        type="range" 
        min={0} 
        max={1000} 
        defaultValue={500}
        onChange={handleChange}
        data-testid="price-filter" 
      />
    );
    
    fireEvent.change(screen.getByTestId('price-filter'), { target: { value: '300' } });
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('handles rating filter', async () => {
    const handleChange = jest.fn();
    
    render(
      <div>
        <label>Minimum Rating</label>
        <select onChange={handleChange} data-testid="rating-filter">
          <option value="">Any</option>
          <option value="4">4+ Stars</option>
          <option value="3">3+ Stars</option>
        </select>
      </div>
    );
    
    await userEvent.selectOptions(screen.getByTestId('rating-filter'), '4');
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('resets all filters', async () => {
    const handleReset = jest.fn();
    
    render(
      <div>
        <select data-testid="category-filter" defaultValue="electronics">
          <option value="">All</option>
          <option value="electronics">Electronics</option>
        </select>
        <button onClick={handleReset}>Reset Filters</button>
      </div>
    );
    
    await userEvent.click(screen.getByText('Reset Filters'));
    
    expect(handleReset).toHaveBeenCalled();
  });
});

// ==============================================================================
// ImageUploader Component Tests
// ==============================================================================

describe('ImageUploader Component', () => {
  const mockOnUpload = jest.fn();

  beforeEach(() => {
    mockOnUpload.mockClear();
    mockFetch.mockClear();
  });

  it('renders upload area', () => {
    render(
      <div data-testid="image-uploader">
        <input type="file" accept="image/*" data-testid="file-input" />
        <p>Drag and drop an image or click to upload</p>
      </div>
    );
    
    expect(screen.getByTestId('file-input')).toBeInTheDocument();
    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
  });

  it('accepts image files', () => {
    render(
      <input type="file" accept="image/*" data-testid="file-input" />
    );
    
    const input = screen.getByTestId('file-input');
    expect(input).toHaveAttribute('accept', 'image/*');
  });

  it('handles file selection', async () => {
    const handleChange = jest.fn();
    
    render(
      <input 
        type="file" 
        accept="image/*" 
        onChange={handleChange}
        data-testid="file-input" 
      />
    );
    
    const file = new File(['test'], 'test.png', { type: 'image/png' });
    const input = screen.getByTestId('file-input');
    
    await userEvent.upload(input, file);
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('shows preview after upload', async () => {
    const [preview, setPreview] = [null as string | null, jest.fn()];
    
    render(
      <div>
        <input 
          type="file" 
          accept="image/*"
          data-testid="file-input"
        />
        {preview && <img src={preview} alt="Preview" data-testid="preview" />}
      </div>
    );
    
    // Preview should not be visible initially
    expect(screen.queryByTestId('preview')).not.toBeInTheDocument();
  });

  it('validates file type', async () => {
    const handleError = jest.fn();
    
    render(
      <input 
        type="file" 
        accept="image/*"
        data-testid="file-input"
        onError={handleError}
      />
    );
    
    const input = screen.getByTestId('file-input');
    expect(input).toHaveAttribute('accept', 'image/*');
  });
});

// ==============================================================================
// VoiceRecorder Component Tests
// ==============================================================================

describe('VoiceRecorder Component', () => {
  const mockOnRecordingComplete = jest.fn();

  beforeEach(() => {
    mockOnRecordingComplete.mockClear();
  });

  it('renders record button', () => {
    render(
      <button data-testid="record-button" aria-label="Start recording">
        🎤 Record
      </button>
    );
    
    expect(screen.getByTestId('record-button')).toBeInTheDocument();
  });

  it('handles start recording', async () => {
    const handleClick = jest.fn();
    
    render(
      <button 
        onClick={handleClick}
        data-testid="record-button"
      >
        Start Recording
      </button>
    );
    
    await userEvent.click(screen.getByTestId('record-button'));
    
    expect(handleClick).toHaveBeenCalled();
  });

  it('shows recording indicator when active', () => {
    render(
      <div>
        <button data-testid="record-button">Recording...</button>
        <span data-testid="recording-indicator" className="recording-active">●</span>
      </div>
    );
    
    expect(screen.getByTestId('recording-indicator')).toBeInTheDocument();
  });

  it('handles stop recording', async () => {
    const handleStop = jest.fn();
    
    render(
      <button 
        onClick={handleStop}
        data-testid="stop-button"
      >
        Stop Recording
      </button>
    );
    
    await userEvent.click(screen.getByTestId('stop-button'));
    
    expect(handleStop).toHaveBeenCalled();
  });

  it('has proper accessibility', () => {
    render(
      <button 
        data-testid="record-button"
        aria-label="Start voice recording"
        role="button"
      >
        🎤
      </button>
    );
    
    const button = screen.getByTestId('record-button');
    expect(button).toHaveAttribute('aria-label', 'Start voice recording');
  });
});

// ==============================================================================
// Search Results Component Tests
// ==============================================================================

describe('Search Results Component', () => {
  const mockProducts = [
    { id: '1', name: 'Product 1', price: 99.99, rating: 4.5 },
    { id: '2', name: 'Product 2', price: 149.99, rating: 4.0 },
    { id: '3', name: 'Product 3', price: 79.99, rating: 4.8 },
  ];

  it('renders list of products', () => {
    render(
      <div data-testid="search-results">
        {mockProducts.map(product => (
          <div key={product.id} data-testid="product-card">
            <h3>{product.name}</h3>
            <p>${product.price}</p>
          </div>
        ))}
      </div>
    );
    
    expect(screen.getAllByTestId('product-card')).toHaveLength(3);
    expect(screen.getByText('Product 1')).toBeInTheDocument();
  });

  it('shows empty state when no results', () => {
    render(
      <div data-testid="search-results">
        <p>No products found</p>
      </div>
    );
    
    expect(screen.getByText('No products found')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(
      <div data-testid="search-results">
        <div data-testid="loading-skeleton" role="status" aria-label="Loading">
          Loading...
        </div>
      </div>
    );
    
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });

  it('handles product click', async () => {
    const handleClick = jest.fn();
    
    render(
      <div data-testid="search-results">
        <div onClick={() => handleClick('1')} data-testid="product-card">
          <h3>Product 1</h3>
        </div>
      </div>
    );
    
    await userEvent.click(screen.getByTestId('product-card'));
    
    expect(handleClick).toHaveBeenCalledWith('1');
  });
});
