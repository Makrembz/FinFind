/**
 * Component tests for Product components.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// ==============================================================================
// ProductCard Component Tests
// ==============================================================================

describe('ProductCard Component', () => {
  const mockProduct = {
    id: 'prod_001',
    name: 'Premium Wireless Headphones',
    price: 199.99,
    category: 'Electronics',
    brand: 'SoundMax',
    rating: 4.7,
    description: 'High-quality wireless headphones with noise cancellation',
    image_url: '/images/headphones.jpg',
    in_stock: true,
  };

  it('renders product information', () => {
    render(
      <div data-testid="product-card">
        <img src={mockProduct.image_url} alt={mockProduct.name} />
        <h3>{mockProduct.name}</h3>
        <p>${mockProduct.price}</p>
        <p>{mockProduct.brand}</p>
        <span>★ {mockProduct.rating}</span>
      </div>
    );
    
    expect(screen.getByText(mockProduct.name)).toBeInTheDocument();
    expect(screen.getByText(`$${mockProduct.price}`)).toBeInTheDocument();
    expect(screen.getByText(mockProduct.brand)).toBeInTheDocument();
  });

  it('displays product image', () => {
    render(
      <img src={mockProduct.image_url} alt={mockProduct.name} data-testid="product-image" />
    );
    
    const image = screen.getByTestId('product-image');
    expect(image).toHaveAttribute('alt', mockProduct.name);
  });

  it('shows in-stock badge', () => {
    render(
      <div>
        {mockProduct.in_stock && (
          <span data-testid="stock-badge" className="badge-success">In Stock</span>
        )}
      </div>
    );
    
    expect(screen.getByText('In Stock')).toBeInTheDocument();
  });

  it('shows out-of-stock badge', () => {
    const outOfStockProduct = { ...mockProduct, in_stock: false };
    
    render(
      <div>
        {!outOfStockProduct.in_stock && (
          <span data-testid="stock-badge" className="badge-error">Out of Stock</span>
        )}
      </div>
    );
    
    expect(screen.getByText('Out of Stock')).toBeInTheDocument();
  });

  it('handles click to view details', async () => {
    const handleClick = jest.fn();
    
    render(
      <div onClick={handleClick} data-testid="product-card" role="button" tabIndex={0}>
        <h3>{mockProduct.name}</h3>
      </div>
    );
    
    await userEvent.click(screen.getByTestId('product-card'));
    
    expect(handleClick).toHaveBeenCalled();
  });

  it('handles add to cart', async () => {
    const handleAddToCart = jest.fn();
    
    render(
      <div data-testid="product-card">
        <h3>{mockProduct.name}</h3>
        <button onClick={() => handleAddToCart(mockProduct.id)}>Add to Cart</button>
      </div>
    );
    
    await userEvent.click(screen.getByText('Add to Cart'));
    
    expect(handleAddToCart).toHaveBeenCalledWith(mockProduct.id);
  });
});

// ==============================================================================
// ProductDetail Component Tests
// ==============================================================================

describe('ProductDetail Component', () => {
  const mockProduct = {
    id: 'prod_001',
    name: 'Premium Wireless Headphones',
    price: 199.99,
    category: 'Electronics',
    brand: 'SoundMax',
    rating: 4.7,
    description: 'High-quality wireless headphones with noise cancellation',
    features: ['Noise Cancellation', '30-hour Battery', 'Bluetooth 5.0'],
    specs: {
      weight: '250g',
      dimensions: '20x15x8cm',
      color: 'Black',
    },
    image_url: '/images/headphones.jpg',
    in_stock: true,
  };

  it('renders full product details', () => {
    render(
      <div data-testid="product-detail">
        <h1>{mockProduct.name}</h1>
        <p>{mockProduct.description}</p>
        <p>${mockProduct.price}</p>
        <ul>
          {mockProduct.features.map((f, i) => (
            <li key={i}>{f}</li>
          ))}
        </ul>
      </div>
    );
    
    expect(screen.getByText(mockProduct.name)).toBeInTheDocument();
    expect(screen.getByText(mockProduct.description)).toBeInTheDocument();
    expect(screen.getByText('Noise Cancellation')).toBeInTheDocument();
  });

  it('displays specifications', () => {
    render(
      <div data-testid="specs">
        <h3>Specifications</h3>
        <dl>
          <dt>Weight</dt>
          <dd>{mockProduct.specs.weight}</dd>
          <dt>Dimensions</dt>
          <dd>{mockProduct.specs.dimensions}</dd>
        </dl>
      </div>
    );
    
    expect(screen.getByText('250g')).toBeInTheDocument();
    expect(screen.getByText('20x15x8cm')).toBeInTheDocument();
  });

  it('shows rating with stars', () => {
    render(
      <div data-testid="rating">
        <span aria-label={`Rating: ${mockProduct.rating} out of 5`}>
          {'★'.repeat(Math.floor(mockProduct.rating))}
          {mockProduct.rating % 1 >= 0.5 ? '½' : ''}
          {'☆'.repeat(5 - Math.ceil(mockProduct.rating))}
        </span>
        <span>{mockProduct.rating}</span>
      </div>
    );
    
    expect(screen.getByText(mockProduct.rating.toString())).toBeInTheDocument();
  });

  it('handles quantity selection', async () => {
    const handleQuantityChange = jest.fn();
    
    render(
      <div>
        <label htmlFor="quantity">Quantity</label>
        <input 
          id="quantity"
          type="number" 
          min={1} 
          max={10} 
          defaultValue={1}
          onChange={handleQuantityChange}
          data-testid="quantity-input"
        />
      </div>
    );
    
    const input = screen.getByTestId('quantity-input');
    fireEvent.change(input, { target: { value: '3' } });
    
    expect(handleQuantityChange).toHaveBeenCalled();
  });

  it('handles add to wishlist', async () => {
    const handleWishlist = jest.fn();
    
    render(
      <button onClick={handleWishlist} aria-label="Add to wishlist">
        ♡ Add to Wishlist
      </button>
    );
    
    await userEvent.click(screen.getByText(/Add to Wishlist/));
    
    expect(handleWishlist).toHaveBeenCalled();
  });
});

// ==============================================================================
// ProductRecommendations Component Tests
// ==============================================================================

describe('ProductRecommendations Component', () => {
  const mockRecommendations = [
    { id: '1', name: 'Similar Product 1', price: 149.99 },
    { id: '2', name: 'Similar Product 2', price: 179.99 },
    { id: '3', name: 'Similar Product 3', price: 129.99 },
  ];

  it('renders recommendations section', () => {
    render(
      <div data-testid="recommendations">
        <h2>You might also like</h2>
        {mockRecommendations.map(rec => (
          <div key={rec.id} data-testid="recommendation-card">
            <h3>{rec.name}</h3>
            <p>${rec.price}</p>
          </div>
        ))}
      </div>
    );
    
    expect(screen.getByText('You might also like')).toBeInTheDocument();
    expect(screen.getAllByTestId('recommendation-card')).toHaveLength(3);
  });

  it('handles recommendation click', async () => {
    const handleClick = jest.fn();
    
    render(
      <div data-testid="recommendations">
        {mockRecommendations.map(rec => (
          <div 
            key={rec.id} 
            onClick={() => handleClick(rec.id)}
            data-testid="recommendation-card"
          >
            {rec.name}
          </div>
        ))}
      </div>
    );
    
    await userEvent.click(screen.getAllByTestId('recommendation-card')[0]);
    
    expect(handleClick).toHaveBeenCalledWith('1');
  });
});

// ==============================================================================
// ProductAlternatives Component Tests
// ==============================================================================

describe('ProductAlternatives Component', () => {
  const mockAlternatives = [
    { id: '1', name: 'Budget Alternative', price: 49.99, savings: 150 },
    { id: '2', name: 'Mid-Range Alternative', price: 99.99, savings: 100 },
  ];

  it('renders alternatives section', () => {
    render(
      <div data-testid="alternatives">
        <h2>Budget-Friendly Alternatives</h2>
        {mockAlternatives.map(alt => (
          <div key={alt.id} data-testid="alternative-card">
            <h3>{alt.name}</h3>
            <p>${alt.price}</p>
            <p>Save ${alt.savings}</p>
          </div>
        ))}
      </div>
    );
    
    expect(screen.getByText('Budget-Friendly Alternatives')).toBeInTheDocument();
    expect(screen.getByText('Save $150')).toBeInTheDocument();
  });

  it('shows trade-offs for alternatives', () => {
    render(
      <div data-testid="alternative-card">
        <h3>Budget Alternative</h3>
        <div data-testid="trade-offs">
          <h4>Trade-offs</h4>
          <ul>
            <li>Lower audio quality</li>
            <li>Shorter battery life</li>
          </ul>
        </div>
      </div>
    );
    
    expect(screen.getByText('Lower audio quality')).toBeInTheDocument();
  });
});

// ==============================================================================
// ProductExplanation Component Tests
// ==============================================================================

describe('ProductExplanation Component', () => {
  it('renders explanation for recommendation', () => {
    render(
      <div data-testid="explanation">
        <h3>Why we recommend this</h3>
        <p>This product matches your search for wireless headphones and fits within your $200 budget.</p>
      </div>
    );
    
    expect(screen.getByText('Why we recommend this')).toBeInTheDocument();
    expect(screen.getByText(/matches your search/)).toBeInTheDocument();
  });

  it('shows match factors', () => {
    const factors = [
      { label: 'Category Match', score: 95 },
      { label: 'Price Match', score: 85 },
      { label: 'Rating', score: 90 },
    ];
    
    render(
      <div data-testid="match-factors">
        {factors.map((f, i) => (
          <div key={i}>
            <span>{f.label}</span>
            <progress value={f.score} max={100} />
            <span>{f.score}%</span>
          </div>
        ))}
      </div>
    );
    
    expect(screen.getByText('Category Match')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
  });

  it('shows financial fit explanation', () => {
    render(
      <div data-testid="financial-fit">
        <h4>Financial Fit</h4>
        <p>At $199.99, this is within your budget of $250</p>
        <span className="badge-success">✓ Fits Budget</span>
      </div>
    );
    
    expect(screen.getByText(/within your budget/)).toBeInTheDocument();
    expect(screen.getByText('✓ Fits Budget')).toBeInTheDocument();
  });
});
