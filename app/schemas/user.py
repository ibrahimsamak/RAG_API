from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(ge=0, le=120)
    password:str = Field(min_length=8)


    @field_validator("password")
    @classmethod
    def password_strngth(cls, v:str):
        if not any(c.isdigit() for c in v):
            raise ValueError("password must contain a digit.")
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int
    full_name: str = Field(alias="name")
    email: EmailStr
    created_at: datetime