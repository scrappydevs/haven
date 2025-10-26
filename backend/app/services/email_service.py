"""
Email Service for sending handoff forms to nurses and doctors
Supports SMTP and SendGrid
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails with attachments"""

    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
    ):
        """
        Initialize email service

        Args:
            smtp_server: SMTP server address (e.g., 'smtp.gmail.com')
            smtp_port: SMTP port (default: 587 for TLS)
            smtp_username: SMTP authentication username
            smtp_password: SMTP authentication password
            sender_email: From email address
            sender_name: From name
        """
        # Load from environment variables if not provided
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.getenv("SMTP_USERNAME", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.sender_email = sender_email or os.getenv("SENDER_EMAIL", self.smtp_username)
        self.sender_name = sender_name or os.getenv("SENDER_NAME", "Haven Health System")

        self.use_tls = True  # Always use TLS for security

    def send_handoff_form(
        self,
        recipient_emails: List[str],
        form_number: str,
        patient_id: str,
        patient_name: Optional[str],
        severity: str,
        alert_summary: str,
        pdf_path: str,
        cc_emails: Optional[List[str]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send handoff form PDF via email

        Args:
            recipient_emails: List of recipient email addresses
            form_number: Form number (e.g., "HO-2025-0001")
            patient_id: Patient ID
            patient_name: Patient name
            severity: Alert severity level
            alert_summary: Brief alert summary
            pdf_path: Path to PDF file to attach
            cc_emails: Optional CC recipients
            additional_context: Additional context for email body

        Returns:
            Dict with success status and message
        """
        try:
            # Validate inputs
            if not recipient_emails:
                return {"success": False, "message": "No recipient emails provided"}

            if not os.path.exists(pdf_path):
                return {"success": False, "message": f"PDF file not found: {pdf_path}"}

            # Create email
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = ", ".join(recipient_emails)
            if cc_emails:
                msg['Cc'] = ", ".join(cc_emails)
            msg['Subject'] = self._create_subject(form_number, severity, patient_name or patient_id)

            # Create email body
            html_body = self._create_email_body(
                form_number=form_number,
                patient_id=patient_id,
                patient_name=patient_name,
                severity=severity,
                alert_summary=alert_summary,
                additional_context=additional_context
            )

            msg.attach(MIMEText(html_body, 'html'))

            # Attach PDF
            with open(pdf_path, 'rb') as f:
                pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                pdf_filename = Path(pdf_path).name
                pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
                msg.attach(pdf_attachment)

            # Send email
            all_recipients = recipient_emails + (cc_emails or [])
            self._send_email(msg, all_recipients)

            logger.info(f"Successfully sent handoff form {form_number} to {len(all_recipients)} recipients")

            return {
                "success": True,
                "message": f"Email sent successfully to {len(all_recipients)} recipients",
                "recipients": all_recipients
            }

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg, "error": str(e)}

    def _create_subject(self, form_number: str, severity: str, patient_identifier: str) -> str:
        """Create email subject line"""
        severity_prefix = ""
        if severity.lower() in ["critical", "high"]:
            severity_prefix = f"[{severity.upper()}] "

        return f"{severity_prefix}Patient Handoff Form {form_number} - {patient_identifier}"

    def _create_email_body(
        self,
        form_number: str,
        patient_id: str,
        patient_name: Optional[str],
        severity: str,
        alert_summary: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create HTML email body"""
        # Severity color mapping
        severity_colors = {
            "critical": "#dc2626",
            "high": "#ea580c",
            "medium": "#ca8a04",
            "low": "#059669",
            "info": "#6b7280"
        }
        severity_color = severity_colors.get(severity.lower(), "#6b7280")

        patient_display = patient_name if patient_name else patient_id

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8fafc; border-left: 4px solid #2563eb; padding: 20px; margin-bottom: 20px;">
                <h1 style="margin: 0 0 10px 0; color: #1e293b; font-size: 24px;">Patient Handoff Form</h1>
                <p style="margin: 0; color: #64748b; font-size: 14px;">Haven Health System</p>
            </div>

            <div style="background-color: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <div style="margin-bottom: 15px;">
                    <strong style="color: #475569;">Form Number:</strong> {form_number}
                </div>

                <div style="margin-bottom: 15px;">
                    <strong style="color: #475569;">Patient:</strong> {patient_display}
                    <br/>
                    <span style="color: #64748b; font-size: 14px;">ID: {patient_id}</span>
                </div>

                <div style="margin-bottom: 15px;">
                    <strong style="color: #475569;">Severity:</strong>
                    <span style="background-color: {severity_color}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 12px; text-transform: uppercase;">
                        {severity}
                    </span>
                </div>

                <div style="margin-bottom: 15px;">
                    <strong style="color: #475569;">Summary:</strong>
                    <p style="margin: 8px 0 0 0; padding: 12px; background-color: #f8fafc; border-radius: 4px; color: #334155;">
                        {alert_summary}
                    </p>
                </div>
            </div>
        """

        # Add additional context if provided
        if additional_context:
            html += """
            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                <strong style="color: #92400e;">Additional Information:</strong>
            """
            for key, value in additional_context.items():
                html += f"""
                <p style="margin: 8px 0; color: #78350f;">
                    <strong>{key}:</strong> {value}
                </p>
                """
            html += "</div>"

        html += """
            <div style="background-color: #f8fafc; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
                <strong style="color: #475569;">📎 Attachment:</strong>
                <p style="margin: 8px 0 0 0; color: #64748b; font-size: 14px;">
                    A detailed PDF handoff form is attached to this email. Please review it for complete patient information, clinical context, and recommended actions.
                </p>
            </div>

            <div style="border-top: 2px solid #e2e8f0; padding-top: 20px; margin-top: 20px;">
                <p style="margin: 0 0 10px 0; color: #dc2626; font-size: 14px;">
                    ⚠️ <strong>Important:</strong> This email contains confidential patient information. Please handle according to HIPAA guidelines.
                </p>
                <p style="margin: 0; color: #64748b; font-size: 12px;">
                    This is an automated notification from the Haven Health System AI Agent.
                    <br/>
                    For technical issues, please contact your system administrator.
                </p>
            </div>
        </body>
        </html>
        """

        return html

    def _send_email(self, msg: MIMEMultipart, recipients: List[str]):
        """Send email via SMTP"""
        try:
            # Connect to SMTP server
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)

            # Login if credentials provided
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            # Send email
            server.sendmail(self.sender_email, recipients, msg.as_string())
            server.quit()

            logger.info(f"Email sent successfully via SMTP to {len(recipients)} recipients")

        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            raise

    def test_connection(self) -> Dict[str, Any]:
        """Test SMTP connection and credentials"""
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)

            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            server.quit()

            return {
                "success": True,
                "message": "SMTP connection successful"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"SMTP connection failed: {str(e)}"
            }


# Create singleton instance (will use environment variables)
email_service = EmailService()
