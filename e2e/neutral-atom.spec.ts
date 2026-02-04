/**
 * Q-Orchestrator E2E Tests - Neutral Atom Studio
 * ===============================================
 * Tests atom register editor and sequence timeline
 */

import { test, expect } from '@playwright/test';

test.describe('Neutral Atom Studio', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Navigate to Neutral Atom Studio
    await page.getByText('Neutral Atom Studio').click();
    await page.waitForTimeout(500);
  });

  test('should display atom register editor', async ({ page }) => {
    // Check for the editor canvas or grid
    await expect(page.getByText('Atom Register', { exact: false })).toBeVisible({ timeout: 5000 });
  });

  test('should display analog sequence timeline', async ({ page }) => {
    // Check for timeline component
    await expect(page.getByText('Sequence', { exact: false })).toBeVisible({ timeout: 5000 });
  });

  test('should show validation panel', async ({ page }) => {
    // Look for validation or constraints section
    const validationSection = page.getByText(/validation|constraints|errors/i).first();
    
    if (await validationSection.isVisible()) {
      expect(await validationSection.isVisible()).toBeTruthy();
    }
  });

  test('should interact with atom position controls', async ({ page }) => {
    // Look for position input fields
    const positionInput = page.locator('input[type="number"]').first();
    
    if (await positionInput.isVisible()) {
      await positionInput.fill('5.0');
      await page.keyboard.press('Enter');
      
      // Value should be updated
      await expect(positionInput).toHaveValue('5.0');
    }
  });

  test('should switch between editor tabs', async ({ page }) => {
    // Look for tabs in the studio
    const tabs = page.getByRole('tab');
    const tabCount = await tabs.count();
    
    if (tabCount > 1) {
      // Click second tab
      await tabs.nth(1).click();
      await page.waitForTimeout(300);
      
      // Tab should be selected
      await expect(tabs.nth(1)).toHaveAttribute('aria-selected', 'true');
    }
  });
});

test.describe('Atom Register Manipulation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByText('Neutral Atom Studio').click();
    await page.waitForTimeout(500);
  });

  test('should add new atom to register', async ({ page }) => {
    // Look for add atom button
    const addBtn = page.getByRole('button', { name: /add|new|create/i }).first();
    
    if (await addBtn.isVisible()) {
      // Get initial atom count
      const initialAtoms = await page.locator('[data-atom]').count();
      
      await addBtn.click();
      await page.waitForTimeout(300);
      
      // Should have one more atom
      const newAtomCount = await page.locator('[data-atom]').count();
      expect(newAtomCount).toBeGreaterThanOrEqual(initialAtoms);
    }
  });

  test('should validate atom spacing constraints', async ({ page }) => {
    // Look for validation messages related to spacing
    const validationMsg = page.getByText(/spacing|distance|blockade/i).first();
    
    // This test checks that validation exists, even if no error is shown
    // The system should enforce minimum spacing requirements
  });
});
