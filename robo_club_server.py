from mcp.server.fastmcp import FastMCP
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import re

load_dotenv()

mcp = FastMCP("google-sheets-manager")

# Google Sheets API Setup
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

def get_sheets_service():
    """Initialize Google Sheets API service with error handling"""
    try:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        
        creds = ServiceAccountCredentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        return build('sheets', 'v4', credentials=creds)
    except Exception as e:
        raise Exception(f"Failed to initialize Google Sheets API: {str(e)}")

# Initialize service
service = get_sheets_service()

# ======================================================================
# CORE SPREADSHEET OPERATIONS
# ======================================================================

@mcp.tool()
def create_spreadsheet(title: str, sheet_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Create a new Google Spreadsheet.
    
    Args:
        title: Name of the spreadsheet
        sheet_names: Optional list of sheet names to create (default: ["Sheet1"])
    
    Returns:
        Dictionary with spreadsheet_id and spreadsheet_url
    
    Example:
        create_spreadsheet("Robotics Club Data", ["Attendance", "Inventory", "Schedule"])
    """
    try:
        sheets = []
        if sheet_names:
            sheets = [{"properties": {"title": name}} for name in sheet_names]
        else:
            sheets = [{"properties": {"title": "Sheet1"}}]
        
        spreadsheet = {
            "properties": {"title": title},
            "sheets": sheets
        }
        
        result = service.spreadsheets().create(body=spreadsheet).execute()
        
        return {
            "success": True,
            "spreadsheet_id": result["spreadsheetId"],
            "spreadsheet_url": result["spreadsheetUrl"],
            "message": f"Spreadsheet '{title}' created successfully"
        }
    except HttpError as e:
        return {"success": False, "error": f"API error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


@mcp.tool()
def get_spreadsheet_info(spreadsheet_id: str) -> Dict[str, Any]:
    """
    Get information about a spreadsheet including all sheet names.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
    
    Returns:
        Information about the spreadsheet and its sheets
    """
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        
        sheets_info = []
        for sheet in spreadsheet.get('sheets', []):
            props = sheet['properties']
            sheets_info.append({
                "sheet_id": props['sheetId'],
                "title": props['title'],
                "index": props['index'],
                "row_count": props['gridProperties']['rowCount'],
                "column_count": props['gridProperties']['columnCount']
            })
        
        return {
            "success": True,
            "spreadsheet_title": spreadsheet['properties']['title'],
            "spreadsheet_id": spreadsheet['spreadsheetId'],
            "spreadsheet_url": spreadsheet['spreadsheetUrl'],
            "sheets": sheets_info,
            "sheet_count": len(sheets_info)
        }
    except HttpError as e:
        return {"success": False, "error": f"API error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


# ======================================================================
# SHEET MANAGEMENT
# ======================================================================

@mcp.tool()
def create_sheet(spreadsheet_id: str, sheet_name: str, row_count: int = 1000, column_count: int = 26) -> Dict[str, Any]:
    """
    Create a new sheet/tab in an existing spreadsheet.
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Name for the new sheet
        row_count: Number of rows (default: 1000)
        column_count: Number of columns (default: 26)
    
    Example:
        create_sheet("SHEET_ID", "Attendance", 500, 10)
    """
    try:
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name,
                        'gridProperties': {
                            'rowCount': row_count,
                            'columnCount': column_count
                        }
                    }
                }
            }]
        }
        
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=request_body
        ).execute()
        
        sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
        
        return {
            "success": True,
            "sheet_id": sheet_id,
            "sheet_name": sheet_name,
            "message": f"Sheet '{sheet_name}' created successfully"
        }
    except HttpError as e:
        return {"success": False, "error": f"API error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


@mcp.tool()
def delete_sheet(spreadsheet_id: str, sheet_name: str) -> Dict[str, Any]:
    """
    Delete a sheet from a spreadsheet.
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Name of the sheet to delete
    """
    try:
        # Get sheet ID from name
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_id = None
        
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == sheet_name:
                sheet_id = sheet['properties']['sheetId']
                break
        
        if sheet_id is None:
            return {"success": False, "error": f"Sheet '{sheet_name}' not found"}
        
        request_body = {
            'requests': [{
                'deleteSheet': {
                    'sheetId': sheet_id
                }
            }]
        }
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=request_body
        ).execute()
        
        return {
            "success": True,
            "message": f"Sheet '{sheet_name}' deleted successfully"
        }
    except HttpError as e:
        return {"success": False, "error": f"API error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


@mcp.tool()
def rename_sheet(spreadsheet_id: str, old_name: str, new_name: str) -> Dict[str, Any]:
    """
    Rename a sheet in a spreadsheet.
    
    Args:
        spreadsheet_id: Google Sheet ID
        old_name: Current name of the sheet
        new_name: New name for the sheet
    """
    try:
        # Get sheet ID from name
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_id = None
        
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == old_name:
                sheet_id = sheet['properties']['sheetId']
                break
        
        if sheet_id is None:
            return {"success": False, "error": f"Sheet '{old_name}' not found"}
        
        request_body = {
            'requests': [{
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': sheet_id,
                        'title': new_name
                    },
                    'fields': 'title'
                }
            }]
        }
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=request_body
        ).execute()
        
        return {
            "success": True,
            "message": f"Sheet renamed from '{old_name}' to '{new_name}'"
        }
    except HttpError as e:
        return {"success": False, "error": f"API error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


# ======================================================================
# DATA OPERATIONS - READ
# ======================================================================

@mcp.tool()
def read_range(spreadsheet_id: str, range_name: str) -> Dict[str, Any]:
    """
    Read data from a specific range in a sheet.
    
    Args:
        spreadsheet_id: Google Sheet ID
        range_name: Range in A1 notation (e.g., "Sheet1!A1:D10" or "Attendance!A:D")
    
    Returns:
        Data from the specified range
    
    Example:
        read_range("SHEET_ID", "Attendance!A1:D100")
    """
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        return {
            "success": True,
            "range": range_name,
            "row_count": len(values),
            "column_count": len(values[0]) if values else 0,
            "data": values
        }
    except HttpError as e:
        return {"success": False, "error": f"API error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


@mcp.tool()
def read_entire_sheet(spreadsheet_id: str, sheet_name: str) -> Dict[str, Any]:
    """
    Read all data from a sheet.
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Name of the sheet to read
    
    Returns:
        All data from the sheet
    """
    return read_range(spreadsheet_id, f"{sheet_name}")


@mcp.tool()
def read_with_headers(spreadsheet_id: str, sheet_name: str) -> Dict[str, Any]:
    """
    Read data from a sheet and parse it with headers (first row as keys).
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Name of the sheet
    
    Returns:
        Data as list of dictionaries with headers as keys
    """
    try:
        result = read_range(spreadsheet_id, sheet_name)
        
        if not result.get("success"):
            return result
        
        data = result.get("data", [])
        
        if len(data) < 2:
            return {
                "success": True,
                "headers": data[0] if data else [],
                "rows": [],
                "message": "No data rows found (only headers or empty)"
            }
        
        headers = data[0]
        rows = []
        
        for row_data in data[1:]:
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header] = row_data[i] if i < len(row_data) else ""
            rows.append(row_dict)
        
        return {
            "success": True,
            "headers": headers,
            "rows": rows,
            "row_count": len(rows)
        }
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


# ======================================================================
# DATA OPERATIONS - WRITE
# ======================================================================

@mcp.tool()
def write_range(spreadsheet_id: str, range_name: str, values: List[List[Any]], value_input_option: str = "RAW") -> Dict[str, Any]:
    """
    Write data to a specific range in a sheet.
    
    Args:
        spreadsheet_id: Google Sheet ID
        range_name: Range in A1 notation (e.g., "Sheet1!A1:D10")
        values: 2D list of values to write
        value_input_option: "RAW" or "USER_ENTERED" (formulas will be evaluated)
    
    Example:
        write_range("SHEET_ID", "Sheet1!A1:B2", [["Name", "Age"], ["John", 25]])
    """
    try:
        body = {"values": values}
        
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body=body
        ).execute()
        
        return {
            "success": True,
            "updated_cells": result.get('updatedCells'),
            "updated_rows": result.get('updatedRows'),
            "updated_columns": result.get('updatedColumns'),
            "message": f"Data written to {range_name}"
        }
    except HttpError as e:
        return {"success": False, "error": f"API error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


@mcp.tool()
def append_rows(spreadsheet_id: str, sheet_name: str, values: List[List[Any]], value_input_option: str = "RAW") -> Dict[str, Any]:
    """
    Append rows to the end of a sheet.
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Name of the sheet
        values: 2D list of values to append
        value_input_option: "RAW" or "USER_ENTERED"
    
    Example:
        append_rows("SHEET_ID", "Attendance", [["John Doe", "2025-01-15", "Present"]])
    """
    try:
        body = {"values": values}
        
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:A",
            valueInputOption=value_input_option,
            body=body
        ).execute()
        
        return {
            "success": True,
            "updated_range": result.get('updates', {}).get('updatedRange'),
            "updated_rows": result.get('updates', {}).get('updatedRows'),
            "message": f"Appended {len(values)} row(s) to {sheet_name}"
        }
    except HttpError as e:
        return {"success": False, "error": f"API error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


@mcp.tool()
def set_headers(spreadsheet_id: str, sheet_name: str, headers: List[str]) -> Dict[str, Any]:
    """
    Set or update the header row (first row) of a sheet.
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Name of the sheet
        headers: List of header names
    
    Example:
        set_headers("SHEET_ID", "Attendance", ["Student Name", "Date", "Status", "Time"])
    """
    return write_range(
        spreadsheet_id, 
        f"{sheet_name}!A1:{chr(64 + len(headers))}1", 
        [headers]
    )


@mcp.tool()
def clear_range(spreadsheet_id: str, range_name: str) -> Dict[str, Any]:
    """
    Clear data from a specific range (keeps formatting).
    
    Args:
        spreadsheet_id: Google Sheet ID
        range_name: Range in A1 notation (e.g., "Sheet1!A1:D10")
    """
    try:
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            body={}
        ).execute()
        
        return {
            "success": True,
            "message": f"Cleared data from {range_name}"
        }
    except HttpError as e:
        return {"success": False, "error": f"API error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


@mcp.tool()
def clear_sheet(spreadsheet_id: str, sheet_name: str) -> Dict[str, Any]:
    """
    Clear all data from a sheet.
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Name of the sheet to clear
    """
    return clear_range(spreadsheet_id, sheet_name)


# ======================================================================
# DATA OPERATIONS - UPDATE & DELETE
# ======================================================================

@mcp.tool()
def update_cell(spreadsheet_id: str, sheet_name: str, cell: str, value: Any, value_input_option: str = "RAW") -> Dict[str, Any]:
    """
    Update a single cell.
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Name of the sheet
        cell: Cell reference (e.g., "A1", "B5")
        value: Value to write
        value_input_option: "RAW" or "USER_ENTERED"
    
    Example:
        update_cell("SHEET_ID", "Attendance", "A1", "Student Name")
    """
    return write_range(spreadsheet_id, f"{sheet_name}!{cell}", [[value]], value_input_option)


@mcp.tool()
def batch_update(spreadsheet_id: str, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform multiple updates in a single request.
    
    Args:
        spreadsheet_id: Google Sheet ID
        updates: List of update dictionaries with 'range' and 'values' keys
    
    Example:
        batch_update("SHEET_ID", [
            {"range": "Sheet1!A1", "values": [["Name"]]},
            {"range": "Sheet1!B1", "values": [["Age"]]}
        ])
    """
    try:
        data = []
        for update in updates:
            data.append({
                'range': update['range'],
                'values': update['values']
            })
        
        body = {
            'valueInputOption': 'RAW',
            'data': data
        }
        
        result = service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        
        return {
            "success": True,
            "total_updated_cells": result.get('totalUpdatedCells'),
            "total_updated_rows": result.get('totalUpdatedRows'),
            "responses": len(result.get('responses', [])),
            "message": f"Batch update completed with {len(updates)} operations"
        }
    except HttpError as e:
        return {"success": False, "error": f"API error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


# ======================================================================
# FORMATTING
# ======================================================================

@mcp.tool()
def format_header_row(spreadsheet_id: str, sheet_name: str, bold: bool = True, background_color: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Format the header row (first row) of a sheet.
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Name of the sheet
        bold: Make text bold (default: True)
        background_color: RGB color dict with 'red', 'green', 'blue' (0-1 range)
                         Example: {"red": 0.8, "green": 0.8, "blue": 0.8}
    """
    try:
        # Get sheet ID
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_id = None
        
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == sheet_name:
                sheet_id = sheet['properties']['sheetId']
                break
        
        if sheet_id is None:
            return {"success": False, "error": f"Sheet '{sheet_name}' not found"}
        
        requests = []
        
        # Bold text
        if bold:
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {"bold": True}
                        }
                    },
                    "fields": "userEnteredFormat.textFormat.bold"
                }
            })
        
        # Background color
        if background_color:
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": background_color
                        }
                    },
                    "fields": "userEnteredFormat.backgroundColor"
                }
            })
        
        if requests:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": requests}
            ).execute()
        
        return {
            "success": True,
            "message": f"Header row formatted in sheet '{sheet_name}'"
        }
    except HttpError as e:
        return {"success": False, "error": f"API error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


# ======================================================================
# SEARCH & FILTER
# ======================================================================

@mcp.tool()
def find_in_sheet(spreadsheet_id: str, sheet_name: str, search_text: str, case_sensitive: bool = False) -> Dict[str, Any]:
    """
    Search for text in a sheet and return matching cells with their positions.
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Name of the sheet
        search_text: Text to search for
        case_sensitive: Whether search should be case-sensitive
    
    Returns:
        List of matches with row, column, and value
    """
    try:
        result = read_entire_sheet(spreadsheet_id, sheet_name)
        
        if not result.get("success"):
            return result
        
        data = result.get("data", [])
        matches = []
        
        for row_idx, row in enumerate(data):
            for col_idx, cell_value in enumerate(row):
                cell_str = str(cell_value)
                search_str = search_text
                
                if not case_sensitive:
                    cell_str = cell_str.lower()
                    search_str = search_str.lower()
                
                if search_str in cell_str:
                    col_letter = chr(65 + col_idx) if col_idx < 26 else f"A{chr(65 + col_idx - 26)}"
                    matches.append({
                        "row": row_idx + 1,
                        "column": col_letter,
                        "cell": f"{col_letter}{row_idx + 1}",
                        "value": cell_value
                    })
        
        return {
            "success": True,
            "search_text": search_text,
            "matches_found": len(matches),
            "matches": matches
        }
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


# ======================================================================
# ROBOTICS CLUB SPECIFIC TOOLS
# ======================================================================

@mcp.tool()
def mark_attendance(spreadsheet_id: str, sheet_name: str, member_name: str, status: str = "Present", date: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Mark attendance for a club member.
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Sheet name (e.g., "Attendance")
        member_name: Name of the member
        status: Present/Absent/Late/Excused
        date: Date in YYYY-MM-DD format (defaults to today)
        notes: Optional notes
    
    Example:
        mark_attendance("SHEET_ID", "Attendance", "John Doe", "Present")
    """
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        row = [member_name, date, status, timestamp]
        if notes:
            row.append(notes)
        
        result = append_rows(spreadsheet_id, sheet_name, [row])
        
        if result.get("success"):
            result["message"] = f"Attendance marked: {member_name} - {status} on {date}"
        
        return result
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


@mcp.tool()
def add_inventory_item(spreadsheet_id: str, sheet_name: str, item_name: str, quantity: int, category: str, location: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Add an item to the inventory sheet.
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Sheet name (e.g., "Inventory")
        item_name: Name of the item
        quantity: Quantity available
        category: Category (e.g., "Electronics", "Tools", "Parts")
        location: Storage location
        notes: Additional notes
    """
    try:
        date_added = datetime.now().strftime("%Y-%m-%d")
        
        row = [item_name, quantity, category, location or "", date_added]
        if notes:
            row.append(notes)
        
        result = append_rows(spreadsheet_id, sheet_name, [row])
        
        if result.get("success"):
            result["message"] = f"Inventory item added: {item_name} (Qty: {quantity})"
        
        return result
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


@mcp.tool()
def log_project_activity(spreadsheet_id: str, sheet_name: str, project_name: str, activity: str, member_name: str, hours_spent: Optional[float] = None, date: Optional[str] = None) -> Dict[str, Any]:
    """
    Log project activity in the sheet.
    
    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Sheet name (e.g., "Project Log")
        project_name: Name of the project
        activity: Description of activity
        member_name: Name of member who worked on it
        hours_spent: Hours spent on activity
        date: Date (defaults to today)
    """
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        row = [date, timestamp, project_name, activity, member_name]
        if hours_spent is not None:
            row.append(hours_spent)
        
        result = append_rows(spreadsheet_id, sheet_name, [row])
        
        if result.get("success"):
            result["message"] = f"Activity logged: {project_name} - {activity}"
        
        return result
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


# ======================================================================
# HELPER: SETUP COMPLETE ROBOTICS CLUB SPREADSHEET
# ======================================================================

@mcp.tool()
def setup_robotics_club_spreadsheet(title: str = "Robotics Club Management") -> Dict[str, Any]:
    """
    Create a complete spreadsheet for robotics club with all necessary sheets and headers.
    
    Args:
        title: Title for the spreadsheet
    
    Returns:
        Complete setup information including spreadsheet ID and URL
    """
    try:
        # Create spreadsheet
        result = create_spreadsheet(title, ["Attendance", "Inventory", "Project Log", "Members", "Schedule"])
        
        if not result.get("success"):
            return result
        
        spreadsheet_id = result["spreadsheet_id"]
        
        # Setup Attendance sheet
        set_headers(spreadsheet_id, "Attendance", ["Member Name", "Date", "Status", "Time", "Notes"])
        format_header_row(spreadsheet_id, "Attendance", True, {"red": 0.8, "green": 0.9, "blue": 1.0})
        
        # Setup Inventory sheet
        set_headers(spreadsheet_id, "Inventory", ["Item Name", "Quantity", "Category", "Location", "Date Added", "Notes"])
        format_header_row(spreadsheet_id, "Inventory", True, {"red": 0.9, "green": 1.0, "blue": 0.8})
        
        # Setup Project Log sheet
        set_headers(spreadsheet_id, "Project Log", ["Date", "Time", "Project Name", "Activity", "Member Name", "Hours Spent"])
        format_header_row(spreadsheet_id, "Project Log", True, {"red": 1.0, "green": 0.9, "blue": 0.8})
        
        # Setup Members sheet
        set_headers(spreadsheet_id, "Members", ["Name", "Email", "Phone", "Join Date", "Role", "Status"])
        format_header_row(spreadsheet_id, "Members", True, {"red": 1.0, "green": 0.8, "blue": 0.9})
        
        # Setup Schedule sheet
        set_headers(spreadsheet_id, "Schedule", ["Date", "Time", "Event", "Location", "Description", "Coordinator"])
        format_header_row(spreadsheet_id, "Schedule", True, {"red": 0.9, "green": 0.8, "blue": 1.0})
        
        return {
            "success": True,
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_url": result["spreadsheet_url"],
            "sheets_created": ["Attendance", "Inventory", "Project Log", "Members", "Schedule"],
            "message": "Robotics club spreadsheet setup complete! All sheets configured with headers."
        }
    except Exception as e:
        return {"success": False, "error": f"Error during setup: {str(e)}"}


# ======================================================================
# RUN SERVER
# ======================================================================

if __name__ == "__main__":
    mcp.run(transport="stdio")