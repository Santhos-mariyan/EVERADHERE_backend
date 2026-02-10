import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from typing import Optional

class EmailService:
    """Service for sending emails via SMTP"""
    
    @staticmethod
    def send_otp_email(email: str, otp_code: str, purpose: str = "email_verification") -> bool:
        """
        Send OTP to email
        
        Args:
            email: Recipient email address
            otp_code: 6-digit OTP code
            purpose: 'email_verification' or 'password_reset'
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            print(f"\n{'='*60}")
            print(f"📧 EMAIL SERVICE - Preparing to send OTP")
            print(f"{'='*60}")
            print(f"Recipient: {email}")
            print(f"OTP Code: {otp_code}")
            print(f"Purpose: {purpose}")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Your EverAdhere Verification Code"
            # Use authenticated SMTP user as From to avoid provider rejections
            msg['From'] = f"{settings.EMAILS_FROM_NAME} <{settings.SMTP_USER}>"
            msg['To'] = email
            
            print(f"✅ Message headers set")
            print(f"   From: {settings.EMAILS_FROM_EMAIL}")
            print(f"   To: {email}")
            
            # Email body
            if purpose == "email_verification":
                subject_line = "Email Verification"
                title = "Verify Your Email"
                message_text = "Please verify your email address to complete your registration"
            else:  # password_reset
                subject_line = "Password Reset"
                title = "Reset Your Password"
                message_text = "Please use the code below to reset your password"
            
            # HTML content
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h2 style="color: #333; text-align: center; margin-bottom: 10px;">{title}</h2>
                        <p style="color: #666; text-align: center; margin-bottom: 30px;">{message_text}</p>
                        
                        <div style="background-color: #f9f9f9; border: 2px solid #4CAF50; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                            <p style="color: #666; margin: 0 0 10px 0; font-size: 14px;">Your Verification Code:</p>
                            <p style="font-size: 36px; font-weight: bold; color: #4CAF50; margin: 10px 0; letter-spacing: 5px;">{otp_code}</p>
                        </div>
                        
                        <p style="color: #999; font-size: 12px; text-align: center; margin-top: 20px;">
                            This code will expire in 15 minutes.
                        </p>
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            If you didn't request this code, please ignore this email.
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="color: #999; font-size: 11px; text-align: center;">
                            EverAdhere | EverAdhere Management System<br>
                            © 2026 All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            # Plain text content
            text_content = f"""
            {title}
            
            {message_text}
            
            Your Verification Code: {otp_code}
            
            This code will expire in 15 minutes.
            
            If you didn't request this code, please ignore this email.
            
            ---
            EverAdhere | EverAdhere Management System
            © 2026 All rights reserved.
            """
            
            # Attach parts
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            print(f"✅ Email content prepared")
            
            # Send email with retries
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    print(f"📤 Connecting to SMTP server: {settings.SMTP_HOST}:{settings.SMTP_PORT} (attempt {attempt})")
                    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
                        print(f"✅ Connected to SMTP server")
                        print(f"🔒 Starting TLS...")
                        server.starttls()
                        print(f"✅ TLS enabled")
                        print(f"🔐 Logging in as {settings.SMTP_USER}...")
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                        print(f"✅ Logged in successfully")
                        print(f"📨 Sending email...")
                        server.send_message(msg)
                        print(f"✅ Email sent successfully!")
                        break
                except smtplib.SMTPAuthenticationError:
                    print(f"❌ SMTP Authentication failed on attempt {attempt}")
                    # authentication won't succeed on retries
                    return False
                except Exception as e:
                    print(f"⚠️ SMTP send attempt {attempt} failed: {e}")
                    if attempt < max_attempts:
                        time.sleep(1)
                        continue
                    else:
                        print(f"❌ All SMTP attempts failed")
                        return False
            
            print(f"{'='*60}")
            print(f"✅ EMAIL DELIVERY COMPLETE")
            print(f"{'='*60}\n")
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"\n{'='*60}")
            print(f"❌ SMTP AUTHENTICATION ERROR")
            print(f"{'='*60}")
            print(f"Error: {str(e)}")
            print(f"Check SMTP_USER and SMTP_PASSWORD in .env")
            print(f"Current User: {settings.SMTP_USER}")
            print(f"{'='*60}\n")
            return False
        except smtplib.SMTPException as e:
            print(f"\n{'='*60}")
            print(f"❌ SMTP SERVER ERROR")
            print(f"{'='*60}")
            print(f"Error: {str(e)}")
            print(f"Check SMTP_HOST and SMTP_PORT in .env")
            print(f"Current: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
            print(f"{'='*60}\n")
            return False
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"❌ EMAIL SENDING ERROR")
            print(f"{'='*60}")
            print(f"Error sending email to {email}: {str(e)}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            return False
            return False
    
    @staticmethod
    def send_welcome_email(email: str, name: str) -> bool:
        """
        Send welcome email to new user
        
        Args:
            email: Recipient email address
            name: User's name
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Welcome to EverAdhere"
            msg['From'] = settings.EMAILS_FROM_EMAIL
            msg['To'] = email
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h1 style="color: #4CAF50; text-align: center;">Welcome to EverAdhere</h1>
                        <p style="color: #666; font-size: 16px;">Hi {name},</p>
                        
                        <p style="color: #666; line-height: 1.6;">
                            Thank you for joining EverAdhere! Your account has been successfully created and verified.
                        </p>
                        
                        <p style="color: #666; line-height: 1.6;">
                            You can now:
                        </p>
                        <ul style="color: #666; line-height: 1.8;">
                            <li>Access your personalized dashboard</li>
                            <li>View and manage medications</li>
                            <li>Track your therapy progress</li>
                            <li>Receive notifications and updates</li>
                        </ul>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            EverAdhere | EverAdhere Management System<br>
                            © 2026 All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            text_content = f"""
            Welcome to EverAdhere
            
            Hi {name},
            
            Thank you for joining EverAdhere! Your account has been successfully created and verified.
            
            You can now:
            - Access your personalized dashboard
            - View and manage medications
            - Track your therapy progress
            - Receive notifications and updates
            
            ---
            EverAdhere | EvereAdhere Management System
            © 2026 All rights reserved.
            """
            
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending welcome email to {email}: {str(e)}")
            return False
