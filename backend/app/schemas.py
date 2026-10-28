from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=72,
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError(
                "Password exceeds bcrypt's 72-byte limit"
            )

        if not any(char.isalpha() for char in value):
            raise ValueError(
                "Password must contain at least one letter"
            )

        if not any(char.isdigit() for char in value):
            raise ValueError(
                "Password must contain at least one digit"
            )

        return value