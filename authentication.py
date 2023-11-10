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

async def verify_password(provided_password: str, hash_password: str):
    return pwd_context.verify(provided_password, hash_password)

async def authenticate_user(provided_username: str, provided_password: str):
    user = await User.get(username = provided_username)

    if user and verify_password(provided_password, user.password):
        return user
    else:
        return False

async def token_generator(provided_username: str, provided_password: str):
    user = await authenticate_user(provided_username, provided_password)
    
    if user:
        token_data = {
            "id" : user.id,
            "username" : user.username
        }

        token = jwt.encode(token_data, config_credentials["SECRET"])

        return token
    else:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid username or password",
            headers = {"WWW-Authenticate" : "Bearer"}
        )