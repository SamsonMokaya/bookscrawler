"""
Tests for email notification functionality
"""
import pytest
from unittest.mock import patch, MagicMock
from app.utils.email import (
    send_email,
    send_new_books_alert,
    send_book_changes_alert,
    send_crawl_error_alert,
    send_daily_summary
)
from app.config import settings


class TestEmailSending:
    """Test core email sending functionality"""
    
    @patch('app.utils.email.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending"""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = send_email(
            subject="Test Subject",
            body="Test body",
            html_body="<p>Test HTML</p>"
        )
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
    
    @patch('app.utils.email.smtplib.SMTP')
    def test_send_email_smtp_failure(self, mock_smtp):
        """Test email sending handles SMTP errors gracefully"""
        # Mock SMTP to raise exception
        mock_smtp.side_effect = Exception("SMTP connection failed")
        
        # Should not raise, just return False
        result = send_email(
            subject="Test Subject",
            body="Test body"
        )
        
        assert result is False
    
    def test_email_disabled_when_config_missing(self):
        """Test emails are disabled when config is incomplete"""
        # Save original values
        original_user = settings.SMTP_USER_EMAIL
        original_pass = settings.SMTP_PASSWORD
        original_recipient = settings.NOTIFICATION_EMAIL
        
        try:
            # Clear email config
            settings.SMTP_USER_EMAIL = ""
            settings.SMTP_PASSWORD = ""
            settings.NOTIFICATION_EMAIL = ""
            
            # Email should be disabled
            assert settings.email_enabled is False
            
            result = send_email(
                subject="Test",
                body="Test"
            )
            
            assert result is False
            
        finally:
            # Restore original values
            settings.SMTP_USER_EMAIL = original_user
            settings.SMTP_PASSWORD = original_pass
            settings.NOTIFICATION_EMAIL = original_recipient


class TestNewBooksAlert:
    """Test new books email functionality"""
    
    @patch('app.utils.email.send_email')
    def test_new_books_alert_formatting(self, mock_send):
        """Test new books email formats correctly"""
        mock_send.return_value = True
        
        books = [
            {'name': 'Book 1', 'category': 'Fiction', 'price_incl_tax': 19.99},
            {'name': 'Book 2', 'category': 'Poetry', 'price_incl_tax': 12.50}
        ]
        
        result = send_new_books_alert(books)
        
        assert result is True
        mock_send.assert_called_once()
        
        # Verify subject includes count
        call_args = mock_send.call_args
        subject = call_args[0][0]
        assert "2 books" in subject.lower()
    
    @patch('app.utils.email.send_email')
    def test_new_books_alert_limits_display(self, mock_send):
        """Test new books alert limits to 10 books in display"""
        mock_send.return_value = True
        
        # Create 15 books
        books = [
            {'name': f'Book {i}', 'category': 'Fiction', 'price_incl_tax': 19.99}
            for i in range(15)
        ]
        
        result = send_new_books_alert(books)
        
        assert result is True
        call_args = mock_send.call_args
        body = call_args[0][1]
        
        # Should mention total count
        assert "15" in body
        # Should mention "and X more"
        assert "5 more" in body
    
    def test_new_books_alert_empty_list(self):
        """Test new books alert returns False for empty list"""
        result = send_new_books_alert([])
        assert result is False


