from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import User, Transaction, Budget
from schemas import (
    UserCreate,
    UserLogin,
    TransactionCreate,
    BudgetCreate
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Personal Finance API",
    version="2.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


security = HTTPBearer()

@app.get("/")
def home():
    return {
        "message": "Personal Finance API está funcionando!"
    }


# =========================
# USUÁRIOS
# =========================

@app.post("/users/register")
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Este e-mail já está cadastrado."
        )

    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Usuário criado com sucesso!",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email
        }
    }


@app.post("/users/login")
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha incorretos."
        )

    if not verify_password(
        user.password,
        existing_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha incorretos."
        )

    access_token = create_access_token(
        data={
            "sub": str(existing_user.id)
        }
    )

    return {
        "message": "Login realizado com sucesso!",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": existing_user.id,
            "name": existing_user.name,
            "email": existing_user.email
        }
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado."
        )

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Usuário não encontrado."
        )

    return user


@app.get("/users/me")
def get_my_user(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }


# =========================
# TRANSAÇÕES
# =========================

@app.post("/transactions")
def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_transaction = Transaction(
        title=transaction.title,
        amount=transaction.amount,
        type=transaction.type,
        category=transaction.category,
        date=transaction.date,
        user_id=current_user.id
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return {
        "message": "Transação criada com sucesso!",
        "transaction": {
            "id": new_transaction.id,
            "title": new_transaction.title,
            "amount": new_transaction.amount,
            "type": new_transaction.type,
            "category": new_transaction.category,
            "date": new_transaction.date,
            "user_id": new_transaction.user_id
        }
    }


@app.get("/transactions")
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == current_user.id
        )
        .all()
    )

    return transactions


@app.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
        .first()
    )

    if not existing_transaction:
        raise HTTPException(
            status_code=404,
            detail="Transação não encontrada."
        )

    existing_transaction.title = transaction.title
    existing_transaction.amount = transaction.amount
    existing_transaction.type = transaction.type
    existing_transaction.category = transaction.category
    existing_transaction.date = transaction.date

    db.commit()
    db.refresh(existing_transaction)

    return {
        "message": "Transação atualizada com sucesso!",
        "transaction": {
            "id": existing_transaction.id,
            "title": existing_transaction.title,
            "amount": existing_transaction.amount,
            "type": existing_transaction.type,
            "category": existing_transaction.category,
            "date": existing_transaction.date,
            "user_id": existing_transaction.user_id
        }
    }


@app.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transação não encontrada."
        )

    db.delete(transaction)
    db.commit()

    return {
        "message": "Transação excluída com sucesso!"
    }


# =========================
# ORÇAMENTOS
# =========================

@app.post("/budgets")
def create_budget(
    budget: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_budget = Budget(
        category=budget.category,
        amount=budget.amount,
        user_id=current_user.id
    )

    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)

    return {
        "message": "Orçamento criado com sucesso!",
        "budget": {
            "id": new_budget.id,
            "category": new_budget.category,
            "amount": new_budget.amount,
            "user_id": new_budget.user_id
        }
    }


@app.get("/budgets")
def get_budgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budgets = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id
        )
        .all()
    )

    return budgets


@app.put("/budgets/{budget_id}")
def update_budget(
    budget_id: int,
    budget: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_budget = (
        db.query(Budget)
        .filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        )
        .first()
    )

    if not existing_budget:
        raise HTTPException(
            status_code=404,
            detail="Orçamento não encontrado."
        )

    existing_budget.category = budget.category
    existing_budget.amount = budget.amount

    db.commit()
    db.refresh(existing_budget)

    return {
        "message": "Orçamento atualizado com sucesso!",
        "budget": {
            "id": existing_budget.id,
            "category": existing_budget.category,
            "amount": existing_budget.amount,
            "user_id": existing_budget.user_id
        }
    }


@app.delete("/budgets/{budget_id}")
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = (
        db.query(Budget)
        .filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        )
        .first()
    )

    if not budget:
        raise HTTPException(
            status_code=404,
            detail="Orçamento não encontrado."
        )

    db.delete(budget)
    db.commit()

    return {
        "message": "Orçamento excluído com sucesso!"
    }