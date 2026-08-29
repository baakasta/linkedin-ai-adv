from typing import Annotated
import uuid
from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.db import get_db
from backend.models.user import User
from backend.models.company import Company
from backend.models.conversation import Conversation, ConversationMessage
from backend.dependencies import require_plan
from backend.models.subscription import PlanTier
from backend.schemas.conversationschema import (
    ConversationCreate,
    ConversationResponse,
    AssistantMessageRequest,
    AssistantMessageResponse,
    ConversationDetail,
)
from backend.services.ai_client import call_ai_or_placeholder
from backend.services.assistant import build_assistant_placeholder

DEP_PRO = require_plan(PlanTier.PRO)

router = APIRouter()


async def _owned_conversation(
    conversation_id: uuid.UUID, current_user: User, db: AsyncSession
) -> Conversation:
    conversation = (await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.company))
        .where(Conversation.id == conversation_id)
    )).scalars().first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if conversation.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your conversation")
    return conversation


@router.post(
    "/assistant/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: ConversationCreate,
    current_user: Annotated[User, Depends(DEP_PRO)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    company = (await db.execute(
        select(Company).where(Company.id == payload.company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    conversation = Conversation(
        company_id=company.id,
        title=payload.title or f"Assistant - {company.name}",
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("/assistant/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(DEP_PRO)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conversation = await _owned_conversation(conversation_id, current_user, db)
    messages = (await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at)
    )).scalars().all()
    return ConversationDetail(
        id=conversation.id,
        company_id=conversation.company_id,
        title=conversation.title,
        created_at=conversation.created_at,
        messages=messages,
    )


@router.get(
    "/assistant/conversations/company/{company_id}",
    response_model=list[ConversationResponse],
)
async def list_company_conversations(
    company_id: uuid.UUID,
    current_user: Annotated[User, Depends(DEP_PRO)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    company = (await db.execute(
        select(Company).where(Company.id == company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    result = await db.execute(
        select(Conversation)
        .where(Conversation.company_id == company_id)
        .order_by(Conversation.created_at.desc())
    )
    return result.scalars().all()


@router.post(
    "/assistant/conversations/{conversation_id}/messages",
    response_model=AssistantMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: uuid.UUID,
    payload: AssistantMessageRequest,
    current_user: Annotated[User, Depends(DEP_PRO)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conversation = await _owned_conversation(conversation_id, current_user, db)
    now = datetime.now(UTC)

    # persist user message
    user_message = ConversationMessage(
        conversation_id=conversation.id,
        author="user",
        content=payload.content,
        created_at=now,
    )
    db.add(user_message)

    # build AI request from full history so far (excl. this new message)
    history = (await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at)
    )).scalars().all()
    ai_payload = {
        "conversation_id": str(conversation.id),
        "company_name": conversation.company.name,
        "messages": [
            {"author": m.author, "content": m.content} for m in history
        ],
    }
    placeholder_reply = build_assistant_placeholder(payload.content, conversation.company.name)
    ai_result = await call_ai_or_placeholder("/api/assistant/chat", ai_payload, {
        "reply": placeholder_reply,
    })

    reply_text = ai_result.get("reply") or placeholder_reply

    assistant_message = ConversationMessage(
        conversation_id=conversation.id,
        author="assistant",
        content=reply_text,
        created_at=datetime.now(UTC),
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)
    return assistant_message


@router.get(
    "/assistant/conversations/{conversation_id}/messages",
    response_model=list[AssistantMessageResponse],
)
async def list_messages(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(DEP_PRO)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conversation = await _owned_conversation(conversation_id, current_user, db)
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at)
    )
    return result.scalars().all()