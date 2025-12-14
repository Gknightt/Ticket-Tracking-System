"""
End-to-End Tests for Auth Service using Playwright

Prerequisites:
    pip install pytest-playwright
    playwright install

Run tests:
    pytest testing/end2end/test.py -v
    pytest testing/end2end/test.py -v -k "test_login"  # Run specific test
    pytest testing/end2end/test.py -v --headed  # Run with browser visible

Environment Variables:
    AUTH_BASE_URL - Base URL of auth service (default: http://127.0.0.1:8000)
    TEST_USER_EMAIL - Test user email
    TEST_USER_PASSWORD - Test user password
"""

import os
import re
import pytest
from playwright.sync_api import Page, expect, sync_playwright

# Configuration
BASE_URL = os.environ.get("AUTH_BASE_URL", "http://127.0.0.1:8000")
TEST_USER_EMAIL = os.environ.get("TEST_USER_EMAIL", "admin@test.com")
TEST_USER_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "admin123")

# HDTS Employee test credentials
HDTS_TEST_EMAIL = os.environ.get("HDTS_TEST_EMAIL", "employee@test.com")
HDTS_TEST_PASSWORD = os.environ.get("HDTS_TEST_PASSWORD", "employee123")


class TestStaffLogin:
    """Tests for staff login page (/staff/login/ or /api/v1/users/login/)"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup before each test"""
        self.page = page
        self.login_url = f"{BASE_URL}/staff/login/"
    
    def test_login_page_loads(self):
        """Test that the login page loads correctly"""
        self.page.goto(self.login_url)
        
        # Check page title
        expect(self.page).to_have_title(re.compile(r"Sign In", re.IGNORECASE))
        
        # Check form elements exist (staff login uses #email, #password)
        expect(self.page.locator("#email")).to_be_visible()
        expect(self.page.locator("#password")).to_be_visible()
        expect(self.page.locator("#loginButton")).to_be_visible()
    
    def test_login_empty_credentials_shows_error(self):
        """Test that submitting empty form shows validation error"""
        self.page.goto(self.login_url)
        
        # Click login without entering credentials
        self.page.locator("#loginButton").click()
        
        # Should show toast notification with error
        self.page.wait_for_timeout(1000)
        toast = self.page.locator(".toast-container")
        expect(toast).to_be_visible(timeout=5000)
    
    def test_login_invalid_credentials_shows_error(self):
        """Test that invalid credentials show error message"""
        self.page.goto(self.login_url)
        
        # Enter invalid credentials
        self.page.fill("#email", "invalid@example.com")
        self.page.fill("#password", "wrongpassword")
        
        # Submit form
        self.page.locator("#loginButton").click()
        
        # Wait for response and check for error toast
        self.page.wait_for_timeout(2000)
        
        # Should still be on login page or show error
        toast = self.page.locator(".toast-container")
        expect(toast).to_be_visible(timeout=5000)
    
    @pytest.mark.skipif(
        os.environ.get("TEST_USER_EMAIL", "admin@test.com") == "admin@test.com",
        reason="Requires real test credentials. Set TEST_USER_EMAIL and TEST_USER_PASSWORD env vars."
    )
    def test_login_success(self):
        """Test successful login with valid credentials"""
        self.page.goto(self.login_url)
        
        # Enter valid credentials
        self.page.fill("#email", TEST_USER_EMAIL)
        self.page.fill("#password", TEST_USER_PASSWORD)
        
        # Submit form
        self.page.locator("#loginButton").click()
        
        # Wait for redirect (should redirect away from login page on success)
        self.page.wait_for_timeout(3000)
        
        # Check cookies are set
        cookies = self.page.context.cookies()
        cookie_names = [c["name"] for c in cookies]
        
        # Should have access_token cookie after successful login
        # Note: This may vary based on 2FA configuration
        assert "access_token" in cookie_names or self.page.url != self.login_url
    
    def test_login_remember_me_checkbox(self):
        """Test that remember me checkbox is present and functional"""
        self.page.goto(self.login_url)
        
        # Check remember me checkbox exists
        remember_me = self.page.locator("#rememberMe")
        expect(remember_me).to_be_visible()
        
        # Check it's unchecked by default
        expect(remember_me).not_to_be_checked()
        
        # Check it
        remember_me.check()
        expect(remember_me).to_be_checked()


class TestStaffLogout:
    """Tests for staff logout functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup before each test - login first"""
        self.page = page
        self.login_url = f"{BASE_URL}/staff/login/"
        self.logout_url = f"{BASE_URL}/logout/"
    
    def _login(self):
        """Helper to perform login"""
        self.page.goto(self.login_url)
        self.page.fill("#email", TEST_USER_EMAIL)
        self.page.fill("#password", TEST_USER_PASSWORD)
        self.page.locator("#loginButton").click()
        self.page.wait_for_timeout(3000)
    
    def test_logout_clears_cookies(self):
        """Test that logout clears authentication cookies"""
        # First login
        self._login()
        
        # Get cookies before logout
        cookies_before = self.page.context.cookies()
        
        # Perform logout
        self.page.goto(self.logout_url)
        self.page.wait_for_timeout(1000)
        
        # Get cookies after logout
        cookies_after = self.page.context.cookies()
        cookie_names_after = [c["name"] for c in cookies_after]
        
        # access_token should be cleared
        assert "access_token" not in cookie_names_after or \
               next((c for c in cookies_after if c["name"] == "access_token"), {}).get("value", "") == ""
    
    def test_logout_redirects_to_login(self):
        """Test that logout redirects to login page"""
        # First login
        self._login()
        
        # Perform logout
        self.page.goto(self.logout_url)
        self.page.wait_for_timeout(2000)
        
        # Should be redirected to login page
        expect(self.page).to_have_url(re.compile(r"/login"))


