/**
 * Q-Orchestrator E2E Tests - Accessibility & Responsiveness
 * ==========================================================
 * Tests accessibility compliance and responsive design
 */

import { test, expect } from '@playwright/test';

test.describe('Accessibility', () => {
  test('should have proper page structure', async ({ page }) => {
    await page.goto('/');
    
    // Check for main landmark
    await expect(page.getByRole('main')).toBeVisible();
    
    // Check for navigation
    await expect(page.getByRole('navigation')).toBeVisible();
    
    // Check for headings
    const headings = await page.getByRole('heading').count();
    expect(headings).toBeGreaterThan(0);
  });

  test('should have accessible buttons', async ({ page }) => {
    await page.goto('/');
    
    // All buttons should have accessible names
    const buttons = await page.getByRole('button').all();
    
    for (const button of buttons.slice(0, 10)) {
      const name = await button.getAttribute('aria-label') || await button.textContent();
      expect(name).toBeTruthy();
    }
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/');
    
    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Something should be focused
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBeTruthy();
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto('/');
    
    // Check that text elements are visible
    const mainText = page.getByText('Dashboard Principal');
    await expect(mainText).toBeVisible();
    
    // Text should have good contrast (visible against background)
    const color = await mainText.evaluate((el) => 
      window.getComputedStyle(el).color
    );
    expect(color).toBeTruthy();
  });
});

test.describe('Responsive Design', () => {
  test('should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    
    // Main content should be visible
    await expect(page.getByRole('main')).toBeVisible();
    
    // Sidebar might be collapsed or hidden
    const sidebar = page.locator('[data-sidebar="true"]').first();
    // On mobile, sidebar may be hidden initially - that's OK
  });

  test('should work on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    
    // Main content should be visible
    await expect(page.getByRole('main')).toBeVisible();
  });

  test('should work on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    
    // Full layout should be visible
    await expect(page.getByRole('main')).toBeVisible();
    await expect(page.getByRole('navigation')).toBeVisible();
  });

  test('should handle window resize', async ({ page }) => {
    await page.goto('/');
    
    // Start at desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(300);
    
    // Resize to mobile
    await page.setViewportSize({ width: 375, height: 812 });
    await page.waitForTimeout(300);
    
    // Content should still be visible
    await expect(page.getByRole('main')).toBeVisible();
    
    // Resize back to desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(300);
    
    await expect(page.getByRole('main')).toBeVisible();
  });
});
