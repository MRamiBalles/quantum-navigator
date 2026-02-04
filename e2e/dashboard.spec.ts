/**
 * Q-Orchestrator E2E Tests - Dashboard Navigation
 * ================================================
 * Tests critical navigation flows in the main dashboard
 */

import { test, expect } from '@playwright/test';

test.describe('Dashboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load the main dashboard', async ({ page }) => {
    // Verify main layout is visible
    await expect(page.locator('main')).toBeVisible();
    
    // Check for sidebar
    await expect(page.getByRole('navigation')).toBeVisible();
    
    // Verify dashboard title
    await expect(page.getByText('Dashboard Principal')).toBeVisible();
  });

  test('should navigate to Neutral Atom Studio', async ({ page }) => {
    // Click on Neutral Atom menu item
    await page.getByText('Neutral Atom Studio').click();
    
    // Verify navigation occurred
    await expect(page.getByText('Neutral Atom Studio')).toBeVisible();
    
    // Check for atom register editor
    await expect(page.getByText('Atom Register')).toBeVisible({ timeout: 5000 });
  });

  test('should navigate to Benchmark Results', async ({ page }) => {
    // Click on Benchmarks menu item
    await page.getByText('Benchmarks').first().click();
    
    // Verify benchmark page loaded
    await expect(page.getByText('Benchmark Results')).toBeVisible();
  });

  test('should navigate to Neural Decoder Analysis', async ({ page }) => {
    // Click on GNN Decoder menu item
    await page.getByText('GNN Decoder').click();
    
    // Verify decoder analysis page loaded
    await expect(page.getByText('Neural Decoder Analysis')).toBeVisible();
  });

  test('should toggle sidebar collapse', async ({ page }) => {
    // Find and click sidebar toggle button
    const sidebarToggle = page.getByRole('button', { name: /toggle/i }).first();
    
    if (await sidebarToggle.isVisible()) {
      await sidebarToggle.click();
      
      // Wait for animation
      await page.waitForTimeout(300);
      
      // Sidebar should be collapsed (narrower)
      const sidebar = page.locator('[data-sidebar="true"]').first();
      if (await sidebar.isVisible()) {
        const box = await sidebar.boundingBox();
        if (box) {
          // Collapsed sidebar should be narrow
          expect(box.width).toBeLessThan(100);
        }
      }
    }
  });
});

test.describe('Dashboard Module Cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display all module cards on dashboard', async ({ page }) => {
    // Check for key module cards
    const moduleNames = [
      'Neutral Atom',
      'Benchmark',
      'GNN Decoder',
    ];

    for (const moduleName of moduleNames) {
      await expect(page.getByText(moduleName, { exact: false }).first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('should click module card and navigate', async ({ page }) => {
    // Find a clickable module card
    const moduleCard = page.locator('.quantum-card').first();
    
    if (await moduleCard.isVisible()) {
      await moduleCard.click();
      
      // Should navigate to a different view
      await page.waitForTimeout(500);
    }
  });
});
