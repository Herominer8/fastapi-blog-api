from fastapi_mail import FastMail, ConnectionConfig, MessageSchema
from core.config import settings


#Only Uncomment If You've Already Prepared An Email Service
# conf = ConnectionConfig(
#     MAIL_USERNAME=settings.MAIL_USERNAME,
#     MAIL_PASSWORD=settings.MAIL_PASSWORD,
#     MAIL_PORT=settings.MAIL_PORT,
#     MAIL_SERVER=settings.MAIL_SERVER,
#     MAIL_STARTTLS=settings.MAIL_STARTTLS,
#     MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
#     USE_CREDENTIALS=True,
#     VALIDATE_CERTS=True
# )

# async def send_reset_email(email_to: str, token: str):
#     reset_link = f"http://localhost:8000/reset-password?token={token}"
    
#     html_content = f"""
#     <html>
#     <body>
#         <h2>Reset Your Password</h2>
#         <p>Click the link below to reset your password:</p>
#         <a href="{reset_link}">{reset_link}</a>
#         <p>This link expires in 1 hour.</p>
#         <p>If you didn't request this, ignore this email.</p>
#     </body>
#     </html>
#     """

#     message = MessageSchema(
#         subject="Reset Your Password",
#         recipients=[email_to],
#         body=html_content,
#         subtype="html"
#     )

#     fm = FastMail(conf)
#     await fm.send_message(message)

# async def send_verification_email_task(email_to: str, code: str):
#     verification_link = f"http://localhost:8000/verify-email?code={code}"
    
#     html = f"""
#     <html>
#     <body>
#         <h2>Verify Your Email</h2>
#         <p>Click the link below to verify your email:</p>
#         <a href="{verification_link}">{verification_link}</a>
#         <p>This link expires in 24 hours.</p>
#     </body>
#     </html>
#     """
    
#     message = MessageSchema(
#         subject="Verify Your Email",
#         recipients=[email_to],
#         body=html,
#         subtype="html"
#     )
    
#     fm = FastMail(conf)
#     await fm.send_message(message)