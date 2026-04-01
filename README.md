#Collection Agent


An AI-Powered collections management system for logistics businesses.
Built with Python, Streamlit, Google Sheets, and Gemini AI.

## What it does 

- Auto generates daily call list based on payment status
- Prioritizes clients by days pending
- Uses Gemini AI to reason on call history
- Caller logs outcomes via simple web interface
- Auto-resolves paid clients

## Tech Stack
- Python 3.12
- Streamlit - web interface
- Google Sheets API - data storage
- Gemini 2.5 Flash Lite - AI reasoning
- gspread - Google Sheets client

## Project Structure


collections-agent/
├── app.py              # Streamlit web app
├── agent1C.py          # Agent 1 — call planner
├── sheets.py           # Google Sheets interface
├── requirements.txt    # Dependencies
├── .env                # API keys (not pushed)
├── .gitignore          # Git ignore rules
└── README.md           # This file

## Setup
1. Clone the repo
2. Create virtual environment
   bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
```
3. Install dependencies
   bash
   pip install -r requirements.txt

4. Create `.env` file

   GEMINI_API_KEY=your_key_here
   GOOGLE_SHEET_NAME=your_sheet_name_here

5. Add `credentials.json` from Google Cloud Console
6. Run
   bash
   streamlit run app.py


## Environment Variables
| Variable | Description |
|---|---|
| GEMINI_API_KEY | Gemini API key from Google AI Studio |
| GOOGLE_SHEET_NAME | Exact name of your Google Sheets ledger |

## Note
credentials.json and .env are not pushed to GitHub.
Add them manually after cloning.
