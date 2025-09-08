import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pydantic import EmailStr

from app.core.config import settings
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode


@staticmethod
def send_email_smtp(email: EmailStr, data: str, email_type: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SENDER_EMAIL
        msg['To'] = email
        current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        if email_type == "otp":
            msg['Subject'] = f"AGSS Password Reset Verification Code in {current_time}"
            body = f"""
                We are sending you a Verification Code to complete your authentication process:

                Your Verification Code: {data}

                Important Security Notes:
                - This OTP is valid for 3 minutes only
                - Please do not share this code with anyone
                - If you did not request this verification, please ignore this email

                For your security, please ensure you are on the official AGSS website before entering this code.

                Best regards,
                AGSS Support Team (agss.swt301@gmail.com)"""

        elif email_type == "create":
            msg['Subject'] = f"AGSS Account Created in {current_time}"
            body = f"""
                Congratulations! Your AGSS account has been successfully created.

                Account Information:
                - Login Email: {email}
                - Temporary Password: {data}

                Security Recommendations:
                - Please change your password immediately after your first login
                - Use a strong password combining letters, numbers, and special characters
                - Never share your login credentials with others
                - Enable two-factor authentication for enhanced security

                Getting Started:
                1. Visit our website and log in with the credentials above
                2. Complete your profile setup
                3. Explore our features and services

                If you need assistance, please don't hesitate to contact us:
                Contact: agss.swt301@gmail.com

                Welcome to AGSS! We're excited to have you on board."""

        elif email_type == "change_email":
            msg['Subject'] = f"AGSS Change Email Verification Code in {current_time}"
            body = f"""
                We are sending you a Verification Code to complete your authentication process:

                Your Verification Code: {data}

                Important Security Notes:
                - This OTP is valid for 3 minutes only
                - Please do not share this code with anyone
                - If you did not request this verification, please ignore this email

                For your security, please ensure you are on the official AGSS website before entering this code.

                Best regards,
                AGSS Support Team (agss.swt301@gmail.com)"""

        elif email_type == "change_status":
            listData = data.split("|")
            full_name = listData[0]
            status = listData[1]
            message = listData[2]

            if status == "active":

                msg['Subject'] = f"AGSS Account Active - {current_time}"

                body = f"""
                    Dear {full_name}
                    
                    Your AGSS account has been successfully active
                    
                    Content: {message}
                    
                    Current Status: ACTIVE 

                    Important Security Notes:
                    
                      - If you did not request this change, please contact AGSS Support immediately.
                      
                      - Always make sure you are accessing the official AGSS website.

                    Access the website:  https://agss-swt301.online/login

                    Best regards,
                     
                    AGSS Support Team (agss.swt301@gmail.com)
                """
            elif status == "inactive":

                msg['Subject'] = f"AGSS Account Inactive - {current_time}"

                body = f"""

                    Dear {full_name}

                    Your AGSS account has been inactive.

                    Reason: {message}

                    Current Status: INACTIVE

                    Important Security Notes:

                    - If you did not request this change, please contact AGSS Support immediately.

                    - While inactive, you will not be able to log in or use AGSS services until reactivated.

                    Best regards,

                    AGSS Support Team (agss.swt301@gmail.com)

                """
        else:
            raise ValueError(f"Unsupported email type: {email_type}")

        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(settings.STMP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as ex:
        raise CustomException(ErrorCode.AUTH_EMAIL_SEND_FAILED)
