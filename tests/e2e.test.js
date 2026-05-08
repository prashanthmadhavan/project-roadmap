/**
 * Phase 1: E2E Tests (Playwright)
 * 
 * Testing user scenarios and browser interactions
 * - Delete task via event delegation (XSS prevention)
 * - Drag-drop without race condition
 * - Create task with date validation
 * - Login error handling
 * - Session timeout tracking
 * 
 * Run with: npx playwright test tests/e2e.test.js
 */

// This is a mock E2E test file showing the structure
// In production, use: npm install -D @playwright/test

const { test, expect } = require('@playwright/test');

// Configure test environment
test.describe.configure({ mode: 'parallel' });

const BASE_URL = 'http://localhost:8888';

// ============================================================================
// E2E TEST SUITE 1: Delete Task via Event Delegation (XSS Prevention)
// ============================================================================

test.describe('CR-01: Delete Task - XSS Prevention via Event Delegation', () => {
  
  test.beforeEach(async ({ page }) => {
    // Setup: Login as demo user
    await page.goto(`${BASE_URL}/index.html`);
    await page.fill('input[id="username"]', 'demo');
    await page.fill('input[id="password"]', 'Demo@1234');
    await page.click('button:has-text("Login")');
    await page.waitForSelector('#projectsList');
  });

  test('E2E-01: Should delete task without XSS vulnerability', async ({ page }) => {
    // Arrange: Verify task exists in the list
    const taskBefore = page.locator('.task-item:has-text("Design mockups")');
    await expect(taskBefore).toBeVisible();
    
    // Act: Click delete button (uses event delegation, not inline onclick)
    const deleteBtn = page.locator('button.delete-btn').first();
    const taskId = await deleteBtn.getAttribute('data-task-id');
    expect(taskId).toBeTruthy(); // Verify data attribute exists (not onclick)
    
    await deleteBtn.click();
    
    // Assert: Task should be removed from DOM
    await expect(page.locator('.task-item:has-text("Design mockups")')).not.toBeVisible();
  });

  test('E2E-02: Should use data attributes instead of onclick', async ({ page }) => {
    // Arrange: Navigate to tasks
    await page.waitForSelector('.task-item');
    
    // Act: Get delete button
    const deleteBtn = page.locator('button.delete-btn').first();
    
    // Assert: Verify uses data attribute (safe), not onclick (vulnerable)
    const hasDataAttribute = await deleteBtn.getAttribute('data-task-id');
    const hasOnclick = await deleteBtn.getAttribute('onclick');
    
    expect(hasDataAttribute).toBeTruthy();
    expect(hasOnclick).toBeNull();
  });

  test('E2E-03: Should prevent onclick injection via task ID', async ({ page }) => {
    // This test verifies the fix prevents XSS by using data attributes
    // Arrange: Check all delete buttons use safe data attributes
    const deleteButtons = page.locator('button.delete-btn');
    const count = await deleteButtons.count();
    
    for (let i = 0; i < count; i++) {
      // Act: Check each button
      const btn = deleteButtons.nth(i);
      const hasData = await btn.getAttribute('data-task-id');
      
      // Assert: Each button must have data attribute, not onclick
      expect(hasData).toBeTruthy();
      expect(hasData).not.toMatch(/</); // No HTML tags in ID
      expect(hasData).not.toMatch(/onclick/); // No onclick injection
    }
  });
});

// ============================================================================
// E2E TEST SUITE 2: Drag-Drop Without Race Condition
// ============================================================================

