import smtplib
from email.message import EmailMessage
import os
from datetime import datetime

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv('SENDER_EMAIL', 'noreply@metrouni.edu.bd')
SMTP_PASS = os.getenv('SENDER_PASSWORD', 'tnhn uwcm cara ozyl')
LOGIN_URL = os.getenv("FRONTEND_LOGIN_URL", "https://campus.metrouni.ac.bd/login")

async def send_account_created_email(
    to_email: str,
    student_id: str,
    login_id: str,
    plain_password: str
):
    msg = EmailMessage()
    msg["Subject"] = "Your Campus Account Has Been Created"
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    msg.set_content(
        f"""
        Your Campus account has been created.

        Login ID / Student ID: {student_id}
        Email: {login_id}
        Password: {plain_password}

        Login here: {LOGIN_URL}

        For security reasons, please change your password after your first login.
        """
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Account Created</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f4f6f9; font-family:Arial, Helvetica, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f9; padding:30px 0;">
            <tr>
                <td align="center">
                    <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; background:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.08);">

                        <!-- Header -->
                        <tr>
                            <td style="background:#4f46e5; padding:25px; text-align:center;">
                                <h1 style="color:#ffffff; margin:0; font-size:22px; font-weight:600;">
                                    Campus
                                </h1>
                            </td>
                        </tr>

                        <!-- Body -->
                        <tr>
                            <td style="padding:30px;">
                                <h2 style="margin-top:0; color:#111827; font-size:20px;">
                                    Welcome!
                                </h2>

                                <p style="color:#374151; font-size:15px; line-height:1.6;">
                                    Your account has been successfully created. Below are your login details:
                                </p>

                                <!-- Credentials Box -->
                                <table width="100%" cellpadding="0" cellspacing="0"
                                       style="background:#f9fafb; border-radius:8px; margin:20px 0; padding:20px;">
                                    <tr>
                                        <td style="padding:8px 0; font-size:14px;">
                                            <strong>Login ID / Student ID:</strong> {student_id}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px 0; font-size:14px;">
                                            <strong>Email:</strong> {login_id}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px 0; font-size:14px;">
                                            <strong>Password:</strong> {plain_password}
                                        </td>
                                    </tr>
                                </table>

                                <!-- CTA Button -->
                                <div style="text-align:center; margin:30px 0;">
                                    <a href="{LOGIN_URL}"
                                       style="background:#4f46e5;
                                              color:#ffffff;
                                              text-decoration:none;
                                              padding:12px 24px;
                                              border-radius:6px;
                                              font-size:14px;
                                              font-weight:600;
                                              display:inline-block;">
                                        Login to Your Account
                                    </a>
                                </div>

                                <p style="font-size:13px; color:#6b7280; line-height:1.6;">
                                    For security reasons, we strongly recommend changing your password
                                    immediately after your first login.
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background:#f3f4f6; padding:20px; text-align:center; font-size:12px; color:#9ca3af;">
                                © {datetime.utcnow().year} Student Portal. All rights reserved.
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)