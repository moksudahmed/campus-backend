import smtplib
import secrets
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict
import os

class PasswordResetService2222:
    """Service for handling password reset email functionality"""
    
    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str):
        """
        Initialize the password reset service
        
        Args:
            smtp_server: SMTP server address (e.g., 'smtp.gmail.com')
            smtp_port: SMTP port (587 for TLS, 465 for SSL)
            sender_email: Email address to send from
            sender_password: Email account password or app password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.base_url = os.getenv('APP_BASE_URL', 'http://localhost:3000')
        self.reset_tokens: Dict = {}
    
    def generate_reset_token(self, user_email: str) -> tuple[str, datetime]:
        """
        Generate a secure password reset token
        
        Args:
            user_email: User's email address
            
        Returns:
            Tuple of (token, expiration_datetime)
        """
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        
        # Set expiration (1 hour from now)
        expiration = datetime.now() + timedelta(hours=1)
        
        # In production, save this token to database with user_email and expiration
        # Example: save_to_db(user_email, token, expiration)
        
        return token, expiration
    
    def create_reset_email(self, recipient_email: str, recipient_name: str, reset_token: str) -> MIMEMultipart:
        """
        Create the password reset email
        
        Args:
            recipient_email: Recipient's email address
            recipient_name: Recipient's name
            reset_token: Password reset token
            
        Returns:
            MIMEMultipart email message
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = "Password Reset Request"
        message["From"] = self.sender_email
        message["To"] = recipient_email
        
        # Create reset link
        reset_link = f"{self.base_url}/reset-password?token={reset_token}"
        
        # Plain text version
        text = f"""
Hello {recipient_name},

We received a request to reset your password. Click the link below to reset your password:

{reset_link}

This link will expire in 1 hour.

If you didn't request a password reset, please ignore this email or contact support if you have concerns.

Best regards,
Your App Team
        """
        
        # HTML version
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #4CAF50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            margin: 20px 0;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 20px;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
        .warning {{
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            margin-top: 20px;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello {recipient_name},</p>
            
            <p>We received a request to reset your password. Click the button below to reset your password:</p>
            
            <center>
                <a href="{reset_link}" class="button">Reset Password</a>
            </center>
            
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #0066cc;">{reset_link}</p>
            
            <div class="warning">
                <strong>⏰ Important:</strong> This link will expire in 1 hour for security reasons.
            </div>
            
            <p>If you didn't request a password reset, please ignore this email or contact our support team if you have concerns.</p>
            
            <p>Best regards,<br>Your App Team</p>
        </div>
        <div class="footer">
            <p>This is an automated message, please do not reply to this email.</p>
            <p>&copy; 2024 Your Company. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Attach both versions
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)
        
        return message
    
    def send_reset_email(self, recipient_email: str, recipient_name: str) -> bool:
        """
        Send password reset email to user
        
        Args:
            recipient_email: User's email address
            recipient_name: User's name
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Generate reset token
            reset_token, expiration = self.generate_reset_token(recipient_email)
            
            # Create email message
            message = self.create_reset_email(recipient_email, recipient_name, reset_token)
           
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Secure the connection
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
                
            
            print(f"✓ Password reset email sent successfully to {recipient_email}")
            print(f"Token expires at: {expiration.strftime('%Y-%m-%d %H:%M:%S')}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print("✗ Authentication failed. Check your email and password.")
            return False
        except smtplib.SMTPException as e:
            print(f"✗ SMTP error occurred: {str(e)}")
            return False
        except Exception as e:
            print(f"✗ Error sending email: {str(e)}")
            return False

    def verify_token(self, token: str) -> Optional[str]:
        """Verify reset token validity"""
        if token not in self.reset_tokens:
            return None
        
        token_data = self.reset_tokens[token]
        
        if token_data['used']:
            return None
        
        if datetime.now() > token_data['expiry']:
            return None
        
        return token_data['email']