class TestHDTSEmployeeLogin:
    """Tests for HDTS employee login page (/login/ or /hdts/login/)"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup before each test"""
        self.page = page
        # /login/ redirects to HDTS login
        self.login_url = f"{BASE_URL}/login/"
    
    def test_hdts_login_page_loads(self):
        """Test that the HDTS login page loads correctly"""
        self.page.goto(self.login_url)
        
        # Check page title
        expect(self.page).to_have_title(re.compile(r"Employee Login|HDTS", re.IGNORECASE))
        
        # Check form elements exist (HDTS uses #id_email, #id_password)
        expect(self.page.locator("#id_email")).to_be_visible()
        expect(self.page.locator("#id_password")).to_be_visible()
        expect(self.page.locator("#loginButton")).to_be_visible()
    
    def test_hdts_login_empty_credentials_shows_error(self):
        """Test that submitting empty form shows validation error"""
        self.page.goto(self.login_url)
        
        # Click login without entering credentials
        self.page.locator("#loginButton").click()
        
        # Should show toast notification with error
        self.page.wait_for_timeout(1000)
        toast = self.page.locator(".toast-container")
        expect(toast).to_be_visible(timeout=5000)
    
    @pytest.mark.skipif(
        os.environ.get("HDTS_TEST_EMAIL", "employee@test.com") == "employee@test.com",
        reason="Requires real test credentials. Set HDTS_TEST_EMAIL and HDTS_TEST_PASSWORD env vars."
    )
    def test_hdts_login_success(self):
        """Test successful HDTS employee login"""
        self.page.goto(self.login_url)
        
        # Enter valid credentials
        self.page.fill("#id_email", HDTS_TEST_EMAIL)
        self.page.fill("#id_password", HDTS_TEST_PASSWORD)
        
        # Submit form
        self.page.locator("#loginButton").click()
        
        # Wait for response
        self.page.wait_for_timeout(3000)
        
        # Check for successful login (redirect or token)
        cookies = self.page.context.cookies()
        cookie_names = [c["name"] for c in cookies]
        
        # Should have access_token or be redirected
        assert "access_token" in cookie_names or self.page.url != self.login_url


class TestRecaptchaBypass:
    """Tests to verify reCAPTCHA bypass when RECAPTCHA_ENABLED=False"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup before each test"""
        self.page = page
        self.staff_login_url = f"{BASE_URL}/staff/login/"
        self.hdts_login_url = f"{BASE_URL}/login/"
    
    def test_staff_login_no_recaptcha_element_when_disabled(self):
        """Test that reCAPTCHA element is not present when disabled"""
        self.page.goto(self.staff_login_url)
        
        # Check if RECAPTCHA_ENABLED is false by checking window variable
        recaptcha_enabled = self.page.evaluate("window.RECAPTCHA_ENABLED")
        
        if not recaptcha_enabled:
            # reCAPTCHA div should not be visible
            recaptcha_div = self.page.locator(".g-recaptcha")
            expect(recaptcha_div).to_have_count(0)
        else:
            # reCAPTCHA should be visible
            recaptcha_div = self.page.locator(".g-recaptcha")
            expect(recaptcha_div).to_be_visible()
    
    def test_hdts_login_no_recaptcha_element_when_disabled(self):
        """Test that reCAPTCHA element is not present on HDTS login when disabled"""
        self.page.goto(self.hdts_login_url)
        
        # Check if RECAPTCHA_ENABLED is false by checking window variable
        recaptcha_enabled = self.page.evaluate("window.RECAPTCHA_ENABLED")
        
        if not recaptcha_enabled:
            # reCAPTCHA div should not be visible
            recaptcha_div = self.page.locator(".g-recaptcha")
            expect(recaptcha_div).to_have_count(0)
        else:
            # reCAPTCHA should be visible
            recaptcha_div = self.page.locator(".g-recaptcha")
            expect(recaptcha_div).to_be_visible()
    
    def test_login_works_without_recaptcha_when_disabled(self):
        """Test that login works without reCAPTCHA when it's disabled"""
        self.page.goto(self.staff_login_url)
        
        # Check if reCAPTCHA is disabled
        recaptcha_enabled = self.page.evaluate("window.RECAPTCHA_ENABLED")
        
        if not recaptcha_enabled:
            # Should be able to login without reCAPTCHA
            self.page.fill("#email", TEST_USER_EMAIL)
            self.page.fill("#password", TEST_USER_PASSWORD)
            self.page.locator("#loginButton").click()
            
            # Wait for response
            self.page.wait_for_timeout(3000)
            
            # Should not show reCAPTCHA required warning toast
            # Check for warning toast with reCAPTCHA text (NOT raw page content which includes JS source)
            recaptcha_warning_toast = self.page.locator(".toast.warning:has-text('reCAPTCHA')")
            expect(recaptcha_warning_toast).to_have_count(0)


# Standalone test runner
def run_tests():
    """Run tests using pytest programmatically"""
    pytest.main([__file__, "-v", "--headed"])


if __name__ == "__main__":
    run_tests()
