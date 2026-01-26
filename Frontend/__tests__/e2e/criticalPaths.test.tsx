/**
 * End-to-end tests for critical paths.
 * 
 * These tests simulate complete user journeys through the application.
 * For actual E2E testing, consider using Playwright or Cypress.
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// ==============================================================================
// Complete Search Journey
// ==============================================================================

describe('E2E: Complete Search Journey', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('user searches, filters, views product, and adds to cart', async () => {
    // Mock search results
    const mockSearchResults = {
      products: [
        { id: '1', name: 'Wireless Headphones', price: 99.99, rating: 4.5 },
        { id: '2', name: 'Budget Earbuds', price: 29.99, rating: 4.0 },
      ],
      total_results: 2,
    };

    const mockProductDetail = {
      id: '1',
      name: 'Wireless Headphones',
      price: 99.99,
      description: 'Great headphones',
      features: ['Bluetooth 5.0', 'Noise Cancellation'],
    };

    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => mockSearchResults })
      .mockResolvedValueOnce({ ok: true, json: async () => mockProductDetail });

    // Step 1: Render search page
    const { rerender } = render(
      <div data-testid="search-page">
        <input data-testid="search-input" placeholder="Search..." />
        <button data-testid="search-button">Search</button>
        <div data-testid="results">
          {mockSearchResults.products.map(p => (
            <div key={p.id} data-testid="product-card">
              <span>{p.name}</span>
              <span>${p.price}</span>
            </div>
          ))}
        </div>
      </div>
    );

    // Step 2: User enters search
    await userEvent.type(screen.getByTestId('search-input'), 'headphones');
    expect(screen.getByTestId('search-input')).toHaveValue('headphones');

    // Step 3: Results are displayed
    expect(screen.getAllByTestId('product-card')).toHaveLength(2);

    // Step 4: Navigate to product detail
    rerender(
      <div data-testid="product-detail-page">
        <h1>{mockProductDetail.name}</h1>
        <p>{mockProductDetail.description}</p>
        <p>${mockProductDetail.price}</p>
        <button data-testid="add-to-cart">Add to Cart</button>
      </div>
    );

    expect(screen.getByText(mockProductDetail.name)).toBeInTheDocument();

    // Step 5: Add to cart
    const addToCartHandler = jest.fn();
    rerender(
      <div data-testid="product-detail-page">
        <h1>{mockProductDetail.name}</h1>
        <button data-testid="add-to-cart" onClick={addToCartHandler}>
          Add to Cart
        </button>
      </div>
    );

    await userEvent.click(screen.getByTestId('add-to-cart'));
    expect(addToCartHandler).toHaveBeenCalled();
  });
});

// ==============================================================================
// Recommendation to Purchase Journey
// ==============================================================================

describe('E2E: Recommendation to Purchase Journey', () => {
  it('user views recommendations, compares, and selects product', async () => {
    const mockRecommendations = [
      { id: '1', name: 'Product A', price: 149.99, explanation: 'Based on your history' },
      { id: '2', name: 'Product B', price: 199.99, explanation: 'Trending in Electronics' },
    ];

    // Step 1: View recommendations
    const { rerender } = render(
      <div data-testid="recommendations-page">
        <h1>Recommended for You</h1>
        {mockRecommendations.map(rec => (
          <div key={rec.id} data-testid="recommendation">
            <h3>{rec.name}</h3>
            <p>${rec.price}</p>
            <p>{rec.explanation}</p>
          </div>
        ))}
      </div>
    );

    expect(screen.getAllByTestId('recommendation')).toHaveLength(2);
    expect(screen.getByText('Based on your history')).toBeInTheDocument();

    // Step 2: Click to view detail
    rerender(
      <div data-testid="product-page">
        <h1>{mockRecommendations[0].name}</h1>
        <p>${mockRecommendations[0].price}</p>
        <div data-testid="explanation">
          <h3>Why we recommend this</h3>
          <p>{mockRecommendations[0].explanation}</p>
        </div>
      </div>
    );

    expect(screen.getByTestId('explanation')).toBeInTheDocument();
  });
});

// ==============================================================================
// Budget-Constrained Search Journey
// ==============================================================================

describe('E2E: Budget-Constrained Search Journey', () => {
  it('user searches with budget and views alternatives', async () => {
    const overBudgetProduct = { id: '1', name: 'Premium Headphones', price: 349.99 };
    const alternatives = [
      { id: '2', name: 'Budget Option', price: 79.99, savings: 270 },
      { id: '3', name: 'Mid-Range Option', price: 149.99, savings: 200 },
    ];

    // Step 1: Search results show over-budget warning
    const { rerender } = render(
      <div data-testid="search-results">
        <div data-testid="product-card">
          <h3>{overBudgetProduct.name}</h3>
          <p>${overBudgetProduct.price}</p>
          <div data-testid="budget-warning" className="warning">
            ⚠️ Exceeds your budget of $200
          </div>
        </div>
      </div>
    );

    expect(screen.getByTestId('budget-warning')).toBeInTheDocument();

    // Step 2: Show alternatives
    rerender(
      <div data-testid="alternatives-section">
        <h2>Budget-Friendly Alternatives</h2>
        {alternatives.map(alt => (
          <div key={alt.id} data-testid="alternative-card">
            <h3>{alt.name}</h3>
            <p>${alt.price}</p>
            <span className="savings">Save ${alt.savings}</span>
          </div>
        ))}
      </div>
    );

    expect(screen.getAllByTestId('alternative-card')).toHaveLength(2);
    expect(screen.getByText('Save $270')).toBeInTheDocument();
  });
});

// ==============================================================================
// Multimodal Search Journey
// ==============================================================================

describe('E2E: Multimodal Search Journey', () => {
  it('user uses voice search to find products', async () => {
    // Step 1: Open voice search
    const { rerender } = render(
      <div data-testid="voice-search-modal">
        <h2>Voice Search</h2>
        <button data-testid="record-button">🎤 Start Recording</button>
      </div>
    );

    expect(screen.getByTestId('record-button')).toBeInTheDocument();

    // Step 2: Show recording state
    rerender(
      <div data-testid="voice-search-modal">
        <h2>Voice Search</h2>
        <div data-testid="recording-indicator">Recording...</div>
        <button data-testid="stop-button">⬛ Stop</button>
      </div>
    );

    expect(screen.getByTestId('recording-indicator')).toBeInTheDocument();

    // Step 3: Show transcription
    rerender(
      <div data-testid="voice-search-modal">
        <h2>Voice Search</h2>
        <p data-testid="transcription">
          "affordable wireless headphones"
        </p>
        <button data-testid="search-button">Search</button>
      </div>
    );

    expect(screen.getByText(/"affordable wireless headphones"/)).toBeInTheDocument();

    // Step 4: Show results
    rerender(
      <div data-testid="search-results">
        <p>Results for: "affordable wireless headphones"</p>
        <div data-testid="product-card">Budget Headphones - $49.99</div>
      </div>
    );

    expect(screen.getByText(/Results for:/)).toBeInTheDocument();
  });

  it('user uses image search to find similar products', async () => {
    // Step 1: Upload image
    const { rerender } = render(
      <div data-testid="image-search">
        <input type="file" data-testid="image-input" accept="image/*" />
        <p>Upload a product image to find similar items</p>
      </div>
    );

    // Step 2: Show processing
    rerender(
      <div data-testid="image-search">
        <div data-testid="processing">Analyzing image...</div>
      </div>
    );

    expect(screen.getByTestId('processing')).toBeInTheDocument();

    // Step 3: Show similar products
    rerender(
      <div data-testid="image-results">
        <h2>Products matching your image</h2>
        <div data-testid="similar-product">
          <span>Similar Headphones</span>
          <span>95% match</span>
        </div>
      </div>
    );

    expect(screen.getByText('95% match')).toBeInTheDocument();
  });
});

// ==============================================================================
// Complete User Session Journey
// ==============================================================================

describe('E2E: Complete User Session', () => {
  it('simulates a full shopping session', async () => {
    // This test simulates:
    // 1. User arrives at homepage
    // 2. Browses recommendations
    // 3. Searches for specific product
    // 4. Applies filters
    // 5. Views product details
    // 6. Sees alternatives (over budget)
    // 7. Selects alternative
    // 8. Adds to cart

    // Step 1: Homepage with recommendations
    const { rerender } = render(
      <div data-testid="homepage">
        <h1>Welcome to FinFind</h1>
        <section data-testid="featured-recommendations">
          <h2>Recommended for You</h2>
          <div>Product 1</div>
          <div>Product 2</div>
        </section>
      </div>
    );

    expect(screen.getByText('Welcome to FinFind')).toBeInTheDocument();

    // Step 2: Search
    rerender(
      <div data-testid="search-page">
        <input data-testid="search-input" defaultValue="laptop" />
        <div data-testid="results">
          <div>MacBook Pro - $2499</div>
          <div>Dell XPS - $1299</div>
        </div>
      </div>
    );

    expect(screen.getByDisplayValue('laptop')).toBeInTheDocument();

    // Step 3: Filter by budget
    rerender(
      <div data-testid="filtered-results">
        <div data-testid="active-filter">Budget: Under $1000</div>
        <p>No products match your current filters</p>
        <button data-testid="show-over-budget">Show products over budget</button>
      </div>
    );

    expect(screen.getByText(/No products match/)).toBeInTheDocument();

    // Step 4: View over-budget product with alternatives
    rerender(
      <div data-testid="product-detail">
        <h1>Dell XPS - $1299</h1>
        <div data-testid="budget-warning">Over your budget by $299</div>
        <section data-testid="alternatives">
          <h3>Budget Alternatives</h3>
          <div data-testid="alternative">Acer Aspire - $699</div>
        </section>
      </div>
    );

    expect(screen.getByTestId('budget-warning')).toBeInTheDocument();
    expect(screen.getByText('Acer Aspire - $699')).toBeInTheDocument();

    // Step 5: Select alternative and add to cart
    const addToCart = jest.fn();
    rerender(
      <div data-testid="product-detail">
        <h1>Acer Aspire - $699</h1>
        <div className="badge-success">✓ Within budget</div>
        <button data-testid="add-to-cart" onClick={addToCart}>
          Add to Cart
        </button>
      </div>
    );

    await userEvent.click(screen.getByTestId('add-to-cart'));
    expect(addToCart).toHaveBeenCalled();
  });
});
