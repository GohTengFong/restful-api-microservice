from fastapi import FastAPI, Request, HTTPException, status
from tortoise.contrib.fastapi import register_tortoise
from models import *
from emails import *

# Authentication
from authentication import *
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Response Classes
from fastapi.responses import HTMLResponse

# Templates
from fastapi.templating import Jinja2Templates

# Signals
from tortoise.signals import post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient

app = FastAPI()

# uvicorn main:app --reload

@app.get("/")
def root():
    return {"Message" : "Hello World"}

@post_save(User)
async def register_business(
    sender: "Type[User]",
    instance: User,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str]
):
    if created:
        business_obj = await Business.create(owner = instance)

        await business_pydantic.from_tortoise_orm(business_obj)

        await send_verification_email([instance.email], instance)

@app.post("/register")
async def register_user(user: user_pydanticIn):
    user_info = user.dict(exclude_unset = True)
    user_info["password"] = hash_password(user_info["password"])
    user_object = await User.create(**user_info) # returns a user database object (represents a record in the database)
    new_user = await user_pydantic.from_tortoise_orm(user_object) # converts it into a pydantic model object (a Python object)

    return {"Message" : f"Hello {new_user.username}! Please verify your account via email."}

templates = Jinja2Templates(directory = "templates")
@app.get("/verification", response_class = HTMLResponse)
async def verify_user(request: Request, token: str):
    user = await verify_token(token)

    if user and not user.is_verified:
        user.is_verified = True
        await user.save()
        return templates.TemplateResponse("verification.html", {"request": request, "username" : user.username})
    else:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid jwtoken.",
            headers = {"WWW-Authenticate" : "Bearer"}
        )

register_tortoise(
    app,
    db_url = "sqlite://database.sqlite3",
    modules = {"models" : ["models"]},
    generate_schemas = True,
    add_exception_handlers = True
)