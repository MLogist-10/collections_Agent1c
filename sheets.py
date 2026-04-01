import gspread
from google.oauth2.service_account import Credentials

from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_client():
    creds = Credentials.from_service_account_file(
        "agent-acc-1-creds.json",
        scopes=SCOPES)

    return gspread.authorize(creds)
def mark_resolved(client_name):
    """Mark all call logs for a paid client as Resolved"""
    client = get_client()
    sheet = client.open("Agent_Call_Logs").sheet1
    all_rows = sheet.get_all_records()

    for i, row in enumerate(all_rows, start=2):
        if row["Client Name"].strip().lower() == client_name.strip().lower():
            if row.get("Status", "").strip() != "Resolved":
                sheet.update_cell(i, 8, "Resolved")

def get_sheet(sheet_name):
    ##read all rows from a sheet##
    client = get_client()
    sheet = client.open(sheet_name).sheet1
    return sheet.get_all_records()
    
    

def log_call(client_name, lr_no, call_status, what_client_said, promise_date, notes):
    ###write a new call log entry to call logs sheet###

    client = get_client()
    sheet = client.open("Agent_Call_Logs").sheet1

    row = [
        datetime.now().strftime("%d/%m/%Y %H:%M"),
        client_name,
        lr_no,
        call_status,
        what_client_said,
        promise_date,
        notes
    ]
    sheet.append_row(row)
    return True

def get_client_history(client_name, all_logs):
    ###Get all call Logs for a specific client###
    history = [row for row in all_logs 
               if row["Client Name"].strip().lower() == client_name.strip().lower()]
    return history


if __name__ == "__main__":
    # data = get_sheet("Agent_COPY---To_Pay & To_billed - clients_ledger[1 Aug-]")
    # for row in data:
    #     print(row)
    log_call(
        client_name="Test Party",
        lr_no="1234",
        call_status="Answered",
        what_client_said="Will Pay by friday",
        promise_date="04/04/2025",
        notes="Spoke to ownser directly"
    )
    print("Log written succesfully!")