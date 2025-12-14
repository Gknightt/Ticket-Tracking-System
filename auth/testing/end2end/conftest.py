"""
Pytest configuration for Playwright end-to-end tests.

This file configures pytest-playwright with custom settings.
"""

import pytest
from playwright.sync_api import Page, Browser, BrowserContext


# Configure pytest-playwright
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "login: marks tests that require login"
    )
    config.addinivalue_line(
        "markers", "logout: marks tests for logout functionality"
    )


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context with custom settings"""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    """Create a new page for each test with custom settings"""
    page = context.new_page()
    
    # Set default timeout for all operations
    page.set_default_timeout(30000)  # 30 seconds
    page.set_default_navigation_timeout(30000)
    
    yield page
    
    # Cleanup after test
    page.close()


@pytest.fixture
def authenticated_page(page: Page) -> Page:
    """Fixture that provides an authenticated page (logged in user)"""
    import os
    
    base_url = os.environ.get("AUTH_BASE_URL", "http://localhost:8000")
    test_email = os.environ.get("TEST_USER_EMAIL", "admin@test.com")
    test_password = os.environ.get("TEST_USER_PASSWORD", "admin123")
    
    # Navigate to login
    page.goto(f"{base_url}/login/")
    
    # Fill credentials
    page.fill("#email", test_email)
    page.fill("#password", test_password)
    
    # Submit
    page.locator("#loginButton").click()
    
    # Wait for login to complete
    page.wait_for_timeout(3000)
    
    yield page


@pytest.fixture
def hdts_authenticated_page(page: Page) -> Page:
    """Fixture that provides an authenticated HDTS employee page"""
    import os
    
    base_url = os.environ.get("AUTH_BASE_URL", "http://localhost:8000")
    test_email = os.environ.get("HDTS_TEST_EMAIL", "employee@test.com")
    test_password = os.environ.get("HDTS_TEST_PASSWORD", "employee123")
    
    # Navigate to HDTS login
    page.goto(f"{base_url}/hdts/login/")
    
    # Fill credentials
    page.fill("#id_email", test_email)
    page.fill("#id_password", test_password)
    
    # Submit
    page.locator("#loginButton").click()
    
    # Wait for login to complete
    page.wait_for_timeout(3000)
    
    yield page
