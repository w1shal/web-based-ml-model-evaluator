from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)  # bcrypt limit is 72 bytes

    @field_validator("password")
    @classmethod
    def strong(cls, v):
        if not (any(c.isalpha() for c in v) and any(c.isdigit() for c in v)):
            raise ValueError("Password must contain letters and digits")
        return v


class LoginIn(BaseModel):
    identifier: str = Field(min_length=1)  # username or email
    password: str = Field(min_length=1)
