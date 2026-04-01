from sheets import get_client

client = get_client()
sheets = client.list_spreadsheet_files()
for s in sheets:
    print(s['name'])
