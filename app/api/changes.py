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


@router.get("")
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
        
        # Get ALL changes matching filter (we'll group then paginate)
        all_changes = await ChangeLog.find(query_filter).sort('-changed_at').to_list()
        
        # Group changes by timestamp and book
        from collections import defaultdict
        
        # First group by timestamp (to second precision)
        events_by_time = defaultdict(list)
        for change in all_changes:
            timestamp_key = change.changed_at.replace(microsecond=0).isoformat()
            events_by_time[timestamp_key].append(change)
        
        # Build grouped events
        grouped_events = []
        for timestamp, changes_at_time in sorted(events_by_time.items(), reverse=True):
            # Group by book within this timestamp
            books_affected = defaultdict(list)
            for change in changes_at_time:
                books_affected[change.book_id].append(change)
            
            # Build book entries
            book_entries = []
            for book_id, book_changes in books_affected.items():
                change_type = book_changes[0].change_type
                book_name = book_changes[0].book_name
                
                # Build field changes
                field_changes = []
                for change in book_changes:
                    if change.change_type != 'new_book':
                        field_changes.append({
                            "field": change.field_changed,
                            "old_value": change.old_value,
                            "new_value": change.new_value,
                            "description": change.description
                        })
                
                book_entries.append({
                    "book_id": book_id,
                    "book_name": book_name,
                    "change_type": change_type,
                    "total_fields_changed": len(field_changes),
                    "fields": field_changes,
                    "summary": ", ".join([f["field"] for f in field_changes]) if field_changes else "New book added"
                })
            
            grouped_events.append({
                "changed_at": timestamp,
                "total_books_affected": len(book_entries),
                "total_fields_changed": sum(len(b["fields"]) for b in book_entries),
                "books": book_entries
            })
        
        # Apply pagination to grouped events
        total_events = len(grouped_events)
        total_pages = math.ceil(total_events / limit) if total_events > 0 else 1
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_events = grouped_events[start_idx:end_idx]
        
        logger.info(f"Returned {total} total changes ({total_events} events, page {page}/{total_pages})")
        
        return {
            "total_changes": total,
            "total_events": total_events,
            "page": page,
            "limit": limit,
            "pages": total_pages,
            "events": paginated_events
        }
        
    except Exception as e:
        logger.error(f"Error fetching changes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch changes"
        )
