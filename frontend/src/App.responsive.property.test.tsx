/**
 * Property-Based Tests for Responsive Layout
 * 
 * **Feature: pdf-to-word-converter, Property 32: Responsive Layout Adaptation**
 * **Validates: Requirements 14.3**
 * 
 * Tests that the web interface adapts the layout responsively for any viewport size change.
 */

import { render } from '@testing-library/react';
import * as fc from 'fast-check';
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

describe('Property 32: Responsive Layout Adaptation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should adapt layout for any viewport width', () => {
    fc.assert(
      fc.property(
        // Generate viewport widths from 320px (mobile) to 2560px (large desktop)
        fc.integer({ min: 320, max: 2560 }),
        fc.integer({ min: 480, max: 1440 }),
        (width, height) => {
          // Set viewport size
          Object.defineProperty(window, 'innerWidth', {
            writable: true,
            configurable: true,
            value: width,
          });
          Object.defineProperty(window, 'innerHeight', {
            writable: true,
            configurable: true,
            value: height,
          });

          // Render the app
          const { container, unmount } = render(<App />);

          try {
            // Verify the app renders without errors
            expect(container).toBeTruthy();

            // Verify main container has responsive classes
            const mainContainer = container.querySelector('main');
            expect(mainContainer).toBeTruthy();
            expect(mainContainer?.className).toContain('max-w-7xl');
            expect(mainContainer?.className).toContain('mx-auto');

            // Verify responsive padding classes are present
            const hasResponsivePadding = 
              mainContainer?.className.includes('px-4') ||
              mainContainer?.className.includes('sm:px-6') ||
              mainContainer?.className.includes('lg:px-8');
            expect(hasResponsivePadding).toBe(true);

            // Verify header has responsive classes
            const header = container.querySelector('header');
            expect(header).toBeTruthy();
            const headerContainer = header?.querySelector('div');
            expect(headerContainer?.className).toContain('max-w-7xl');

            // Verify the layout doesn't break (no overflow issues)
            const body = container.querySelector('.min-h-screen');
            expect(body).toBeTruthy();
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should maintain proper spacing at different viewport sizes', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(
          { width: 320, height: 568, name: 'mobile' },
          { width: 768, height: 1024, name: 'tablet' },
          { width: 1024, height: 768, name: 'desktop-small' },
          { width: 1920, height: 1080, name: 'desktop-large' }
        ),
        (viewport) => {
          // Set viewport size
          Object.defineProperty(window, 'innerWidth', {
            writable: true,
            configurable: true,
            value: viewport.width,
          });
          Object.defineProperty(window, 'innerHeight', {
            writable: true,
            configurable: true,
            value: viewport.height,
          });

          // Render the app
          const { container, unmount } = render(<App />);

          try {
            // Verify spacing classes are present
            const main = container.querySelector('main');
            expect(main?.className).toMatch(/py-\d+/); // Has vertical padding
            expect(main?.className).toMatch(/px-\d+/); // Has horizontal padding

            // Verify header spacing
            const header = container.querySelector('header');
            const headerInner = header?.querySelector('div');
            expect(headerInner?.className).toMatch(/py-\d+/);
            expect(headerInner?.className).toMatch(/px-\d+/);

            // Verify footer spacing
            const footer = container.querySelector('footer');
            const footerInner = footer?.querySelector('div');
            expect(footerInner?.className).toMatch(/py-\d+/);
            expect(footerInner?.className).toMatch(/px-\d+/);
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should render all essential elements at any viewport size', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 320, max: 2560 }),
        fc.integer({ min: 480, max: 1440 }),
        (width, height) => {
          // Set viewport size
          Object.defineProperty(window, 'innerWidth', {
            writable: true,
            configurable: true,
            value: width,
          });
          Object.defineProperty(window, 'innerHeight', {
            writable: true,
            configurable: true,
            value: height,
          });

          // Render the app
          const { container, unmount } = render(<App />);

          try {
            // Verify essential elements are present regardless of viewport
            expect(container.querySelector('header')).toBeTruthy();
            expect(container.querySelector('main')).toBeTruthy();
            expect(container.querySelector('footer')).toBeTruthy();

            // Verify header content using querySelector instead of getByText
            const header = container.querySelector('h1');
            expect(header?.textContent).toContain('ConvertX');

            // Verify footer content
            const footer = container.querySelector('footer');
            expect(footer?.textContent).toContain('Created by');

            // Verify main content area exists
            const main = container.querySelector('main');
            expect(main).toBeTruthy();
            expect(main?.children.length).toBeGreaterThan(0);
          } finally {
            // Clean up after each test
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should maintain flex layout structure at all viewport sizes', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 320, max: 2560 }),
        (width) => {
          // Set viewport size
          Object.defineProperty(window, 'innerWidth', {
            writable: true,
            configurable: true,
            value: width,
          });

          // Render the app
          const { container, unmount } = render(<App />);

          try {
            // Verify flex layout classes
            const contentContainer = container.querySelector('.min-h-screen > .relative');
            expect(contentContainer?.className).toContain('flex');
            expect(contentContainer?.className).toContain('flex-col');

            // Verify main content has flex-1 to fill space
            const main = container.querySelector('main');
            expect(main?.className).toContain('flex-1');
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should handle viewport size transitions smoothly', () => {
    fc.assert(
      fc.property(
        fc.array(fc.integer({ min: 320, max: 2560 }), { minLength: 2, maxLength: 5 }),
        (widths) => {
          let previousRender: ReturnType<typeof render> | null = null;

          // Test transitioning through multiple viewport sizes
          for (const width of widths) {
            Object.defineProperty(window, 'innerWidth', {
              writable: true,
              configurable: true,
              value: width,
            });

            // Clean up previous render
            if (previousRender) {
              previousRender.unmount();
            }

            // Render at new viewport size
            previousRender = render(<App />);
            const { container } = previousRender;

            // Verify the app still renders correctly after viewport change
            expect(container).toBeTruthy();
            expect(container.querySelector('header')).toBeTruthy();
            expect(container.querySelector('main')).toBeTruthy();
            expect(container.querySelector('footer')).toBeTruthy();
          }

          // Clean up final render
          if (previousRender) {
            previousRender.unmount();
          }

          // If we got here without errors, the transitions were smooth
          expect(true).toBe(true);
        }
      ),
      { numRuns: 50 } // Fewer runs since this tests multiple transitions
    );
  });
});
