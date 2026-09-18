from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TransactionCreate(BaseModel):
    title: str
    amount: float
    type: str
    category: str
    date: str


class BudgetCreate(BaseModel):
    category: str
    amount: float