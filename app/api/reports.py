"""
API endpoints for generating reports
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from typing import Optional
import csv
import json
import io
import logging

from app.api.dependencies import APIKey
from app.models import ChangeLog
from app.database.mongo import init_db

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = logging.getLogger(__name__)


@router.get("/changes/daily")
async def get_daily_change_report(
    api_key: APIKey,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)"),
    format: str = Query("json", pattern="^(json|csv)$", description="Output format: json or csv")
):
    """
    Generate a daily change report showing all changes for a specific date
    
    - **date**: Target date (YYYY-MM-DD), defaults to today
    - **format**: Output format (json or csv)
    
    Returns:
    - JSON: List of changes with full details
    - CSV: Downloadable CSV file
    """
    await init_db()
    
    # Parse date or use today
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        target_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get date range (full day)
    start_of_day = target_date
    end_of_day = target_date + timedelta(days=1)
    
    # Query changes for this day
    changes = await ChangeLog.find({
        "changed_at": {
            "$gte": start_of_day,
            "$lt": end_of_day
        }
    }).sort("-changed_at").to_list()
    
    if not changes:
        if format == "json":
            return {
                "date": target_date.strftime("%Y-%m-%d"),
                "total_changes": 0,
                "changes": [],
                "message": "No changes detected on this date"
            }
        else:
            # Return empty CSV
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Date", "Message"])
            writer.writerow([target_date.strftime("%Y-%m-%d"), "No changes detected"])
            
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=changes_{target_date.strftime('%Y%m%d')}.csv"}
            )
    
    # Format response
    if format == "json":
        # JSON response
        change_list = []
        for change in changes:
            change_dict = {
                "book_id": change.book_id,
                "book_name": change.book_name,
                "changed_at": change.changed_at.isoformat(),
                "change_type": change.change_type,
                "field_changed": change.field_changed,
                "old_value": str(change.old_value) if change.old_value is not None else None,
                "new_value": str(change.new_value) if change.new_value is not None else None,
                "description": change.description
            }
            change_list.append(change_dict)
        
        # Summary statistics
        summary = {
            "total_changes": len(changes),
            "new_books": sum(1 for c in changes if c.change_type == "new_book"),
            "updates": sum(1 for c in changes if c.change_type == "update"),
            "fields_changed": {}
        }
        
        for change in changes:
            if change.field_changed:
                summary["fields_changed"][change.field_changed] = summary["fields_changed"].get(change.field_changed, 0) + 1
        
        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": summary,
            "changes": change_list
        }
    
    else:
        # CSV response
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Timestamp",
            "Book Name",
            "Change Type",
            "Field Changed",
            "Old Value",
            "New Value",
            "Description"
        ])
        
        # Data rows
        for change in changes:
            writer.writerow([
                change.changed_at.strftime("%Y-%m-%d %H:%M:%S"),
                change.book_name,
                change.change_type,
                change.field_changed or "N/A",
                str(change.old_value) if change.old_value is not None else "N/A",
                str(change.new_value) if change.new_value is not None else "N/A",
                change.description or ""
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=changes_{target_date.strftime('%Y%m%d')}.csv"}
        )


@router.get("/summary/daily")
async def get_daily_summary(
    api_key: APIKey,
    days: int = Query(7, ge=1, le=90, description="Number of days to include (1-90)")
):
    """
    Get a summary of changes over the past N days
    
    - **days**: Number of days to include (default: 7)
    
    Returns daily statistics including:
    - Total changes per day
    - New books per day
    - Updates per day
    - Most changed fields
    """
    await init_db()
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get all changes in range
    changes = await ChangeLog.find({
        "changed_at": {
            "$gte": start_date,
            "$lt": end_date
        }
    }).to_list()
    
    # Group by date
    daily_stats = {}
    field_changes = {}
    
    for change in changes:
        date_key = change.changed_at.strftime("%Y-%m-%d")
        
        if date_key not in daily_stats:
            daily_stats[date_key] = {
                "date": date_key,
                "total_changes": 0,
                "new_books": 0,
                "updates": 0
            }
        
        daily_stats[date_key]["total_changes"] += 1
        
        if change.change_type == "new_book":
            daily_stats[date_key]["new_books"] += 1
        elif change.change_type == "update":
            daily_stats[date_key]["updates"] += 1
        
        # Track field changes
        if change.field_changed:
            field_changes[change.field_changed] = field_changes.get(change.field_changed, 0) + 1
    
    return {
        "period": {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "days": days
        },
        "totals": {
            "total_changes": len(changes),
            "total_new_books": sum(1 for c in changes if c.change_type == "new_book"),
            "total_updates": sum(1 for c in changes if c.change_type == "update")
        },
        "daily_breakdown": sorted(daily_stats.values(), key=lambda x: x["date"], reverse=True),
        "most_changed_fields": dict(sorted(field_changes.items(), key=lambda x: x[1], reverse=True))
    }

