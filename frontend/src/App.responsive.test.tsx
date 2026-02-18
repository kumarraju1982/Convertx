/**
 * Unit Tests for Responsive Behavior
 * 
 * Tests specific responsive layout scenarios at mobile, tablet, and desktop viewports.
 * Validates: Requirements 14.1, 14.2, 14.3
 */

import { render } from '@testing-library/react';
import App from './App';

// Mock the API module
jest.mock('./services/api', () => ({
  api: {
    uploadFile: jest.fn(),
    getJobStatus: jest.fn(),
    downloadFile: jest.fn(),
  },
}));

// Mock the download utility
jest.mock('./utils/download', () => ({
  downloadConvertedFile: jest.fn(),
}));

describe('Responsive Behavior Unit Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Mobile Layout (320px)', () => {
    beforeEach(() => {
      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 320,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 568,
      });
    });

    it('should render mobile layout with proper spacing', () => {
      const { container } = render(<App />);

      // Verify main container has mobile-friendly padding
      const main = container.querySelector('main');
      expect(main?.className).toContain('px-4');
      expect(main?.className).toContain('py-12');
    });

    it('should render header with mobile spacing', () => {
      const { container } = render(<App />);

      const header = container.querySelector('header');
      const headerInner = header?.querySelector('div');
      
      expect(headerInner?.className).toContain('px-4');
      expect(headerInner?.className).toContain('py-6');
    });

    it('should render footer with mobile spacing', () => {
      const { container } = render(<App />);

      const footer = container.querySelector('footer');
      const footerInner = footer?.querySelector('div');
      
      expect(footerInner?.className).toContain('px-4');
      expect(footerInner?.className).toContain('py-6');
    });

    it('should maintain full-width layout on mobile', () => {
      const { container } = render(<App />);

      const main = container.querySelector('main');
      expect(main?.className).toContain('w-full');
      expect(main?.className).toContain('max-w-7xl');
    });

    it('should render all essential elements on mobile', () => {
      const { container } = render(<App />);

      expect(container.querySelector('header')).toBeTruthy();
      expect(container.querySelector('main')).toBeTruthy();
      expect(container.querySelector('footer')).toBeTruthy();
      expect(container.querySelector('h1')).toBeTruthy();
    });
  });

  describe('Tablet Layout (768px)', () => {
    beforeEach(() => {
      // Set tablet viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 1024,
      });
    });

    it('should render tablet layout with proper spacing', () => {
      const { container } = render(<App />);

      const main = container.querySelector('main');
      // Should have responsive padding classes
      expect(main?.className).toMatch(/px-\d+/);
      expect(main?.className).toMatch(/sm:px-\d+/);
    });

    it('should render header with tablet spacing', () => {
      const { container } = render(<App />);

      const header = container.querySelector('header');
      const headerInner = header?.querySelector('div');
      
      expect(headerInner?.className).toMatch(/px-\d+/);
      expect(headerInner?.className).toMatch(/sm:px-\d+/);
    });

    it('should maintain centered layout on tablet', () => {
      const { container } = render(<App />);

      const main = container.querySelector('main');
      expect(main?.className).toContain('mx-auto');
      expect(main?.className).toContain('max-w-7xl');
    });

    it('should render all content properly on tablet', () => {
      const { container } = render(<App />);

      expect(container.querySelector('header')).toBeTruthy();
      expect(container.querySelector('main')).toBeTruthy();
      expect(container.querySelector('footer')).toBeTruthy();
      
      // Verify content is visible
      const h1 = container.querySelector('h1');
      expect(h1?.textContent).toContain('ConvertX');
    });
  });

  describe('Desktop Layout (1024px+)', () => {
    beforeEach(() => {
      // Set desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 1080,
      });
    });

    it('should render desktop layout with proper spacing', () => {
      const { container } = render(<App />);

      const main = container.querySelector('main');
      // Should have all responsive padding classes
      expect(main?.className).toMatch(/px-\d+/);
      expect(main?.className).toMatch(/sm:px-\d+/);
      expect(main?.className).toMatch(/lg:px-\d+/);
    });

    it('should render header with desktop spacing', () => {
      const { container } = render(<App />);

      const header = container.querySelector('header');
      const headerInner = header?.querySelector('div');
      
      expect(headerInner?.className).toMatch(/px-\d+/);
      expect(headerInner?.className).toMatch(/sm:px-\d+/);
      expect(headerInner?.className).toMatch(/lg:px-\d+/);
    });

    it('should maintain max-width constraint on desktop', () => {
      const { container } = render(<App />);

      const main = container.querySelector('main');
      expect(main?.className).toContain('max-w-7xl');
      expect(main?.className).toContain('mx-auto');
    });

    it('should render full-width layout with centered content', () => {
      const { container } = render(<App />);

      const main = container.querySelector('main');
      expect(main?.className).toContain('w-full');
      expect(main?.className).toContain('mx-auto');
    });

    it('should display all elements with proper hierarchy on desktop', () => {
      const { container } = render(<App />);

      // Verify semantic structure
      expect(container.querySelector('header')).toBeTruthy();
      expect(container.querySelector('main')).toBeTruthy();
      expect(container.querySelector('footer')).toBeTruthy();

      // Verify heading
      const h1 = container.querySelector('h1');
      expect(h1).toBeTruthy();
      expect(h1?.className).toContain('text-3xl');
    });
  });

  describe('Viewport Transitions', () => {
    it('should handle transition from mobile to desktop', () => {
      // Start with mobile
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 320,
      });

      const { container, rerender } = render(<App />);
      
      // Verify mobile layout
      let main = container.querySelector('main');
      expect(main?.className).toContain('px-4');

      // Switch to desktop
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920,
      });

      rerender(<App />);

      // Verify desktop layout still works
      main = container.querySelector('main');
      expect(main?.className).toContain('max-w-7xl');
      expect(main?.className).toContain('mx-auto');
    });

    it('should handle transition from desktop to mobile', () => {
      // Start with desktop
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920,
      });

      const { container, rerender } = render(<App />);
      
      // Verify desktop layout
      let main = container.querySelector('main');
      expect(main?.className).toContain('max-w-7xl');

      // Switch to mobile
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 320,
      });

      rerender(<App />);

      // Verify mobile layout still works
      main = container.querySelector('main');
      expect(main?.className).toContain('px-4');
    });

    it('should maintain content visibility during viewport changes', () => {
      // Start with mobile
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 320,
      });

      const { container, rerender } = render(<App />);
      
      // Verify content is visible
      expect(container.querySelector('h1')?.textContent).toContain('ConvertX');

      // Switch to tablet
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      rerender(<App />);

      // Content should still be visible
      expect(container.querySelector('h1')?.textContent).toContain('ConvertX');

      // Switch to desktop
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920,
      });

      rerender(<App />);

      // Content should still be visible
      expect(container.querySelector('h1')?.textContent).toContain('ConvertX');
    });
  });

  describe('Flex Layout Structure', () => {
    it('should use flex column layout for vertical stacking', () => {
      const { container } = render(<App />);

      const contentContainer = container.querySelector('.min-h-screen > .relative');
      expect(contentContainer?.className).toContain('flex');
      expect(contentContainer?.className).toContain('flex-col');
    });

    it('should have flex-1 on main content to fill space', () => {
      const { container } = render(<App />);

      const main = container.querySelector('main');
      expect(main?.className).toContain('flex-1');
    });

    it('should maintain min-height for full viewport coverage', () => {
      const { container } = render(<App />);

      const outerContainer = container.querySelector('.min-h-screen');
      expect(outerContainer).toBeTruthy();
      expect(outerContainer?.className).toContain('min-h-screen');
    });

    it('should have proper z-index layering', () => {
      const { container } = render(<App />);

      // Content should be above background
      const contentContainer = container.querySelector('.relative.z-10');
      expect(contentContainer).toBeTruthy();
    });
  });

  describe('Container Max Width', () => {
    it('should apply max-width to main content', () => {
      const { container } = render(<App />);

      const main = container.querySelector('main');
      expect(main?.className).toContain('max-w-7xl');
    });

    it('should apply max-width to header content', () => {
      const { container } = render(<App />);

      const header = container.querySelector('header');
      const headerInner = header?.querySelector('div');
      expect(headerInner?.className).toContain('max-w-7xl');
    });

    it('should apply max-width to footer content', () => {
      const { container } = render(<App />);

      const footer = container.querySelector('footer');
      const footerInner = footer?.querySelector('div');
      expect(footerInner?.className).toContain('max-w-7xl');
    });

    it('should center content with mx-auto', () => {
      const { container } = render(<App />);

      const main = container.querySelector('main');
      expect(main?.className).toContain('mx-auto');

      const header = container.querySelector('header div');
      expect(header?.className).toContain('mx-auto');

      const footer = container.querySelector('footer div');
      expect(footer?.className).toContain('mx-auto');
    });
  });
});