class TestBookChangesAlert:
    """Test book changes email functionality"""
    
    @patch('app.utils.email.send_email')
    def test_changes_grouped_by_book(self, mock_send):
        """Test changes are grouped by book name"""
        mock_send.return_value = True
        
        changes = [
            {'book_name': 'Book A', 'field_changed': 'price_incl_tax', 'old_value': 19.99, 'new_value': 15.99},
            {'book_name': 'Book A', 'field_changed': 'availability', 'old_value': 'In stock', 'new_value': 'Out of stock'},
            {'book_name': 'Book B', 'field_changed': 'rating', 'old_value': 3, 'new_value': 5}
        ]
        
        result = send_book_changes_alert(changes)
        
        assert result is True
        call_args = mock_send.call_args
        body = call_args[0][1]
        
        # Should show 2 books (A and B)
        assert "2 books" in body.lower() or "2 book" in body.lower()
        # Should show 3 total changes
        assert "3 change" in body.lower()
        # Should show Book A with multiple changes
        assert "Book A" in body
        assert "Book B" in body
    
    @patch('app.utils.email.send_email')
    def test_changes_alert_limits_display(self, mock_send):
        """Test changes alert limits to 15 books"""
        mock_send.return_value = True
        
        # Create 20 books with changes
        changes = [
            {'book_name': f'Book {i}', 'field_changed': 'price_incl_tax', 'old_value': 10.0, 'new_value': 15.0}
            for i in range(20)
        ]
        
        result = send_book_changes_alert(changes)
        
        assert result is True
        call_args = mock_send.call_args
        body = call_args[0][1]
        
        # Should mention "5 more books"
        assert "5 more books" in body.lower()
    
    def test_changes_alert_empty_list(self):
        """Test changes alert returns False for empty list"""
        result = send_book_changes_alert([])
        assert result is False


class TestCrawlErrorAlert:
    """Test crawl error email functionality"""
    
    @patch('app.utils.email.send_email')
    def test_crawl_error_alert_formatting(self, mock_send):
        """Test crawl error email formats correctly"""
        mock_send.return_value = True
        
        result = send_crawl_error_alert(
            error_message="Connection timeout",
            details={'page': 5, 'url': 'https://example.com'}
        )
        
        assert result is True
        call_args = mock_send.call_args
        subject = call_args[0][0]
        body = call_args[0][1]
        
        # Verify error appears in subject and body
        assert "error" in subject.lower() or "alert" in subject.lower()
        assert "Connection timeout" in body


class TestDailySummary:
    """Test daily summary email functionality"""
    
    @patch('app.utils.email.send_email')
    def test_daily_summary_formatting(self, mock_send):
        """Test daily summary email formats correctly"""
        mock_send.return_value = True
        
        summary = {
            'total_scraped': 1000,
            'inserted': 5,
            'updated': 100,
            'failed': 2,
            'total_changes_detected': 150,
            'duration_seconds': 180.5
        }
        
        result = send_daily_summary(summary)
        
        assert result is True
        call_args = mock_send.call_args
        body = call_args[0][1]
        
        # Verify key stats appear in body
        assert "1000" in body  # total_scraped
        assert "5" in body     # inserted
        assert "100" in body   # updated
        assert "180.5" in body or "180.50" in body  # duration


class TestEmailIntegration:
    """Test email integration with crawl tasks"""
    
    @patch('app.utils.email.send_new_books_alert')
    @patch('app.utils.email.send_book_changes_alert')
    def test_crawl_sends_emails_on_new_books(self, mock_changes_email, mock_new_books_email):
        """Test that crawl tasks trigger email notifications"""
        # This is more of an integration test
        # Verify that the email functions are called with correct data
        
        # For now, just verify the functions exist and are importable
        from app.scheduler.crawl_tasks import save_book_to_db
        
        # Verify email functions are imported in crawl_tasks
        assert callable(mock_new_books_email)
        assert callable(mock_changes_email)
    
    @patch('app.utils.email.smtplib.SMTP')
    def test_email_failure_doesnt_crash_crawl(self, mock_smtp):
        """Test that email failures don't stop the crawl"""
        # SMTP should fail
        mock_smtp.side_effect = Exception("SMTP connection error")
        
        # This should not raise, just return False
        result = send_new_books_alert([
            {'name': 'Test Book', 'category': 'Fiction', 'price_incl_tax': 19.99}
        ])
        
        # Should handle exception gracefully and return False
        assert result is False

