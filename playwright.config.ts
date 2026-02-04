import { defineConfig, devices } from '@playwright/test';

/**
 * Q-Orchestrator E2E Test Configuration
 * ======================================
 * Playwright configuration for testing critical user flows
 * 
 * Run tests:
 *   npx playwright test
 *   npx playwright test --ui (interactive mode)
 *   npx playwright test --project=chromium (specific browser)
 */

export default defineConfig({
  testDir: './e2e',
  
  // Run tests in parallel
  fullyParallel: true,
  
  // Fail the build on CI if you accidentally left test.only
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Use half available workers on CI
  workers: process.env.CI ? 2 : undefined,
  
  // Reporter configuration
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],
  
  // Shared settings for all tests
  use: {
    // Base URL for navigation
    baseURL: 'http://localhost:5173',
    
    // Collect trace on first retry
    trace: 'on-first-retry',
    
    // Take screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video recording on failure
    video: 'on-first-retry',
    
    // Viewport
    viewport: { width: 1920, height: 1080 },
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // Mobile viewports
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 13'] },
    },
  ],

  // Run local dev server before starting the tests
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
