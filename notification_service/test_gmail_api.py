#!/usr/bin/env python
"""
Test Gmail API Email Service
Run this to test if Gmail API is working correctly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notification_service.settings')
django.setup()

from notifications.email_service import get_email_service


def test_gmail_api():
    """Test Gmail API email sending"""
    print("=" * 60)
    print("Gmail API Email Service Test")
    print("=" * 60)
    
    try:
        # Initialize email service
        print("\n📧 Initializing email service...")
        email_service = get_email_service()
        
        # Test connection
        print("\n🔌 Testing connection...")
        connection_result = email_service.test_connection()
        print(f"Connection test result: {connection_result}")
        
        if not connection_result.get('success'):
            print("\n❌ Connection failed. Please authenticate first.")
            print("Make sure credentials.json is in the notification_service folder.")
            return False
        
        print(f"✅ Connected as: {connection_result.get('email')}")
        
        # Get provider info
        print("\n📊 Provider information:")
        provider_info = email_service.get_provider_info()
        for key, value in provider_info.items():
            print(f"   {key}: {value}")
        
        # Prompt for test email
        print("\n" + "=" * 60)
        test_email = input("Enter email address to send test email (or press Enter to skip): ").strip()
        
        if not test_email:
            print("\n✅ Connection test passed! Email sending skipped.")
            return True
        
        # Test 1: Simple email
        print("\n" + "=" * 60)
        print("Test 1: Sending simple test email...")
        print("=" * 60)
        result1 = email_service.send_email(
            to=test_email,
            subject="Test Email from TTS Notification Service",
            body_text="This is a test email sent via Gmail API!",
            body_html="<h1>Test Email</h1><p>This is a test email sent via <strong>Gmail API</strong>!</p>"
        )
        print(f"\nResult: {result1}")
        
        if result1.get('success'):
            print("✅ Simple email sent successfully!")
        else:
            print(f"❌ Failed to send simple email: {result1.get('error')}")
        
        # Test 2: Password reset email
        print("\n" + "=" * 60)
        print("Test 2: Sending password reset email...")
        print("=" * 60)
        result2 = email_service.send_password_reset_email(
            to=test_email,
            reset_url="https://map-authentication-production.up.railway.app/reset-password?token=test123",
            user_name="Test User"
        )
        print(f"\nResult: {result2}")
        
        if result2.get('success'):
            print("✅ Password reset email sent successfully!")
        else:
            print(f"❌ Failed to send password reset email: {result2.get('error')}")
        
        # Test 3: Ticket notification
        print("\n" + "=" * 60)
        print("Test 3: Sending ticket notification email...")
        print("=" * 60)
        result3 = email_service.send_ticket_notification(
            to=test_email,
            ticket_id="12345",
            ticket_title="Cannot login to system",
            action="created",
            user_name="Test User",
            ticket_url="https://your-frontend.railway.app/tickets/12345"
        )
        print(f"\nResult: {result3}")
        
        if result3.get('success'):
            print("✅ Ticket notification sent successfully!")
        else:
            print(f"❌ Failed to send ticket notification: {result3.get('error')}")
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        success_count = sum([
            result1.get('success', False),
            result2.get('success', False),
            result3.get('success', False)
        ])
        print(f"✅ {success_count}/3 tests passed")
        
        if success_count == 3:
            print("\n🎉 All tests passed! Gmail API is working correctly!")
            return True
        else:
            print(f"\n⚠️  {3 - success_count} test(s) failed. Check errors above.")
            return False
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n🚀 Starting Gmail API test...\n")
    success = test_gmail_api()
    print("\n" + "=" * 60)
    if success:
        print("✅ Gmail API test completed successfully!")
    else:
        print("❌ Gmail API test failed. See errors above.")
    print("=" * 60 + "\n")
    sys.exit(0 if success else 1)
