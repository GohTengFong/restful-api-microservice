from passlib.context import CryptContext
import jwt
from dotenv import dotenv_values
from models import User
from fastapi import HTTPException, status

config_credentials = dotenv_values(".env")

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

def hash_password(password):
    return pwd_context.hash(password)

async def verify_token(token: str):
    try:
        payload = jwt.decode(token, config_credentials["SECRET"], algorithms = ["HS256"])
        user = await User.get(id = payload.get("id"))
    except:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid jwtoken.",
            headers = {"WWW-Authenticate" : "Bearer"}
        )

    return user