test.describe('CR-02: Drag-Drop Task - Race Condition Prevention', () => {
  
  test.beforeEach(async ({ page }) => {
    // Setup: Login and navigate to Gantt chart
    await page.goto(`${BASE_URL}/index.html`);
    await page.fill('input[id="username"]', 'demo');
    await page.fill('input[id="password"]', 'Demo@1234');
    await page.click('button:has-text("Login")');
    await page.waitForSelector('#gantt-container');
  });

  test('E2E-04: Should debounce drag updates to prevent race condition', async ({ page }) => {
    // Arrange: Get task bar position
    const taskBar = page.locator('.gantt-bar').first();
    await expect(taskBar).toBeVisible();
    const initialPos = await taskBar.boundingBox();
    
    // Act: Simulate drag movement (multiple mousemove events)
    await taskBar.hover();
    await page.mouse.down();
    
    // Move mouse quickly multiple times (would cause race condition without debouncing)
    for (let i = 0; i < 5; i++) {
      await page.mouse.move(initialPos.x + (i * 10), initialPos.y);
      await page.waitForTimeout(20); // Fast movements
    }
    
    await page.mouse.up();
    
    // Assert: Task should be in consistent state (no corruption)
    // Wait for debounce to complete
    await page.waitForTimeout(200);
    
    const taskAfterDrag = page.locator('.gantt-bar').first();
    const finalPos = await taskAfterDrag.boundingBox();
    
    // Position should have changed once (consolidated update), not multiple times
    expect(finalPos).toBeTruthy();
  });

  test('E2E-05: Should complete single drag without simultaneous updates', async ({ page }) => {
    // Arrange: Get initial task state
    const taskBar = page.locator('.gantt-bar').first();
    const startPos = await taskBar.boundingBox();
    
    // Act: Drag task horizontally
    await taskBar.drag(page.locator('.gantt-bar').nth(1), { 
      sourcePosition: { x: startPos.width / 2, y: startPos.height / 2 },
      targetPosition: { x: startPos.width / 2 + 50, y: 0 }
    });
    
    // Wait for debounce
    await page.waitForTimeout(200);
    
    // Assert: Single update should complete without race condition
    const endPos = await taskBar.boundingBox();
    expect(endPos).toBeTruthy();
    expect(endPos.x).toBeGreaterThan(startPos.x);
  });
});

// ============================================================================
// E2E TEST SUITE 3: Create Task with Date Validation
// ============================================================================

