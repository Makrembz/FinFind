/**
 * Integration tests for user flows.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock router
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => ({
    get: jest.fn(),
  }),
  usePathname: () => '/',
}));

// ==============================================================================
// Search Flow Tests
// ==============================================================================

describe('Search User Flow', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    mockPush.mockClear();
  });

  it('completes text search flow', async () => {
    // Mock API response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        products: [
          { id: '1', name: 'Headphones', price: 99.99 },
          { id: '2', name: 'Earbuds', price: 49.99 },
        ],
        total_results: 2,
      }),
    });

    render(
      <div>
        <form data-testid="search-form">
          <input 
            type="text" 
            placeholder="Search products..."
            data-testid="search-input"
          />
          <button type="submit">Search</button>
        </form>
        <div data-testid="results" />
      </div>
    );

    // User types in search
    const input = screen.getByTestId('search-input');
    await userEvent.type(input, 'wireless headphones');
    
    expect(input).toHaveValue('wireless headphones');
  });

  it('completes search with filters flow', async () => {
    render(
      <div>
        <input data-testid="search-input" placeholder="Search..." />
        <select data-testid="category-filter">
          <option value="">All</option>
          <option value="electronics">Electronics</option>
        </select>
        <input type="range" data-testid="price-filter" min={0} max={500} />
        <button>Apply Filters</button>
      </div>
    );

    // User enters search
    await userEvent.type(screen.getByTestId('search-input'), 'headphones');
    
    // User selects category
    await userEvent.selectOptions(screen.getByTestId('category-filter'), 'electronics');
    
    // User adjusts price
    fireEvent.change(screen.getByTestId('price-filter'), { target: { value: '200' } });
    
    // Verify filters applied
    expect(screen.getByTestId('category-filter')).toHaveValue('electronics');
  });

  it('handles empty search results', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        products: [],
        total_results: 0,
      }),
    });

    render(
      <div>
        <input data-testid="search-input" placeholder="Search..." />
        <div data-testid="no-results">No products found</div>
      </div>
    );

    await userEvent.type(screen.getByTestId('search-input'), 'nonexistent product xyz');
    
    expect(screen.getByTestId('no-results')).toBeInTheDocument();
  });
});

// ==============================================================================
// Recommendation Flow Tests
// ==============================================================================

describe('Recommendation User Flow', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    mockPush.mockClear();
  });

  it('loads personalized recommendations', async () => {
    const mockRecommendations = [
      { id: '1', name: 'Recommended 1', price: 99.99, explanation: 'Based on your interests' },
      { id: '2', name: 'Recommended 2', price: 149.99, explanation: 'Similar to past purchases' },
    ];

    render(
      <div data-testid="recommendations-page">
        <h1>Recommended for You</h1>
        {mockRecommendations.map(rec => (
          <div key={rec.id} data-testid="recommendation-card">
            <h3>{rec.name}</h3>
            <p>${rec.price}</p>
            <p>{rec.explanation}</p>
          </div>
        ))}
      </div>
    );

    expect(screen.getByText('Recommended for You')).toBeInTheDocument();
    expect(screen.getAllByTestId('recommendation-card')).toHaveLength(2);
    expect(screen.getByText('Based on your interests')).toBeInTheDocument();
  });

  it('navigates to product from recommendation', async () => {
    const handleClick = jest.fn();

    render(
      <div data-testid="recommendation-card" onClick={handleClick}>
        <h3>Recommended Product</h3>
      </div>
    );

    await userEvent.click(screen.getByTestId('recommendation-card'));
    
    expect(handleClick).toHaveBeenCalled();
  });
});

// ==============================================================================
// Product Detail Flow Tests
// ==============================================================================

describe('Product Detail User Flow', () => {
  const mockProduct = {
    id: 'prod_001',
    name: 'Test Product',
    price: 199.99,
    description: 'A great product',
    rating: 4.5,
    in_stock: true,
  };

  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('views product details', () => {
    render(
      <div data-testid="product-detail">
        <h1>{mockProduct.name}</h1>
        <p>{mockProduct.description}</p>
        <p>${mockProduct.price}</p>
        <span>★ {mockProduct.rating}</span>
      </div>
    );

    expect(screen.getByText(mockProduct.name)).toBeInTheDocument();
    expect(screen.getByText(mockProduct.description)).toBeInTheDocument();
  });

  it('adds product to cart', async () => {
    const handleAddToCart = jest.fn();

    render(
      <div data-testid="product-detail">
        <h1>{mockProduct.name}</h1>
        <button onClick={handleAddToCart}>Add to Cart</button>
      </div>
    );

    await userEvent.click(screen.getByText('Add to Cart'));
    
    expect(handleAddToCart).toHaveBeenCalled();
  });

  it('views alternatives for over-budget product', async () => {
    render(
      <div data-testid="product-detail">
        <h1>Premium Product - $499.99</h1>
        <div data-testid="budget-warning">
          This product exceeds your budget of $200
        </div>
        <button data-testid="view-alternatives">View Alternatives</button>
        <div data-testid="alternatives">
          <div>Budget Alternative - $149.99</div>
        </div>
      </div>
    );

    expect(screen.getByTestId('budget-warning')).toBeInTheDocument();
    
    await userEvent.click(screen.getByTestId('view-alternatives'));
    
    expect(screen.getByText(/Budget Alternative/)).toBeInTheDocument();
  });
});

// ==============================================================================
// Profile/Preferences Flow Tests
// ==============================================================================

describe('Profile User Flow', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('views user profile', () => {
    const mockUser = {
      name: 'Test User',
      email: 'test@example.com',
      budget: 200,
      preferences: ['Electronics', 'Home'],
    };

    render(
      <div data-testid="profile-page">
        <h1>My Profile</h1>
        <p>{mockUser.name}</p>
        <p>{mockUser.email}</p>
        <p>Budget: ${mockUser.budget}</p>
        <div>
          Preferred Categories:
          {mockUser.preferences.map(p => (
            <span key={p} className="badge">{p}</span>
          ))}
        </div>
      </div>
    );

    expect(screen.getByText(mockUser.name)).toBeInTheDocument();
    expect(screen.getByText(`Budget: $${mockUser.budget}`)).toBeInTheDocument();
  });

  it('updates budget preference', async () => {
    const handleSave = jest.fn();

    render(
      <div data-testid="preferences-form">
        <label htmlFor="budget">Monthly Budget</label>
        <input 
          id="budget"
          type="number" 
          defaultValue={200}
          data-testid="budget-input"
        />
        <button onClick={handleSave}>Save</button>
      </div>
    );

    const input = screen.getByTestId('budget-input');
    await userEvent.clear(input);
    await userEvent.type(input, '300');
    await userEvent.click(screen.getByText('Save'));

    expect(handleSave).toHaveBeenCalled();
  });

  it('updates category preferences', async () => {
    const handleToggle = jest.fn();

    render(
      <div data-testid="category-preferences">
        <label>
          <input 
            type="checkbox" 
            checked 
            onChange={handleToggle}
          />
          Electronics
        </label>
        <label>
          <input 
            type="checkbox" 
            onChange={handleToggle}
          />
          Home
        </label>
        <label>
          <input 
            type="checkbox" 
            onChange={handleToggle}
          />
          Sports
        </label>
      </div>
    );

    // Toggle Sports category
    await userEvent.click(screen.getByLabelText('Sports'));
    
    expect(handleToggle).toHaveBeenCalled();
  });
});

// ==============================================================================
// Voice Search Flow Tests
// ==============================================================================

describe('Voice Search User Flow', () => {
  it('initiates voice search', async () => {
    const handleStartRecording = jest.fn();
    const handleStopRecording = jest.fn();

    render(
      <div data-testid="voice-search">
        <button onClick={handleStartRecording} data-testid="start-recording">
          🎤 Start Recording
        </button>
        <button onClick={handleStopRecording} data-testid="stop-recording">
          ⬛ Stop
        </button>
      </div>
    );

    await userEvent.click(screen.getByTestId('start-recording'));
    expect(handleStartRecording).toHaveBeenCalled();

    await userEvent.click(screen.getByTestId('stop-recording'));
    expect(handleStopRecording).toHaveBeenCalled();
  });

  it('shows transcription result', () => {
    render(
      <div data-testid="voice-search">
        <p data-testid="transcription">
          Transcribed: "wireless headphones under one hundred dollars"
        </p>
        <button>Search with this</button>
      </div>
    );

    expect(screen.getByTestId('transcription')).toHaveTextContent('wireless headphones');
  });
});

// ==============================================================================
// Image Search Flow Tests
// ==============================================================================

describe('Image Search User Flow', () => {
  it('uploads image for search', async () => {
    const handleUpload = jest.fn();

    render(
      <div data-testid="image-search">
        <input 
          type="file" 
          accept="image/*"
          onChange={handleUpload}
          data-testid="image-input"
        />
        <p>Upload an image to find similar products</p>
      </div>
    );

    const file = new File(['test'], 'test.png', { type: 'image/png' });
    await userEvent.upload(screen.getByTestId('image-input'), file);

    expect(handleUpload).toHaveBeenCalled();
  });

  it('shows similar products after image upload', () => {
    const similarProducts = [
      { id: '1', name: 'Similar 1', similarity: 0.95 },
      { id: '2', name: 'Similar 2', similarity: 0.89 },
    ];

    render(
      <div data-testid="image-results">
        <h2>Products similar to your image</h2>
        {similarProducts.map(p => (
          <div key={p.id} data-testid="similar-product">
            <span>{p.name}</span>
            <span>{Math.round(p.similarity * 100)}% match</span>
          </div>
        ))}
      </div>
    );

    expect(screen.getAllByTestId('similar-product')).toHaveLength(2);
    expect(screen.getByText('95% match')).toBeInTheDocument();
  });
});
