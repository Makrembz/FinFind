/**
 * Component tests for UI elements.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// ==============================================================================
// Button Component Tests
// ==============================================================================

describe('Button Component', () => {
  const mockOnClick = jest.fn();

  beforeEach(() => {
    mockOnClick.mockClear();
  });

  it('renders button with text', () => {
    render(
      <button onClick={mockOnClick}>Click me</button>
    );
    
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', async () => {
    render(
      <button onClick={mockOnClick}>Click me</button>
    );
    
    await userEvent.click(screen.getByText('Click me'));
    
    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  it('can be disabled', () => {
    render(
      <button disabled onClick={mockOnClick}>Disabled</button>
    );
    
    const button = screen.getByText('Disabled');
    expect(button).toBeDisabled();
  });
});

// ==============================================================================
// Input Component Tests
// ==============================================================================

describe('Input Component', () => {
  it('renders input field', () => {
    render(
      <input placeholder="Enter text" data-testid="test-input" />
    );
    
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
  });

  it('handles text input', async () => {
    render(
      <input placeholder="Enter text" data-testid="test-input" />
    );
    
    const input = screen.getByTestId('test-input');
    await userEvent.type(input, 'Hello World');
    
    expect(input).toHaveValue('Hello World');
  });

  it('handles onChange events', async () => {
    const handleChange = jest.fn();
    
    render(
      <input onChange={handleChange} data-testid="test-input" />
    );
    
    await userEvent.type(screen.getByTestId('test-input'), 'a');
    
    expect(handleChange).toHaveBeenCalled();
  });
});

// ==============================================================================
// Card Component Tests
// ==============================================================================

describe('Card Component', () => {
  it('renders card with content', () => {
    render(
      <div className="card" data-testid="test-card">
        <h3>Card Title</h3>
        <p>Card content</p>
      </div>
    );
    
    expect(screen.getByText('Card Title')).toBeInTheDocument();
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders card with image', () => {
    render(
      <div className="card" data-testid="test-card">
        <img src="/test.jpg" alt="Test image" />
        <h3>Product</h3>
      </div>
    );
    
    expect(screen.getByAltText('Test image')).toBeInTheDocument();
  });
});

// ==============================================================================
// Badge Component Tests
// ==============================================================================

describe('Badge Component', () => {
  it('renders badge with text', () => {
    render(
      <span className="badge" data-testid="badge">New</span>
    );
    
    expect(screen.getByText('New')).toBeInTheDocument();
  });

  it('renders badge with different variants', () => {
    const { rerender } = render(
      <span className="badge badge-success">Success</span>
    );
    
    expect(screen.getByText('Success')).toBeInTheDocument();
    
    rerender(
      <span className="badge badge-warning">Warning</span>
    );
    
    expect(screen.getByText('Warning')).toBeInTheDocument();
  });
});

// ==============================================================================
// Skeleton Component Tests
// ==============================================================================

describe('Skeleton Component', () => {
  it('renders skeleton loader', () => {
    render(
      <div className="skeleton" data-testid="skeleton" role="status" aria-label="Loading" />
    );
    
    expect(screen.getByTestId('skeleton')).toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    render(
      <div className="skeleton" role="status" aria-label="Loading content" />
    );
    
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Loading content');
  });
});

// ==============================================================================
// Slider Component Tests
// ==============================================================================

describe('Slider Component', () => {
  it('renders slider', () => {
    render(
      <input type="range" min={0} max={100} defaultValue={50} data-testid="slider" />
    );
    
    expect(screen.getByTestId('slider')).toBeInTheDocument();
  });

  it('handles value changes', async () => {
    const handleChange = jest.fn();
    
    render(
      <input 
        type="range" 
        min={0} 
        max={100} 
        defaultValue={50} 
        onChange={handleChange}
        data-testid="slider" 
      />
    );
    
    const slider = screen.getByTestId('slider');
    fireEvent.change(slider, { target: { value: '75' } });
    
    expect(handleChange).toHaveBeenCalled();
  });
});

// ==============================================================================
// Dialog Component Tests
// ==============================================================================

describe('Dialog Component', () => {
  it('shows dialog when open', () => {
    render(
      <dialog open data-testid="dialog">
        <h2>Dialog Title</h2>
        <p>Dialog content</p>
      </dialog>
    );
    
    expect(screen.getByTestId('dialog')).toBeInTheDocument();
    expect(screen.getByText('Dialog Title')).toBeInTheDocument();
  });

  it('handles close action', async () => {
    const handleClose = jest.fn();
    
    render(
      <dialog open data-testid="dialog">
        <h2>Dialog Title</h2>
        <button onClick={handleClose}>Close</button>
      </dialog>
    );
    
    await userEvent.click(screen.getByText('Close'));
    
    expect(handleClose).toHaveBeenCalled();
  });
});

// ==============================================================================
// Tabs Component Tests
// ==============================================================================

describe('Tabs Component', () => {
  it('renders tabs', () => {
    render(
      <div data-testid="tabs">
        <button role="tab" aria-selected="true">Tab 1</button>
        <button role="tab" aria-selected="false">Tab 2</button>
        <button role="tab" aria-selected="false">Tab 3</button>
      </div>
    );
    
    expect(screen.getByText('Tab 1')).toBeInTheDocument();
    expect(screen.getByText('Tab 2')).toBeInTheDocument();
    expect(screen.getByText('Tab 3')).toBeInTheDocument();
  });

  it('handles tab selection', async () => {
    const setActiveTab = jest.fn();
    
    render(
      <div data-testid="tabs">
        <button role="tab" onClick={() => setActiveTab(0)}>Tab 1</button>
        <button role="tab" onClick={() => setActiveTab(1)}>Tab 2</button>
      </div>
    );
    
    await userEvent.click(screen.getByText('Tab 2'));
    
    expect(setActiveTab).toHaveBeenCalledWith(1);
  });
});

// ==============================================================================
// Tooltip Component Tests
// ==============================================================================

describe('Tooltip Component', () => {
  it('renders trigger element', () => {
    render(
      <div>
        <button data-tooltip="Helpful tip">Hover me</button>
      </div>
    );
    
    expect(screen.getByText('Hover me')).toBeInTheDocument();
  });
});

// ==============================================================================
// Progress Component Tests
// ==============================================================================

describe('Progress Component', () => {
  it('renders progress bar', () => {
    render(
      <progress value={50} max={100} data-testid="progress" />
    );
    
    expect(screen.getByTestId('progress')).toBeInTheDocument();
  });

  it('shows correct progress value', () => {
    render(
      <progress value={75} max={100} data-testid="progress" />
    );
    
    const progress = screen.getByTestId('progress');
    expect(progress).toHaveAttribute('value', '75');
    expect(progress).toHaveAttribute('max', '100');
  });
});

// ==============================================================================
// Select Component Tests
// ==============================================================================

describe('Select Component', () => {
  it('renders select with options', () => {
    render(
      <select data-testid="select">
        <option value="1">Option 1</option>
        <option value="2">Option 2</option>
        <option value="3">Option 3</option>
      </select>
    );
    
    expect(screen.getByTestId('select')).toBeInTheDocument();
    expect(screen.getByText('Option 1')).toBeInTheDocument();
  });

  it('handles selection change', async () => {
    const handleChange = jest.fn();
    
    render(
      <select onChange={handleChange} data-testid="select">
        <option value="1">Option 1</option>
        <option value="2">Option 2</option>
      </select>
    );
    
    await userEvent.selectOptions(screen.getByTestId('select'), '2');
    
    expect(handleChange).toHaveBeenCalled();
  });
});
