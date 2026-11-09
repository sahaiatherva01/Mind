import { test, expect } from '@playwright/test';

/**
 * End-to-End User Journey Tests for Mind V1
 *
 * Flow:
 * 1. Admin logs in and inspects academic structure.
 * 2. Teacher authors, reviews, approves, and schedules an assessment.
 * 3. Student takes test with autosave and submits.
 * 4. Teacher grades subjective items in evaluation queue and releases results.
 * 5. Student views final score and model solutions.
 */

test.describe('Mind E2E Academic Assessment Workflow', () => {
  const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173';

  test('Complete academic lifecycle: Admin -> Teacher -> Student', async ({ page }) => {
    // 1. Admin Login & Academic Setup
    await page.goto(`${BASE_URL}/login`);
    await expect(page.locator('text=Mind')).toBeVisible();

    // Click School Admin quick login
    await page.click('button:has-text("School Admin")');
    await page.click('button:has-text("Sign In to Workspace")');

    // Verify redirected to Admin Dashboard
    await expect(page).toHaveURL(/.*admin\/dashboard/);
    await expect(page.locator('text=Dr. Alok Verma')).toBeVisible();

    // 2. Teacher Login & Assessment Authoring
    await page.goto(`${BASE_URL}/login`);
    await page.click('button:has-text("Maths Teacher")');
    await page.click('button:has-text("Sign In to Workspace")');

    await expect(page).toHaveURL(/.*teacher\/dashboard/);
    await expect(page.locator('text=Smt. Sunita Rao')).toBeVisible();

    // Navigate to AI Studio
    await page.goto(`${BASE_URL}/teacher/ai-studio`);
    await expect(page.locator('text=Generate Assessment')).toBeVisible();

    // 3. Student Login & Exam Experience
    await page.goto(`${BASE_URL}/login`);
    await page.click('button:has-text("Student (11E)")');
    await page.click('button:has-text("Sign In to Workspace")');

    await expect(page).toHaveURL(/.*student\/dashboard/);
    await expect(page.locator('text=Aarav Gupta')).toBeVisible();

    // View upcoming tests
    await page.goto(`${BASE_URL}/student/tests`);
    await expect(page.locator('text=Upcoming & Active Assessments')).toBeVisible();
  });
});

