from google import genai
from sheets import get_sheet, get_client_history, mark_resolved
from datetime import datetime

from dotenv import load_dotenv
import os
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def parse_days(days_value):
    """Safely parse days pending value"""

    if str(days_value).lower() == "paid":
        return "paid"
    try:
        return int(days_value)
    except:
        return None
def parse_balance(balance_value):
    """Convert '₹31,000.00' → 31000.0"""
    try:
        if balance_value == "" or balance_value is None:
            return 0
        # Remove ₹, commas, spaces
        cleaned = str(balance_value).replace("₹", "").replace(",", "").strip()
        return float(cleaned)
    except:
        return 0
    
def get_priority_by_days(days):
    """State1 - no call history, decide purely on days pending"""
    if days < 6:
        return "skip", "Too early, less than 6 days"
    elif 6 <= days <=15:
        return "MEDIUM", None
    elif days > 15:
        return "HIGH", None



def ask_gemini(client_name, balance, days, history):
    """State2 - has call history, ask Gemini to reason"""

    history_text = ""
    for i, log in enumerate(reversed(history), 1):  # most recent first
        history_text += f"""
    Call {i}:
    - Date: {log.get('Date', '-')}
    - Status: {log.get('Call Status', '-')}
    - What client said: {log.get('What Client Said', '-')}
    - Promise Date: {log.get('Promise Date', '-')}
    - Notes: {log.get('Notes', '-')}
    """

    today = datetime.now().strftime("%d/%m/%Y")

    prompt = f"""
    You are a collections assistant for a logistics company in India.
    Today's date is {today}.

    Client: {client_name}
    Balance Pending: ₹{balance}
    Days Pending: {days}

    Call History (most recent first):
    {history_text}

    Based on this call history, should we call this client TODAY?

    Consider:
    - If client gave a promise date that hasn't passed yet -> NO, wait
    - If client gave a promise date that has passed and still unpaid -> YES, broken promise
    - If client was not reachable last time -> YES, try again
    - If client asked to call back on a specific date -> check if that date is today or passed

    Reply in this exact format:
    DECISION: YES or NO
    REASON: one line explanation
    PRIORITY: HIGH or MEDIUM or LOW (only if YES)
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt)
    
    return response.text.strip()


def parse_gemini_response(response_text):
    """Parse Gemini's structured response"""
    lines = response_text.strip().split("\n")
    result = {}
    for line in lines:
        if line.startswith("DECISION:"):
            result["decision"] = line.replace("DECISION:", "").strip()
        elif line.startswith("REASON:"):
            result['reason'] = line.replace("REASON:","").strip()
        elif line.startswith("PRIORITY:"):
            result['priority'] = line.replace("PRIORITY:","").strip()

    return result


def generate_call_list(sheet_name):
    """
    Agent1 - Main orchestration function
    State 1: No call history -> Python logic on days pending
    State 2: Has call history -> Gemini reasons
    """
    data = get_sheet(sheet_name)
    all_logs = get_sheet("Agent_Call_Logs")

    high_priority = []
    medium_priority = []
    skipped = []

    for row in data:
        client_name = row.get("Client Name", "")
        balance = parse_balance(row.get("Balance", 0))
        days_raw = row.get("Days_Pending", 0)
        remarks = row.get("Remarks","")

        days = parse_days(days_raw)
        if days == "paid" or balance == 0:

            unresolved = [
                r for r in all_logs
                if r["Client Name"].strip().lower() == client_name.strip().lower()
                and r.get("Status", "").strip() != "Resolved"
        
            ]
            if unresolved:
                mark_resolved(client_name)
            skipped.append({**row, "skip_reason": "Already paid"})
            continue
        if days is None:
            skipped.append({**row, "skip_reason": "Invalid days value"})
            continue
        
        history = get_client_history(client_name, all_logs)

        #### STATE 1 -  Never called before ####

        if len(history) == 0:
            priority, skip_reason = get_priority_by_days(days)

            if priority == "skip":
                skipped.append({**row, "skip_reason": skip_reason})
                continue
            row["priority"] = priority
            row["decision_basis"] = "Days Pending (first contact)"
            row["remarks_display"] = remarks

            if priority == "HIGH":
                high_priority.append(row)
            else:
                medium_priority.append(row)

        #### STATE2 - Has call history
        else:
            gemini_raw = ask_gemini(client_name, balance, days, history)
            gemini = parse_gemini_response(gemini_raw)
            decision = gemini.get("decision", "NO")
            reason = gemini.get("reason","")
            priority = gemini.get("priority","MEDIUM")

            if decision == "NO":
                skipped.append({**row, "skip_reason":reason})
                continue
            priority_map = {
            "HIGH": "HIGH",
            "MEDIUM": "MEDIUM",
            "LOW": "LOW"
            }
            row["priority"] = priority_map.get("priority", "MEDIUM")
            row["decision_basis"] = f"Gemini - {reason}"
            row["remarks_display"] = history[-1].get("What Client Said", remarks)

            if priority == "HIGH":
                high_priority.append(row)
            else:
                medium_priority.append(row)
    call_list = high_priority + medium_priority
    return call_list, skipped



if __name__ == "__main__":
    try:
        call_list, skipped = generate_call_list("Agent_COPY---To_Pay & To_billed - clients_ledger[1 Aug-]")
        print(f"\n TODAY's CALL LIST - {len(call_list)} clients\n")
        for i, row in enumerate(call_list, 1):
            print(f"{i}. {row['Client Name']} | {row['Balance']} | {row['Days_Pending']} days | {row['priority']}")
            print(f"  Basis: {row['decision_basis']}")
            print()
        print(f"\n --> SKIPPED - {len(skipped)} clients\n")
        for row in skipped:
            print(f"- {row.get('Client Name', '-')} - {row.get('skip_reason', '-')}")
    except Exception as e:
        import traceback
        traceback.print_exc()
# if __name__ == "__main__":
#     data = get_sheet("Agent_COPY---To_Pay & To_billed - clients_ledger[1 Aug-]")
    
#     for row in data:
#         print(f"  {row.get('Client Name')} → '{row.get('Days_Pending')}' | Balance: '{row.get('Balance')}'")
#     call_list, skipped = generate_call_list("Agent_COPY---To_Pay & To_billed - clients_ledger[1 Aug-]")

#     print(f"\n TODAY's CALL LIST - {len(call_list)} clients\n")
#     for i, row in enumerate(call_list, 1):
#         print(f"{i}. {row['Client Name']} | ₹{row['Balance']} | {row['Days Pending']} days | {row['priority']}")
#         print(f"  Basis: {row['decision_basis']}")
#         print(f"  Last remark: {row['remark_display']}")
#         print()

#     print(f"\n --> SKIPPED - {len(skipped)} clients\n")

#     for row in skipped:
#         print(f"- {row.get("Client Name", '-')} - {row.get('skip_reason', '-')}")
