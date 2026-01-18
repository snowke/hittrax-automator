import gspread
import os
import json

import datetime

def upsert_row_to_sheet(data_dict, service_account_file, sheet_id, worksheet_name=None):
    """
    Upserts a row of data to the specified Google Sheet.
    Matches primarily on 'filename' if present.
    Adds 'Created On' and 'Updated On' audit columns.
    
    Args:
        data_dict (dict): Dictionary of data to append. Keys will be headers.
        service_account_file (str): Path to the service account JSON key.
        sheet_id (str): The ID of the Google Sheet.
        worksheet_name (str): Optional name of the worksheet to open.
        
    Returns:
        str: Success message or raises Exception on failure.
    """
    if not os.path.exists(service_account_file):
        raise FileNotFoundError(f"Service account file not found: {service_account_file}")

    # Authenticate with gspread
    gc = gspread.service_account(filename=service_account_file)

    # Open the sheet
    try:
        sh = gc.open_by_key(sheet_id)
        if worksheet_name:
            try:
                worksheet = sh.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                raise Exception(f"Worksheet '{worksheet_name}' not found.")
        else:
            worksheet = sh.get_worksheet(0) # Open the first sheet
    except Exception as e:
        raise Exception(f"Failed to access sheet. Error: {e}")

    # Prepare Headers
    # We enforce 'Created On' and 'Updated On' at the end if they don't exist
    AUDIT_COLS = ['Created On', 'Updated On']
    
    try:
        headers = worksheet.row_values(1)
    except Exception:
        headers = []

    # If sheet is empty, add headers
    if not headers:
        headers = list(data_dict.keys())
        # Ensure audit cols are there
        for col in AUDIT_COLS:
            if col not in headers:
                headers.append(col)
        worksheet.append_row(headers)
    
    # Check for new keys in input data
    new_headers = [k for k in data_dict.keys() if k not in headers]
    if new_headers:
        headers.extend(new_headers)
        worksheet.update(range_name='A1', values=[headers])

    # Ensure Audit Cols exist in headers (in case sheet exists but lacks them)
    audit_indices = {}
    for col in AUDIT_COLS:
        if col not in headers:
            headers.append(col)
            worksheet.update(range_name='A1', values=[headers])
    
    # Map headers to indices (0-based for list access, but gspread 1-based usually? no list is 0)
    header_map = {h: i for i, h in enumerate(headers)}
    
    # Identify Key Column (Filename)
    KEY_COL = 'filename' # Use lowercase match? or 'Filename'?
    # data_dict keys are what we have. check if 'filename' in data_dict
    if KEY_COL not in data_dict:
        # Fallback if case mismatch?
        # For now assume 'filename' key exists as passed from app.py
        raise Exception(f"Key column '{KEY_COL}' missing from data.")

    key_value = data_dict.get(KEY_COL)
    
    # Fetch all data to find match
    # value_render_option='FORMULA' is crucial to match the =HYPERLINK formula string
    all_values = worksheet.get_all_values() 
    # all_values[0] is header, rows start at 1
    
    match_row_index = -1
    
    # Find column index for key
    if KEY_COL not in header_map:
         # Should have been added above if missing
         pass
    
    key_col_idx = header_map[KEY_COL]
    
    # Search for key
    # Skip header (row 0)
    for i in range(1, len(all_values)):
        row = all_values[i]
        if len(row) > key_col_idx and row[key_col_idx] == key_value:
            match_row_index = i # 0-based index in all_values list
            break
            
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Construct values for the row
    # If insert, we build fresh list. If update, we might merge? 
    # Easier to rebuild the whole row based on headers.
    
    row_values = []
    # If matching row found, pre-fill with existing values? 
    # No, we want to overwrite with new data input, EXCEPT audit 'Created On'
    
    existing_created_on = None
    if match_row_index != -1:
        # Get existing row
        existing_row = all_values[match_row_index]
        # Try to preserve Created On
        if 'Created On' in header_map:
            c_idx = header_map['Created On']
            if len(existing_row) > c_idx:
                existing_created_on = existing_row[c_idx]

    for header in headers:
        if header == 'Updated On':
            row_values.append(current_time_str)
        elif header == 'Created On':
            if existing_created_on:
                row_values.append(existing_created_on)
            else:
                row_values.append(current_time_str)
        else:
            # Get from data_dict, or empty string if not provided
            # Only existing columns in header map are considered
            row_values.append(str(data_dict.get(header, "")))

    if match_row_index != -1:
        # UPDATE
        # row index in sheet is match_row_index + 1 (1-based)
        row_num = match_row_index + 1
        # range A{row_num}
        # Update the entire row? 
        # worksheet.update(f"A{row_num}", [row_values], value_input_option='USER_ENTERED')
        
        # Determine cell range string: A{row}:[EndCol]{row} or just start cell
        # gspread update starts at range and fills
        worksheet.update(range_name=f"A{row_num}", values=[row_values], value_input_option='USER_ENTERED')
        return "Updated existing record."
    else:
        # INSERT
        worksheet.append_row(row_values, value_input_option='USER_ENTERED')
        return "Inserted new record."
