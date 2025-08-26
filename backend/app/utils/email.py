"""
Email utilities for future use (notifications, password reset, etc.).
"""
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


async def send_email(
    to: List[str],
    subject: str,
    body: str,
    html_body: Optional[str] = None
):
    """
    Send email (placeholder for future implementation).
    
    Args:
        to: List of recipient email addresses.
        subject: Email subject.
        body: Plain text email body.
        html_body: Optional HTML email body.
        
    Note:
        This is a placeholder implementation for future email functionality.
        Could integrate with services like SendGrid, Amazon SES, or SMTP.
    """
    logger.info(f"Email would be sent to {to} with subject: {subject}")
    logger.debug(f"Email body: {body}")
    
    # TODO: Implement actual email sending
    # This could use:
    # - SMTP with smtplib
    # - SendGrid API
    # - Amazon SES
    # - Other email services
    
    return {"status": "queued", "recipients": to}


async def send_welcome_email(user_email: str, user_name: str):
    """
    Send welcome email to new users.
    
    Args:
        user_email: User's email address.
        user_name: User's display name.
    """
    subject = "Welcome to GoodEats!"
    body = f"""
    Hi {user_name},
    
    Welcome to GoodEats Recipe PWA! 
    
    You can now:
    - Create and share your favorite recipes
    - Discover new recipes from the community
    - Vote on recipes you've tried
    - Generate shopping lists from your favorite recipes
    
    Get cooking!
    
    The GoodEats Team
    """
    
    await send_email([user_email], subject, body)


async def send_password_reset_email(user_email: str, reset_token: str):
    """
    Send password reset email.
    
    Args:
        user_email: User's email address.
        reset_token: Password reset token.
    """
    subject = "Reset Your GoodEats Password"
    body = f"""
    You requested a password reset for your GoodEats account.
    
    Click the link below to reset your password:
    https://goodEats.com/reset-password?token={reset_token}
    
    If you didn't request this reset, please ignore this email.
    
    The GoodEats Team
    """
    
    await send_email([user_email], subject, body)