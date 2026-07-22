from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.postgres import get_db
from models.models import User
from models.schemas import ReworkTicketResponse, ReworkTicketUpdate
from authentication.jwt import get_current_user
from authentication.roles import require_engineer
from services.db_service import (
    list_rework_tickets,
    get_rework_ticket_by_inspection_id,
    get_rework_ticket_by_id,
    update_rework_ticket
)

router = APIRouter(prefix="/api/rework/tickets", tags=["Rework Tickets"])

@router.get("", response_model=List[ReworkTicketResponse])
def get_all_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all rework tickets in order of creation.
    """
    return list_rework_tickets(db)

@router.get("/by-inspection/{inspection_id}", response_model=ReworkTicketResponse)
def get_ticket_by_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve the rework ticket associated with a specific inspection ID.
    """
    ticket = get_rework_ticket_by_inspection_id(db, inspection_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rework ticket not found for inspection ID {inspection_id}."
        )
    return ticket

@router.patch("/{ticket_id}", response_model=ReworkTicketResponse)
def patch_ticket(
    ticket_id: int,
    payload: ReworkTicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """
    Update a rework ticket's status, notes, or priority.
    """
    ticket = get_rework_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rework ticket with ID {ticket_id} not found."
        )
        
    updated = update_rework_ticket(db, ticket_id, payload.dict(exclude_unset=True))
    return updated
