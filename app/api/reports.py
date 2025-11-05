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

