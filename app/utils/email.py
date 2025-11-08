"""
Email notification utility with fail-safe sending logic

This module handles all email notifications for the book scraper.
Email failures are logged but never crash the application.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    to_email: Optional[str] = None
) -> bool:
    """
    Send an email using SMTP with fail-safe logic
    
    This function will NEVER raise exceptions - it only logs errors
    and returns False if sending fails.
    
    Args:
        subject: Email subject line
        body: Plain text email body
        html_body: Optional HTML version of email body
        to_email: Recipient email (defaults to NOTIFICATION_EMAIL from settings)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    # Check if email is enabled
    if not settings.email_enabled:
        logger.debug("Email notifications disabled (missing configuration)")
        return False
    
    try:
        # Use provided email or default from settings
        recipient = to_email or settings.NOTIFICATION_EMAIL
        
        if not recipient:
            logger.warning("No recipient email configured")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_USER_EMAIL
        msg['To'] = recipient
        msg['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        # Attach plain text body
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        # Attach HTML body if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        # Connect to SMTP server and send
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            
            server.login(settings.SMTP_USER_EMAIL, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully: '{subject}' to {recipient}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed - check SMTP_USER_EMAIL and SMTP_PASSWORD")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error while sending email: {e}")
        return False
    except ConnectionError as e:
        logger.error(f"Connection error while sending email: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}", exc_info=True)
        return False


def send_new_books_alert(books: List[Dict]) -> bool:
    """
    Send email alert for newly detected books
    
    Args:
        books: List of book dictionaries with 'name', 'category', 'price_incl_tax'
        
    Returns:
        True if email sent successfully, False otherwise
    """
    if not books:
        return False
    
    count = len(books)
    subject = f"📚 New Books Detected: {count} book{'s' if count > 1 else ''} added"
    
    # Plain text body
    body = f"New Books Detected\n"
    body += f"==================\n\n"
    body += f"Total: {count} new book{'s' if count > 1 else ''}\n"
    body += f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
    
    for book in books[:10]:  # Limit to first 10 books
        body += f"- {book.get('name', 'Unknown')}\n"
        body += f"  Category: {book.get('category', 'N/A')}\n"
        body += f"  Price: £{book.get('price_incl_tax', 0):.2f}\n\n"
    
    if count > 10:
        body += f"... and {count - 10} more\n\n"
    
    body += "---\n"
    body += "Book Scraper API\n"
    
    # HTML body
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">📚 New Books Detected</h2>
        <p><strong>Total:</strong> {count} new book{'s' if count > 1 else ''}</p>
        <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        <hr>
        <ul style="list-style-type: none; padding: 0;">
    """
    
    for book in books[:10]:
        html_body += f"""
            <li style="margin-bottom: 15px; padding: 10px; background-color: #f3f4f6; border-radius: 5px;">
                <strong style="color: #1f2937;">{book.get('name', 'Unknown')}</strong><br>
                <span style="color: #6b7280;">Category: {book.get('category', 'N/A')}</span><br>
                <span style="color: #059669; font-weight: bold;">Price: £{book.get('price_incl_tax', 0):.2f}</span>
            </li>
        """
    
    if count > 10:
        html_body += f"<li style='color: #6b7280;'>... and {count - 10} more</li>"
    
    html_body += """
        </ul>
        <hr>
        <p style="color: #6b7280; font-size: 12px;">Book Scraper API</p>
    </body>
    </html>
    """
    
    return send_email(subject, body, html_body)


def send_book_changes_alert(changes: List[Dict]) -> bool:
    """
    Send email alert for book changes (grouped by book)
    
    Args:
        changes: List of change dictionaries with book details
        Each change should have: book_name, field_changed, old_value, new_value, description
        
    Returns:
        True if email sent successfully, False otherwise
    """
    if not changes:
        return False
    
    # Group changes by book_name
    from collections import defaultdict
    books_with_changes = defaultdict(list)
    
    for change in changes:
        book_name = change.get('book_name', 'Unknown')
        books_with_changes[book_name].append(change)
    
    total_books = len(books_with_changes)
    total_changes = len(changes)
    
    subject = f"📝 Book Updates: {total_books} book{'s' if total_books > 1 else ''} changed"
    
    # Plain text body
    body = f"Book Updates Detected\n"
    body += f"=====================\n\n"
    body += f"Total: {total_books} book{'s' if total_books > 1 else ''} with {total_changes} change{'s' if total_changes > 1 else ''}\n"
    body += f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
    
    # Show first 15 books
    for idx, (book_name, book_changes) in enumerate(list(books_with_changes.items())[:15]):
        body += f"• {book_name}\n"
        for change in book_changes:
            field = change.get('field_changed', 'unknown')
            old_val = change.get('old_value', 'N/A')
            new_val = change.get('new_value', 'N/A')
            
            # Format values based on field type
            if 'price' in field:
                body += f"  → {field}: £{old_val} → £{new_val}\n"
            else:
                body += f"  → {field}: {old_val} → {new_val}\n"
        body += "\n"
    
    if total_books > 15:
        body += f"... and {total_books - 15} more books\n\n"
    
    body += "---\n"
    body += "Book Scraper API\n"
    
    # HTML body
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">📝 Book Updates Detected</h2>
        <p><strong>Total:</strong> {total_books} book{'s' if total_books > 1 else ''} with {total_changes} change{'s' if total_changes > 1 else ''}</p>
        <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        <hr>
        <div style="margin: 15px 0;">
    """
    
    for idx, (book_name, book_changes) in enumerate(list(books_with_changes.items())[:15]):
        html_body += f"""
            <div style="margin-bottom: 20px; padding: 15px; background-color: #f9fafb; border-left: 4px solid #2563eb; border-radius: 5px;">
                <strong style="color: #1f2937; font-size: 16px;">• {book_name}</strong>
                <ul style="margin: 10px 0 0 0; padding-left: 20px; list-style-type: none;">
        """
        
        for change in book_changes:
            field = change.get('field_changed', 'unknown')
            old_val = change.get('old_value', 'N/A')
            new_val = change.get('new_value', 'N/A')
            
            # Determine color based on change type
            color = "#6b7280"
            if 'price' in field:
                if isinstance(new_val, (int, float)) and isinstance(old_val, (int, float)):
                    color = "#dc2626" if new_val > old_val else "#059669"
                old_val_str = f"£{old_val:.2f}" if isinstance(old_val, (int, float)) else old_val
                new_val_str = f"£{new_val:.2f}" if isinstance(new_val, (int, float)) else new_val
            else:
                old_val_str = str(old_val)
                new_val_str = str(new_val)
            
            html_body += f"""
                    <li style="color: {color}; margin: 5px 0;">
                        <strong>{field}:</strong> {old_val_str} → {new_val_str}
                    </li>
            """
        
        html_body += """
                </ul>
            </div>
        """
    
    if total_books > 15:
        html_body += f"<p style='color: #6b7280; text-align: center;'>... and {total_books - 15} more books with changes</p>"
    
    html_body += """
        </div>
        <hr>
        <p style="color: #6b7280; font-size: 12px;">Book Scraper API</p>
    </body>
    </html>
    """
    
    return send_email(subject, body, html_body)


def send_crawl_error_alert(error_message: str, details: Optional[Dict] = None) -> bool:
    """
    Send email alert for crawl failures
    
    Args:
        error_message: Main error message
        details: Optional dictionary with error details
        
    Returns:
        True if email sent successfully, False otherwise
    """
    subject = "⚠️ Crawl Error: Book Scraper Alert"
    
    # Plain text body
    body = f"Crawl Error Detected\n"
    body += f"===================\n\n"
    body += f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
    body += f"Error: {error_message}\n\n"
    
    if details:
        body += "Details:\n"
        for key, value in details.items():
            body += f"  {key}: {value}\n"
        body += "\n"
    
    body += "Please check the application logs for more information.\n\n"
    body += "---\n"
    body += "Book Scraper API\n"
    
    # HTML body
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #dc2626;">⚠️ Crawl Error Detected</h2>
        <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        <hr>
        <div style="background-color: #fef2f2; padding: 15px; border-left: 4px solid #dc2626; margin: 15px 0;">
            <p style="margin: 0; color: #991b1b;"><strong>Error:</strong> {error_message}</p>
        </div>
    """
    
    if details:
        html_body += "<h3>Details:</h3><ul>"
        for key, value in details.items():
            html_body += f"<li><strong>{key}:</strong> {value}</li>"
        html_body += "</ul>"
    
    html_body += """
        <p style="color: #6b7280;">Please check the application logs for more information.</p>
        <hr>
        <p style="color: #6b7280; font-size: 12px;">Book Scraper API</p>
    </body>
    </html>
    """
    
    return send_email(subject, body, html_body)


def send_daily_summary(summary: Dict) -> bool:
    """
    Send daily crawl summary email
    
    Args:
        summary: Dictionary with crawl statistics
        
    Returns:
        True if email sent successfully, False otherwise
    """
    subject = f"📊 Daily Crawl Summary - {datetime.utcnow().strftime('%Y-%m-%d')}"
    
    # Plain text body
    body = f"Daily Crawl Summary\n"
    body += f"==================\n\n"
    body += f"Date: {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"
    body += f"Statistics:\n"
    body += f"  Total Scraped: {summary.get('total_scraped', 0)}\n"
    body += f"  New Books: {summary.get('inserted', 0)}\n"
    body += f"  Updated Books: {summary.get('updated', 0)}\n"
    body += f"  Changes Detected: {summary.get('total_changes_detected', 0)}\n"
    body += f"  Failed: {summary.get('failed', 0)}\n"
    body += f"  Duration: {summary.get('duration_seconds', 0):.2f} seconds\n\n"
    
    if summary.get('error'):
        body += f"Error: {summary['error']}\n\n"
    
    body += "---\n"
    body += "Book Scraper API\n"
    
    # HTML body
    status_color = "#059669" if summary.get('failed', 0) == 0 else "#dc2626"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">📊 Daily Crawl Summary</h2>
        <p><strong>Date:</strong> {datetime.utcnow().strftime('%Y-%m-%d')}</p>
        <hr>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Total Scraped:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right;">{summary.get('total_scraped', 0)}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>New Books:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right; color: #059669;">{summary.get('inserted', 0)}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Updated Books:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right;">{summary.get('updated', 0)}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Changes Detected:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right;">{summary.get('total_changes_detected', 0)}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Failed:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right; color: {status_color};">{summary.get('failed', 0)}</td>
            </tr>
            <tr>
                <td style="padding: 10px;"><strong>Duration:</strong></td>
                <td style="padding: 10px; text-align: right;">{summary.get('duration_seconds', 0):.2f}s</td>
            </tr>
        </table>
    """
    
    if summary.get('error'):
        html_body += f"""
        <div style="background-color: #fef2f2; padding: 15px; border-left: 4px solid #dc2626; margin: 15px 0;">
            <p style="margin: 0; color: #991b1b;"><strong>Error:</strong> {summary['error']}</p>
        </div>
        """
    
    html_body += """
        <hr>
        <p style="color: #6b7280; font-size: 12px;">Book Scraper API</p>
    </body>
    </html>
    """
    
    return send_email(subject, body, html_body)

