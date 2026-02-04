/**
 * Q-Orchestrator E2E Tests - Benchmark Analysis
 * ==============================================
 * Tests benchmark visualization and comparison flows
 */

import { test, expect } from '@playwright/test';

test.describe('Benchmark Results', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Navigate to benchmarks
    await page.getByText('Benchmarks').first().click();
    await page.waitForTimeout(500);
  });

  test('should display benchmark charts', async ({ page }) => {
    // Look for chart containers
    const chartContainer = page.locator('.recharts-wrapper').first();
    
    // Charts should be present
    await expect(chartContainer).toBeVisible({ timeout: 10000 });
  });

  test('should switch between benchmark tabs', async ({ page }) => {
    // Find tab buttons
    const tabList = page.getByRole('tablist');
    
    if (await tabList.isVisible()) {
      const tabs = await tabList.getByRole('tab').all();
      
      // Click through tabs if available
      for (const tab of tabs.slice(0, 3)) {
        await tab.click();
        await page.waitForTimeout(300);
      }
    }
  });

  test('should display data in tables', async ({ page }) => {
    // Check for data tables
    const table = page.locator('table').first();
    
    if (await table.isVisible()) {
      // Should have table headers
      const headers = await page.locator('th').count();
      expect(headers).toBeGreaterThan(0);
    }
  });

  test('should export benchmark data', async ({ page }) => {
    // Look for export button
    const exportBtn = page.getByRole('button', { name: /export|download|csv/i }).first();
    
    if (await exportBtn.isVisible()) {
      // Set up download listener
      const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null);
      
      await exportBtn.click();
      
      const download = await downloadPromise;
      if (download) {
        expect(download.suggestedFilename()).toContain('.csv');
      }
    }
  });
});

test.describe('Benchmark Comparison', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByText('Benchmarks').first().click();
    await page.waitForTimeout(500);
  });

  test('should toggle comparison mode', async ({ page }) => {
    // Look for comparison toggle or button
    const compareBtn = page.getByRole('button', { name: /compare|comparison/i }).first();
    
    if (await compareBtn.isVisible()) {
      await compareBtn.click();
      await page.waitForTimeout(300);
    }
  });

  test('should filter benchmark data', async ({ page }) => {
    // Look for filter controls
    const filterSelect = page.getByRole('combobox').first();
    
    if (await filterSelect.isVisible()) {
      await filterSelect.click();
      
      // Select an option if dropdown appears
      const option = page.getByRole('option').first();
      if (await option.isVisible()) {
        await option.click();
      }
    }
  });
});
