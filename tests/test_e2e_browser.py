"""Browser checks for the OpenMinds operator workspace (requires running API and UI)."""
import pytest
from playwright.async_api import async_playwright


@pytest.mark.asyncio
async def test_operator_console_navigation_and_empty_state():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        await page.goto("http://localhost:3000", wait_until="domcontentloaded")
        await page.get_by_role("heading", name="Team command board").wait_for()
        assert await page.get_by_role("region", name="Kanban board").count() == 1
        assert await page.get_by_role("button", name="New task").count() == 1
        await page.get_by_role("button", name="Runner fleet").click()
        await page.get_by_role("heading", name="Execution fleet").wait_for()
        await page.get_by_role("button", name="Evidence").click()
        await page.get_by_text("Approval controls unavailable").wait_for()
        assert await page.get_by_role("button", name="Approval controls unavailable").is_disabled()
        await page.get_by_role("button", name="Node flows").click()
        await page.get_by_role("heading", name="Node flows").wait_for()
        await page.get_by_role("button", name="Diagnostics").click()
        await page.get_by_role("heading", name="Control-plane diagnostics").wait_for()
        await page.get_by_role("button", name="Assets").click()
        await page.get_by_role("heading", name="Workspace assets").wait_for()
        await page.get_by_role("button", name="Terminal").click()
        assert await page.get_by_role("button", name="Connect terminal unavailable").is_disabled()
        assert errors == []
        await browser.close()


@pytest.mark.asyncio
async def test_create_issue_is_persisted_and_displayed():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://localhost:3000", wait_until="domcontentloaded")
        await page.get_by_role("heading", name="Team command board").wait_for()
        await page.get_by_role("button", name="New task").click()
        dialog = page.get_by_role("dialog", name="Create a task")
        await dialog.get_by_placeholder("Describe the work to be done").fill("Browser verified issue")
        await dialog.get_by_role("button", name="Create task").click()
        await dialog.wait_for(state="hidden")
        await page.get_by_role("heading", name="Browser verified issue").wait_for()
        await page.reload(wait_until="domcontentloaded")
        await page.get_by_role("heading", name="Browser verified issue").wait_for()
        await browser.close()
