from tortoise import Model, fields
from tortoise.contrib.pydantic import pydantic_model_creator
from pydantic import BaseModel
from datetime import datetime

class User(Model):
    id = fields.IntField(pk = True, index = True)
    username = fields.CharField(max_length = 100, null = False, unique = True)
    email = fields.CharField(max_length = 100, null = False, unique = True)
    password = fields.CharField(max_length = 100, null = False)
    is_verified = fields.BooleanField(default = False)
    join_date = fields.DatetimeField(default = datetime.utcnow)

class Business(Model):
    id = fields.IntField(pk = True, index = True)
    owner = fields.ForeignKeyField("models.User", related_name = "business")

class Product(Model):
    id = fields.IntField(pk = True, index = True)
    name = fields.CharField(max_length = 100, null = False, unique = True)
    price = fields.DecimalField(max_digits = 100, decimal_places = 2)
    business = fields.ForeignKeyField("models.Business", related_name = "product")

user_pydantic = pydantic_model_creator(User, name = "User", exclude = ("is_verified"))
user_pydanticIn = pydantic_model_creator(User, name = "UserIn", exclude_readonly = True, exclude = ("is_verified", "join_date"))
user_pydanticOut = pydantic_model_creator(User, name = "UserOut", exclude = ("password"))

business_pydantic = pydantic_model_creator(Business, name = "Business")
business_pydanticIn = pydantic_model_creator(Business, name = "BusinessIn", exclude_readonly = True)

product_pydantic = pydantic_model_creator(Product, name = "Product")
product_pydanticIn = pydantic_model_creator(Product, name = "ProductIn", exclude_readonly = True)