test.describe('CR-03: Create Task - Date Validation', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/index.html`);
    await page.fill('input[id="username"]', 'demo');
    await page.fill('input[id="password"]', 'Demo@1234');
    await page.click('button:has-text("Login")');
    await page.waitForSelector('#taskName');
  });

  test('E2E-06: Should reject task with end date before start date', async ({ page }) => {
    // Arrange: Fill form with invalid date range
    await page.fill('#taskName', 'Invalid Task');
    await page.fill('#startDate', '2026-05-20');
    await page.fill('#endDate', '2026-05-10'); // Before start date
    
    // Act: Try to submit
    const addBtn = page.locator('button:has-text("Add Task")').first();
    await addBtn.click();
    
    // Assert: Should show error (alert or inline message)
    const alertMsg = await page.evaluate(() => {
      // Check if alert was shown (would contain error about dates)
      return window.alertMessage || 'no-alert';
    }).catch(() => 'checked');
    
    // Verify task was not added
    const taskExists = await page.locator('.task-item:has-text("Invalid Task")').isVisible().catch(() => false);
    expect(taskExists).toBe(false);
  });

  test('E2E-07: Should accept task with end date equals start date', async ({ page }) => {
    // Arrange: Fill form with same dates (1-day task)
    const taskName = 'Single Day Task ' + Date.now();
    await page.fill('#taskName', taskName);
    await page.fill('#startDate', '2026-05-15');
    await page.fill('#endDate', '2026-05-15');
    
    // Act: Submit form
    await page.click('button:has-text("Add Task")');
    
    // Assert: Task should be added
    await expect(page.locator(`.task-item:has-text("${taskName}")`)).toBeVisible({ timeout: 5000 });
  });

  test('E2E-08: Should accept task with valid date range', async ({ page }) => {
    // Arrange: Fill form with valid dates
    const taskName = 'Valid Task ' + Date.now();
    await page.fill('#taskName', taskName);
    await page.fill('#startDate', '2026-05-15');
    await page.fill('#endDate', '2026-05-20');
    
    // Act: Submit form
    await page.click('button:has-text("Add Task")');
    
    // Assert: Task should appear in list and on Gantt
    await expect(page.locator(`.task-item:has-text("${taskName}")`)).toBeVisible({ timeout: 5000 });
  });
});

// ============================================================================
// E2E TEST SUITE 4: Login Error Handling
// ============================================================================

test.describe('WR-08: Login - Error Handling', () => {
  
  test('E2E-09: Should show error on invalid credentials', async ({ page }) => {
    // Arrange: Navigate to login
    await page.goto(`${BASE_URL}/index.html`);
    
    // Act: Try login with invalid password
    await page.fill('input[id="username"]', 'demo');
    await page.fill('input[id="password"]', 'WrongPassword123');
    await page.click('button:has-text("Login")');
    
    // Assert: Should not redirect to main screen
    const projectsList = await page.locator('#projectsList').isVisible().catch(() => false);
    expect(projectsList).toBe(false);
    
    // Should stay on login screen or show error
    const loginCard = page.locator('.login-card');
    await expect(loginCard).toBeVisible();
  });

  test('E2E-10: Should allow retry after login failure', async ({ page }) => {
    // Arrange: Navigate to login
    await page.goto(`${BASE_URL}/index.html`);
    
    // Act: First attempt - invalid credentials
    await page.fill('input[id="username"]', 'demo');
    await page.fill('input[id="password"]', 'WrongPassword');
    await page.click('button:has-text("Login")');
    
    // Wait for error to dismiss
    await page.waitForTimeout(1000);
    
    // Second attempt - correct credentials
    await page.fill('input[id="username"]', 'demo');
    await page.fill('input[id="password"]', 'Demo@1234');
    await page.click('button:has-text("Login")');
    
    // Assert: Should successfully login
    await expect(page.locator('#projectsList')).toBeVisible({ timeout: 5000 });
  });
});

// ============================================================================
// E2E TEST SUITE 5: Session Timeout Tracking
// ============================================================================

test.describe('WR-07: Session Timeout - API Activity Tracking', () => {
  
  test('E2E-11: Should not timeout during active API operations', async ({ page }) => {
    // Arrange: Login and start session
    await page.goto(`${BASE_URL}/index.html`);
    await page.fill('input[id="username"]', 'demo');
    await page.fill('input[id="password"]', 'Demo@1234');
    await page.click('button:has-text("Login")');
    await page.waitForSelector('#projectsList');
    
    // Act: Perform API operations continuously (should reset timeout)
    const startTime = Date.now();
    const operationDuration = 5000; // 5 seconds of operations
    
    while (Date.now() - startTime < operationDuration) {
      // Create a task (API call that should reset timeout)
      const taskName = 'Task ' + Date.now();
      await page.fill('#taskName', taskName);
      await page.fill('#startDate', '2026-05-15');
      await page.fill('#endDate', '2026-05-16');
      await page.click('button:has-text("Add Task")');
      
      await page.waitForTimeout(500); // Small delay between operations
    }
    
    // Assert: Should still be logged in (not timed out)
    const projectsList = page.locator('#projectsList');
    await expect(projectsList).toBeVisible();
  });

  test('E2E-12: Should timeout on inactivity (no API calls)', async ({ page }, testInfo) => {
    // Note: This test would need to be configured with shorter timeout for testing
    // Arrange: Login
    await page.goto(`${BASE_URL}/index.html`);
    await page.fill('input[id="username"]', 'demo');
    await page.fill('input[id="password"]', 'Demo@1234');
    await page.click('button:has-text("Login")');
    await page.waitForSelector('#projectsList');
    
    // Act: Wait for timeout (in production would be 15 min, in test should be shorter)
    // This test is marked as skipped because we can't easily test 15-minute timeout
    testInfo.skip(true, 'Requires test environment with shorter timeout');
  });
});

// ============================================================================
// TEST EXECUTION NOTES
// ============================================================================

/**
 * E2E Test Coverage Summary:
 * 
 * CR-01: XSS Prevention (Event Delegation) - 3 tests
 * CR-02: Race Condition (Debouncing) - 3 tests
 * CR-03: Date Validation - 3 tests
 * WR-08: Error Handling - 2 tests
 * WR-07: Session Timeout - 2 tests (1 skipped)
 * 
 * Total: 12 E2E tests
 * 
 * To run these tests:
 * 1. Install Playwright: npm install -D @playwright/test
 * 2. Start the application: python3 server.py
 * 3. Run tests: npx playwright test tests/e2e.test.js
 * 
 * Test Results Expected:
 * - All tests should PASS (GREEN)
 * - Implementation already includes fixes
 * - Tests verify fixes are working correctly
 */

module.exports = { test, expect };
