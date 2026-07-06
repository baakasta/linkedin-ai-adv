from typing import Annotated
import uuid
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.user import User, Account
from backend.models.company import Company
from backend.models.executive import Executive
from backend.models.subscription import Subscription, PlanTier, SubscriptionStatus

from backend.db.db import Base, engine, get_db

from backend.schemas.userschema import UserCreate, UserResponse,AccountResponse, UserUpdate,AccountUpdate
from backend.schemas.executiveschema import ExecutiveCreate, ExecutiveResponse,ExecutiveUpdate
from backend.schemas.companyschema import CompanyCreate, CompanyResponse,CompanyUpdate
from backend.schemas.subscriptionschema import SubscriptionResponse



Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/api/users")
def get_all_users(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(User))
    users = result.scalars().all()
    return users
@app.get("/api/accounts")
def get_all_accounts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(Account))
    accounts = result.scalars().all()
    return accounts

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(User).where(User.id == user_id),
    )
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@app.post(
    "/api/users/create",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):

    existing_email = db.execute(select(User).where(User.email == user.email)).scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_account = Account(name=user.account_name)
    db.add(new_account)
    db.flush()  # confirms new_account.id without committing yet

    new_subscription = Subscription(
    account_id=new_account.id,
    plan_tier=PlanTier.DECOUVERTE,
    status=SubscriptionStatus.ACTIVE,
    )
    db.add(new_subscription)

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        account_id=new_account.id, 
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.patch("/api/users/{user_id}", response_model=UserResponse)
def partial_update_user(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_update.email is not None and user_update.email != user.email:
        result = db.execute(
            select(User).where(User.email == user_update.email),
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()


@app.get("/api/accounts/{account_id}", response_model=AccountResponse)
def get_account(account_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(Account).where(Account.id == account_id),
    )
    account = result.scalars().first()
    if account:
        return account
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

@app.get("/api/accounts/{account_id}/subscription", response_model=SubscriptionResponse)
def get_subscription(account_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(Subscription).where(Subscription.account_id == account_id)
    )
    subscription = result.scalars().first()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription

@app.patch("/api/accounts/{account_id}", response_model=AccountResponse)
def partial_update_account(
    account_id: uuid.UUID,
    account_update: AccountUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(Account).where(Account.id == account_id))
    account = result.scalars().first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    if account_update.name is not None:
        account.name = account_update.name

    db.commit()
    db.refresh(account)
    return account

@app.get("/api/companies", response_model=list[CompanyResponse])
def get_all_companies(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(Company))
    return result.scalars().all()

@app.get("/api/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company

@app.post("/api/companies/create", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(company: CompanyCreate, account_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    existing = db.execute(
        select(Company).where(Company.name == company.name)
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company name already exists")
    
    new_company = Company(
        account_id=account_id,
        name=company.name,
        linkedin_url=company.linkedin_url,
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company

@app.patch("/api/companies/{company_id}", response_model=CompanyResponse)
def partial_update_company(
    company_id: uuid.UUID,
    company_update: CompanyUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(Company).where(Company.id == company_id))
    company = result.scalars().first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    update_data = company_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)
    return company

@app.delete("/api/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(Company).where(Company.id == company_id))
    company = result.scalars().first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="company not found",
        )

    db.delete(company)
    db.commit()

@app.get("/api/executives", response_model=list[ExecutiveResponse])
def get_all_executives(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(Executive))
    return result.scalars().all()

@app.get("/api/executives/{executive_id}", response_model=ExecutiveResponse)
def get_executive(executive_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(Executive).where(Executive.id == executive_id)
    )
    executive = result.scalars().first()
    if not executive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Executive not found")
    return executive

@app.post("/api/executives/create", response_model=ExecutiveResponse, status_code=status.HTTP_201_CREATED)
def create_executive(executive: ExecutiveCreate, db: Annotated[Session, Depends(get_db)]):
    # verify the company exists first
    company = db.execute(
        select(Company).where(Company.id == executive.company_id)
    ).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    new_executive = Executive(
        company_id=executive.company_id,
        full_name=executive.full_name,
        job_title=executive.job_title,
        linkedin_url=executive.linkedin_url,
    )
    db.add(new_executive)
    db.commit()
    db.refresh(new_executive)
    return new_executive

@app.patch("/api/executives/{executive_id}", response_model=ExecutiveResponse)
def partial_update_executive(
    executive_id: uuid.UUID,
    executive_update: ExecutiveUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(Executive).where(Executive.id == executive_id))
    executive = result.scalars().first()
    if not executive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Executive not found",
        )

    update_data = executive_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(executive, field, value)

    db.commit()
    db.refresh(executive)
    return executive

@app.delete("/api/executives/{executive_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_executive(executive_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(Executive).where(Executive.id == executive_id))
    executive = result.scalars().first()
    if not executive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="executive not found",
        )

    db.delete(executive)
    db.commit()