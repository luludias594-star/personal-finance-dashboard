from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TransactionCreate(BaseModel):
    title: str
    amount: float
    type: str
    category: str
    date: str

class TransactionResponse(BaseModel):
    id: int
    title: str
    amount: float
    type: str
    category: str
    date: str
    user_id: int

    class Config:
        from_attributes = True

class BudgetCreate(BaseModel):
    category: str
    amount: float

class BudgetResponse(BaseModel):
    id: int
    category: str
    amount: float
    user_id: int

    class Config:
        from_attributes = True