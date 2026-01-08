from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import get_db
from ..models.proposal import MarketProposal, ProposalStatus
from ..models.market import Market
from ..schemas.proposal import ProposalCreate, ProposalResponse, ProposalReview
from ..utils.security import get_current_user, get_current_admin_user
from ..models.user import User

router = APIRouter(prefix="/proposals", tags=["Market Proposals"])


@router.post("", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def submit_proposal(
    proposal_data: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a new market proposal for admin review."""
    # Validate resolution date is in future
    if proposal_data.resolution_date <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resolution date must be in the future"
        )
    
    proposal = MarketProposal(
        title=proposal_data.title,
        description=proposal_data.description,
        category=proposal_data.category,
        resolution_date=proposal_data.resolution_date,
        user_id=current_user.id,
        status=ProposalStatus.pending.value
    )
    
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    
    # Add username to response
    response = ProposalResponse.model_validate(proposal)
    response.username = current_user.username
    
    return response


@router.get("/my", response_model=List[ProposalResponse])
async def get_my_proposals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's submitted proposals."""
    proposals = db.query(MarketProposal).filter(
        MarketProposal.user_id == current_user.id
    ).order_by(MarketProposal.created_at.desc()).all()
    
    result = []
    for p in proposals:
        response = ProposalResponse.model_validate(p)
        response.username = current_user.username
        result.append(response)
    
    return result


# Admin endpoints
@router.get("/admin/pending", response_model=List[ProposalResponse])
async def get_pending_proposals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all pending proposals (admin only)."""
    proposals = db.query(MarketProposal).filter(
        MarketProposal.status == ProposalStatus.pending.value
    ).order_by(MarketProposal.created_at.asc()).all()
    
    result = []
    for p in proposals:
        response = ProposalResponse.model_validate(p)
        user = db.query(User).filter(User.id == p.user_id).first()
        response.username = user.username if user else "Unknown"
        result.append(response)
    
    return result


@router.post("/admin/{proposal_id}/review", response_model=ProposalResponse)
async def review_proposal(
    proposal_id: int,
    review: ProposalReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Approve or reject a proposal (admin only)."""
    proposal = db.query(MarketProposal).filter(MarketProposal.id == proposal_id).first()
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    
    if proposal.status != ProposalStatus.pending.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proposal has already been reviewed"
        )
    
    proposal.reviewed_at = datetime.now()
    proposal.admin_notes = review.admin_notes
    
    if review.action == "approve":
        # Use modified values if provided, otherwise use original
        final_title = review.title or proposal.title
        final_description = review.description if review.description is not None else proposal.description
        final_category = review.category or proposal.category
        
        # Create the actual market
        market = Market(
            title=final_title,
            description=final_description,
            category=final_category,
            resolution_date=proposal.resolution_date,
            yes_price=0.5,
            no_price=0.5
        )
        db.add(market)
        db.flush()  # Get the market ID
        
        proposal.status = ProposalStatus.approved.value
        proposal.market_id = market.id
        
    else:  # reject
        proposal.status = ProposalStatus.rejected.value
    
    db.commit()
    db.refresh(proposal)
    
    user = db.query(User).filter(User.id == proposal.user_id).first()
    response = ProposalResponse.model_validate(proposal)
    response.username = user.username if user else "Unknown"
    
    return response
