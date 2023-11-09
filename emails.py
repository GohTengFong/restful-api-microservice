from typing import List

from fastapi import BackgroundTasks, HTTPException, status
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import dotenv_values
from pydantic import BaseModel, EmailStr
from models import User
import jwt

# Configuring verification email sender
config_credentials = dotenv_values(".env")
config = ConnectionConfig(
    MAIL_USERNAME = config_credentials["EMAIL"],
    MAIL_PASSWORD = config_credentials["PASSWORD"],
    MAIL_FROM = config_credentials["EMAIL"],
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

class EmailSchema(BaseModel):
    email: List[EmailStr]

async def send_verification_email(email: EmailSchema, user: User):
    token_data = {
        "id" : user.id,
        "username" : user.username
    }

    token = jwt.encode(token_data, config_credentials["SECRET"], algorithm = "HS256")

    template_email = f"""
        <h3>Ecommernce Account Verification</h3>
        <a href="http://localhost:8000/verification/?token={token}">Verify</a>
    """

    message = MessageSchema(
        subject = "Account Verification Email",
        recipients = email,
        body = template_email,
        subtype = "html"
    )

    fm = FastMail(config)
    await fm.send_message(message)