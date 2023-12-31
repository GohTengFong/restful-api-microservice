from fastapi import FastAPI, Request, HTTPException, status, Depends
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

# uvicorn main:app --reload

app = FastAPI()

# oath2_scheme provides a form for the user to fill in their username and password and redirects this request to "/token"
# after, it will go and look in the request for that Authorization header, check if the value is Bearer plus some token, and will return the token as a str
oath2_scheme = OAuth2PasswordBearer(tokenUrl = "token")

@app.get("/")
def root():
    return {"Message" : "Hello World"}

# OAuth2PasswordRequestForm is a Pydantic model class that automatically parses and validates the content of an HTTP POST request
# this route is typically used for generating and returning access tokens
@app.post("/token")
async def generate_token(request_form: OAuth2PasswordRequestForm = Depends()):
    token = await token_generator(request_form.username, request_form.password)
    return {"access_token" : token, "token_type" : "bearer"}

async def get_current_user(token: str = Depends(oath2_scheme)):
    try:
        payload = jwt.decode(token, config_credentials["SECRET"], algorithms = ["HS256"])
        user = await User.get(id = payload.get("id"))
    except:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid username or password",
            headers = {"WWW-Authenticate" : "Bearer"}
        )
    
    return await user

@app.post("/login")
async def login_user(user: user_pydantic = Depends(get_current_user)):
    business = await Business.get(owner = user)

    return {
        "Account Details" : {
            "Username" : user.username,
            "Email" : user.email,
            "Verified" : user.is_verified,
            "Join_Date" : user.join_date.strftime("%b %d %Y")
        }
    }

@post_save(User)
async def register_business(
    sender: "Type[User]",
    instance: User,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str]):
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
    
# CRUD for Products

@app.post("/products")
async def add_new_product(product: product_pydanticIn, user: user_pydantic = Depends(get_current_user)):
    product_info = product.dict(exclude_unset = True)

    if product_info["price"] > 0:
        product_obj = await Product.create(**product_info, business = user)
        new_product = await product_pydantic.from_tortoise_orm(product_obj)

        return {"Data" : new_product}
    else:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Price of a product cannot be equal to or lesser than 0.",
            headers = {"WWW-Authenticate" : "Bearer"}
        )
    
@app.get("/products")
async def get_products():
    response = await product_pydantic.from_queryset(Product.all())
    return {"Data" : response}

@app.get("/products/{id}")
async def get_product(id: int):
    product = await Product.get(id = id)
    business = await product.business
    owner = await business.owner

    response = await product_pydantic.from_queryset_single(Product.get(id = id))
    return {"Data" : {
        "Product Details" : response,
        "Business Details" : {
            "Owner Username" : owner.username,
            "Owner Email" : owner.email
            }
        }
    }

@app.put("/products/{id}")
async def update_product(id: int, update: product_pydanticIn, user: user_pydantic = Depends(get_current_user)):
    update_info = update.dict(exclude_unset = True)
    
    product = await Product.get(id = id)
    business = await product.business
    owner = await business.owner

    if user == owner and update_info["price"] > 0:
        product = await product.update_from_dict(update_info)
        await product.save()

        response = await product_pydantic.from_tortoise_orm(product)
        return {"Data" : response}
    elif update_info["price"] <= 0:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Price of a product cannot be equal to or lesser than 0.",
            headers = {"WWW-Authenticate" : "Bearer"}
        )
    else:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Unable to edit another user's products.",
            headers = {"WWW-Authenticate" : "Bearer"}
        )

@app.delete("/products/{id}")
async def delete_product(id: int, user: user_pydanticIn = Depends(get_current_user)):
    product = await Product.get(id = id)
    business = await product.business
    owner = await business.owner

    if user == owner:
        await product.delete()
        return {"Message" : "Product deleted."}
    else:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Unable to delete another user's products.",
            headers = {"WWW-Authenticate" : "Bearer"}
        )

register_tortoise(
    app,
    db_url = "sqlite://database.sqlite3",
    modules = {"models" : ["models"]},
    generate_schemas = True,
    add_exception_handlers = True
)