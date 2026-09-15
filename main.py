from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List

from database import engine, Base, get_db
from models import User, Transaction, Budget
from schemas import (
    UserCreate, UserLogin, TransactionCreate, TransactionResponse,
    BudgetCreate, BudgetResponse
)
from auth import hash_password, verify_password, create_access_token, verify_token

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Personal Finance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# --- DEPENDÊNCIA DE AUTENTICAÇÃO (PRECISA VIR ANTES DAS ROTAS) ---

def get_current_user_dep(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")
    return user

# --- ROTAS DE USUÁRIO ---

@app.get("/")
def home():
    return {"message": "Personal Finance API está funcionando!"}

@app.post("/users/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado.")
    
    new_user = User(name=user.name, email=user.email, password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "Usuário criado com sucesso!", "user": {"id": new_user.id, "name": new_user.name, "email": new_user.email}}

@app.post("/users/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")
        
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": db_user.id, "name": db_user.name}}

@app.put("/users/change-password")
def change_password(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Preencha todos os campos.")
    if not verify_password(current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")
    current_user.password = hash_password(new_password)
    db.commit()
    return {"message": "Senha alterada com sucesso!"}

@app.get("/users/me")
def read_current_user(current_user: User = Depends(get_current_user_dep)):
    return {"user": {"id": current_user.id, "name": current_user.name, "email": current_user.email}}

# --- ROTAS DE TRANSAÇÃO ---

@app.post("/transactions", response_model=TransactionResponse)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    new_transaction = Transaction(
        title=transaction.title, amount=transaction.amount, type=transaction.type,
        category=transaction.category, date=transaction.date, user_id=current_user.id
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

@app.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    return db.query(Transaction).filter(Transaction.user_id == current_user.id).all()

@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transação não encontrada.")
    db.delete(db_transaction)
    db.commit()
    return {"message": "Transação excluída com sucesso!"}

# --- ROTAS DE ORÇAMENTO ---

@app.get("/budgets", response_model=List[BudgetResponse])
def get_budgets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    return db.query(Budget).filter(Budget.user_id == current_user.id).all()

@app.post("/budgets", response_model=BudgetResponse)
def set_budget(budget: BudgetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    existing_budget = db.query(Budget).filter(Budget.category == budget.category, Budget.user_id == current_user.id).first()
    if existing_budget:
        existing_budget.amount = budget.amount
        db.commit()
        db.refresh(existing_budget)
        return existing_budget
    
    new_budget = Budget(category=budget.category, amount=budget.amount, user_id=current_user.id)
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget