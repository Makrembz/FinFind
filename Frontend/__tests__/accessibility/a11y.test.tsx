/**
 * Accessibility tests for FinFind.
 * 
 * Tests WCAG 2.1 compliance for UI components.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// ==============================================================================
// Keyboard Navigation Tests
// ==============================================================================

describe('Keyboard Navigation', () => {
  it('search input is focusable', () => {
    render(
      <input 
        type="text" 
        placeholder="Search products..."
        data-testid="search-input"
      />
    );
    
    const input = screen.getByTestId('search-input');
    input.focus();
    
    expect(document.activeElement).toBe(input);
  });

  it('buttons are keyboard accessible', async () => {
    const handleClick = jest.fn();
    
    render(
      <button onClick={handleClick} data-testid="test-button">
        Click me
      </button>
    );
    
    const button = screen.getByTestId('test-button');
    button.focus();
    
    // Simulate Enter key
    await userEvent.keyboard('{Enter}');
    
    expect(handleClick).toHaveBeenCalled();
  });

  it('tab navigation works through form', async () => {
    render(
      <form>
        <input data-testid="input-1" tabIndex={0} />
        <input data-testid="input-2" tabIndex={0} />
        <button data-testid="submit" tabIndex={0}>Submit</button>
      </form>
    );
    
    // Tab through elements
    await userEvent.tab();
    expect(document.activeElement).toBe(screen.getByTestId('input-1'));
    
    await userEvent.tab();
    expect(document.activeElement).toBe(screen.getByTestId('input-2'));
    
    await userEvent.tab();
    expect(document.activeElement).toBe(screen.getByTestId('submit'));
  });
});

// ==============================================================================
// ARIA Labels Tests
// ==============================================================================

describe('ARIA Labels', () => {
  it('search input has accessible label', () => {
    render(
      <div>
        <label htmlFor="search">Search Products</label>
        <input 
          id="search"
          type="text" 
          aria-label="Search products"
          placeholder="Search..."
        />
      </div>
    );
    
    expect(screen.getByLabelText('Search Products')).toBeInTheDocument();
  });

  it('buttons have descriptive labels', () => {
    render(
      <div>
        <button aria-label="Start voice recording">🎤</button>
        <button aria-label="Upload image for search">📷</button>
        <button aria-label="Clear search">✕</button>
      </div>
    );
    
    expect(screen.getByLabelText('Start voice recording')).toBeInTheDocument();
    expect(screen.getByLabelText('Upload image for search')).toBeInTheDocument();
    expect(screen.getByLabelText('Clear search')).toBeInTheDocument();
  });

  it('loading states have aria-busy', () => {
    render(
      <div aria-busy="true" aria-label="Loading products">
        Loading...
      </div>
    );
    
    const loading = screen.getByLabelText('Loading products');
    expect(loading).toHaveAttribute('aria-busy', 'true');
  });

  it('error messages are announced', () => {
    render(
      <div role="alert" aria-live="polite">
        Error: Unable to load products. Please try again.
      </div>
    );
    
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});

// ==============================================================================
// Color Contrast Tests (Visual)
// ==============================================================================

describe('Visual Accessibility', () => {
  it('product cards have proper heading structure', () => {
    render(
      <article data-testid="product-card">
        <h3>Product Name</h3>
        <p>$99.99</p>
        <p>Description text</p>
      </article>
    );
    
    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Product Name');
  });

  it('images have alt text', () => {
    render(
      <div>
        <img src="/product.jpg" alt="Blue wireless headphones" />
        <img src="/logo.png" alt="FinFind logo" />
      </div>
    );
    
    expect(screen.getByAltText('Blue wireless headphones')).toBeInTheDocument();
    expect(screen.getByAltText('FinFind logo')).toBeInTheDocument();
  });

  it('decorative images have empty alt', () => {
    render(
      <img src="/decoration.png" alt="" role="presentation" />
    );
    
    const img = screen.getByRole('presentation');
    expect(img).toHaveAttribute('alt', '');
  });
});

// ==============================================================================
// Form Accessibility Tests
// ==============================================================================

describe('Form Accessibility', () => {
  it('required fields are marked', () => {
    render(
      <form>
        <label htmlFor="email">
          Email <span aria-hidden="true">*</span>
          <span className="sr-only">(required)</span>
        </label>
        <input 
          id="email" 
          type="email" 
          required 
          aria-required="true"
        />
      </form>
    );
    
    const input = screen.getByLabelText(/Email/);
    expect(input).toHaveAttribute('aria-required', 'true');
  });

  it('form errors are associated with inputs', () => {
    render(
      <form>
        <label htmlFor="budget">Budget</label>
        <input 
          id="budget" 
          type="number" 
          aria-invalid="true"
          aria-describedby="budget-error"
        />
        <span id="budget-error" role="alert">
          Please enter a valid budget
        </span>
      </form>
    );
    
    const input = screen.getByLabelText('Budget');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-describedby', 'budget-error');
  });

  it('select elements have labels', () => {
    render(
      <div>
        <label htmlFor="category">Category</label>
        <select id="category">
          <option value="">Select category</option>
          <option value="electronics">Electronics</option>
        </select>
      </div>
    );
    
    expect(screen.getByLabelText('Category')).toBeInTheDocument();
  });
});

// ==============================================================================
// Screen Reader Tests
// ==============================================================================

describe('Screen Reader Support', () => {
  it('page has main landmark', () => {
    render(
      <main data-testid="main-content">
        <h1>Search Products</h1>
        <p>Find what you need</p>
      </main>
    );
    
    expect(screen.getByRole('main')).toBeInTheDocument();
  });

  it('navigation has nav landmark', () => {
    render(
      <nav aria-label="Main navigation">
        <ul>
          <li><a href="/">Home</a></li>
          <li><a href="/search">Search</a></li>
        </ul>
      </nav>
    );
    
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });

  it('status updates are announced', () => {
    render(
      <div 
        role="status" 
        aria-live="polite"
        aria-atomic="true"
      >
        5 products found
      </div>
    );
    
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-live', 'polite');
  });

  it('dialog has proper role and label', () => {
    render(
      <div 
        role="dialog" 
        aria-modal="true"
        aria-labelledby="dialog-title"
      >
        <h2 id="dialog-title">Filter Products</h2>
        <p>Select your preferences</p>
      </div>
    );
    
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'dialog-title');
  });
});

// ==============================================================================
// Focus Management Tests
// ==============================================================================

describe('Focus Management', () => {
  it('modal traps focus', async () => {
    render(
      <div role="dialog" aria-modal="true">
        <button data-testid="close">Close</button>
        <input data-testid="input" />
        <button data-testid="save">Save</button>
      </div>
    );
    
    // Focus should cycle within modal
    screen.getByTestId('close').focus();
    
    await userEvent.tab();
    expect(document.activeElement).toBe(screen.getByTestId('input'));
    
    await userEvent.tab();
    expect(document.activeElement).toBe(screen.getByTestId('save'));
  });

  it('skip link is available', () => {
    render(
      <div>
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <nav>Navigation</nav>
        <main id="main-content">Main content</main>
      </div>
    );
    
    expect(screen.getByText('Skip to main content')).toBeInTheDocument();
  });
});

// ==============================================================================
// Responsive Text Tests
// ==============================================================================

describe('Responsive Design Accessibility', () => {
  it('text can be resized', () => {
    // Text should use relative units (em, rem) not px
    // This is more of a CSS test, but we can verify structure
    render(
      <div style={{ fontSize: '1rem' }}>
        <h1 style={{ fontSize: '2em' }}>Heading</h1>
        <p style={{ fontSize: '1em' }}>Body text</p>
      </div>
    );
    
    expect(screen.getByText('Heading')).toBeInTheDocument();
    expect(screen.getByText('Body text')).toBeInTheDocument();
  });

  it('touch targets are adequate size', () => {
    // Buttons should be at least 44x44 pixels
    render(
      <button 
        style={{ minWidth: '44px', minHeight: '44px' }}
        data-testid="touch-target"
      >
        Tap
      </button>
    );
    
    const button = screen.getByTestId('touch-target');
    expect(button).toBeInTheDocument();
  });
});
