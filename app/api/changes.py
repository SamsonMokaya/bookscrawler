"""
Changes/History API endpoints
"""
from fastapi import APIRouter, Query, HTTPException, status, Path
from typing import Optional
from datetime import datetime
import logging
import math

from app.models import ChangeLog, Book
from app.api.schemas import ChangeResponse, ChangesListResponse, BookHistoryResponse
from app.api.dependencies import APIKey

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/changes", tags=["changes"])


@router.get("", response_model=ChangesListResponse)
async def get_changes(
    api_key: APIKey,
    book_id: Optional[str] = Query(None, description="Filter by specific book ID"),
    change_type: Optional[str] = Query(None, description="Filter by change type (new_book, update, deleted)"),
    field_changed: Optional[str] = Query(None, description="Filter by field (price_incl_tax, availability, etc.)"),
    start_date: Optional[datetime] = Query(None, description="Changes after this date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Changes before this date (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Results per page (max 200)")
):
    """
    Get change history with filters and pagination
    
    **Filters:**
    - `book_id`: Filter changes for a specific book
    - `change_type`: Filter by change type (new_book, update, deleted)
    - `field_changed`: Filter by specific field that changed
    - `start_date`: Show changes after this date
    - `end_date`: Show changes before this date
    
    **Pagination:**
    - `page`: Page number (starts at 1)
    - `limit`: Number of results per page (1-200)
    
    **Returns:**
    - List of change log entries sorted by most recent first
    """
    try:
        # Build query filter
        query_filter = {}
        
        if book_id:
            query_filter['book_id'] = book_id
        
        if change_type:
            query_filter['change_type'] = change_type
        
        if field_changed:
            query_filter['field_changed'] = field_changed
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter['$gte'] = start_date
            if end_date:
                date_filter['$lte'] = end_date
            query_filter['changed_at'] = date_filter
        
        # Get total count
        total = await ChangeLog.find(query_filter).count()
        
        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = math.ceil(total / limit) if total > 0 else 1
        
        # Execute query with pagination (sorted by most recent first)
        changes = await ChangeLog.find(query_filter).sort('-changed_at').skip(skip).limit(limit).to_list()
        
        # Convert to response model
        change_responses = [
            ChangeResponse(
                id=str(change.id),
                book_id=change.book_id,
                book_name=change.book_name,
                change_type=change.change_type,
                field_changed=change.field_changed,
                old_value=change.old_value,
                new_value=change.new_value,
                changed_at=change.changed_at
            )
            for change in changes
        ]
        
        logger.info(f"Returned {len(change_responses)} changes (page {page}/{total_pages})")
        
        return ChangesListResponse(
            total=total,
            page=page,
            limit=limit,
            pages=total_pages,
            changes=change_responses
        )
        
    except Exception as e:
        logger.error(f"Error fetching changes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch changes"
        )


@router.get("/books/{book_id}/history")
async def get_book_history(
    book_id: str = Path(..., description="Book ID"),
    api_key: APIKey = None
):
    """
    Get complete change history for a specific book
    
    **Path Parameters:**
    - `book_id`: The unique identifier of the book
    
    **Returns:**
    - Complete change history for the book, sorted by most recent first
    
    **Errors:**
    - 404: Book not found
    """
    try:
        # Check if book exists
        book = await Book.get(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with ID '{book_id}' not found"
            )
        
        # Get all changes for this book
        changes = await ChangeLog.find(
            ChangeLog.book_id == book_id
        ).sort('-changed_at').to_list()
        
        # Group changes by timestamp (same crawl = same second)
        from collections import defaultdict
        grouped_changes = defaultdict(list)
        
        for change in changes:
            # Round to second for grouping (changes in same crawl)
            timestamp_key = change.changed_at.replace(microsecond=0).isoformat()
            grouped_changes[timestamp_key].append(change)
        
        # Build grouped response
        grouped_response = []
        for timestamp, change_group in sorted(grouped_changes.items(), reverse=True):
            # Build field changes for this timestamp
            field_changes = []
            change_type = change_group[0].change_type
            
            for change in change_group:
                if change.change_type == 'new_book':
                    # New book entry (no field changes)
                    pass
                else:
                    field_changes.append({
                        "field": change.field_changed,
                        "old_value": change.old_value,
                        "new_value": change.new_value,
                        "description": change.description
                    })
            
            grouped_entry = {
                "changed_at": timestamp,
                "change_type": change_type,
                "total_fields_changed": len(field_changes),
                "fields": field_changes,
                "summary": ", ".join([f["field"] for f in field_changes]) if field_changes else "New book added"
            }
            grouped_response.append(grouped_entry)
        
        logger.info(f"Returned {len(changes)} total changes ({len(grouped_response)} events) for book: {book.name}")
        
        return {
            "book_id": book_id,
            "book_name": book.name,
            "total_changes": len(changes),
            "total_events": len(grouped_response),
            "changes": grouped_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching book history for {book_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch book history"
        )
