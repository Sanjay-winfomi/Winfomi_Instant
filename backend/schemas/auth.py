from pydantic import BaseModel, Field


class CompanyLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class CompanyLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CompanyUser(BaseModel):
    id: int
    email: str
    name: str
    role: str
