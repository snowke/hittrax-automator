import streamlit as st
import json
import os
import tempfile
from main import analyze_hittrax_image, initialize_application
import scripts.get_credentials as gc
from utils.sheets import upsert_row_to_sheet

st.set_page_config(page_title="HitTrax Automator", layout="wide")

st.title("⚾ HitTrax Automator")

# Initialize Backend
if 'client' not in st.session_state:
    with st.spinner('Initializing AI Model...'):
        init_result = initialize_application()
        if init_result:
            st.session_state.client, st.session_state.model_name = init_result
            st.success(f"Connected to Vertex AI (Model: {st.session_state.model_name})")
        else:
            st.error("Failed to initialize application. Check your credentials.")
            st.stop()

uploaded_file = st.file_uploader("Upload HitTrax Stats Image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display Image
    # Fix: use_container_width deprecated, use width="100%" or simple st.image without arg if we want default behavior, 
    # but the warning said for True use width='stretch' ?? Actually Streamlit docs say use_column_width is old, use_container_width is new but strict?
    # The warning received: "Please replace `use_container_width` with `width`."
    st.image(uploaded_file, caption='Uploaded Image', width='stretch') 
    
    # Process Button
    if st.button('Analyze Image'):
        with st.spinner('Analyzing stats...'):
            # Save temp file because analyze function expects a path
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                result_json_str = analyze_hittrax_image(tmp_path, st.session_state.client, st.session_state.model_name)
                
                # Cleanup temp file
                os.remove(tmp_path)
                
                # Try parsing JSON
                try:
                    data = json.loads(result_json_str)
                    
                    # Parse Date/Time from filename
                    # Expected format: PXL_YYYYMMDD_HHMMSS...
                    filename = uploaded_file.name
                    if filename.startswith("PXL_") and len(filename) >= 13:
                        try:
                            date_part = filename[4:12] # YYYYMMDD
                            time_part = filename[13:19] # HHMMSS
                            
                            formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}"
                            formatted_time = f"{time_part[:2]}:{time_part[2:4]}:{time_part[4:]}"
                            
                            data['date'] = formatted_date
                            data['time'] = formatted_time
                        except Exception:
                            st.warning("Could not parse date/time from filename.")
                    
                    # Add filename to data
                    data['filename'] = uploaded_file.name

                    st.session_state.analyzed_data = data
                    st.toast("Analysis Complete!", icon="✅")
                except json.JSONDecodeError:
                    st.error("Failed to parse AI response as JSON.")
                    st.text(result_json_str)
            
            except Exception as e:
                st.error(f"Error during analysis: {e}")

    # Editable Form
    if 'analyzed_data' in st.session_state:
        st.subheader("Edit & Submit Stats")
        
        with st.form("stats_form"):
            data = st.session_state.analyzed_data
            
            # Create two columns
            col1, col2 = st.columns(2)
            
            edited_data = {}
            
            # Context Info (Row 1)
            with col1:
                edited_data['date'] = st.text_input("Date", value=data.get('date', ''))
                edited_data['time'] = st.text_input("Time", value=data.get('time', ''))
                edited_data['player'] = st.text_input("Player", value=data.get('player', ''))
            with col2:
                edited_data['filename'] = st.text_input("Filename", value=data.get('filename', ''), disabled=True)
                edited_data['bat'] = st.text_input("Bat", value=data.get('bat', ''))
                edited_data['age_category'] = st.text_input("Age Category", value=data.get('age_category', ''))
            
            st.divider()
            
            keys = list(data.keys())
            # Filter out keys we already handled
            exclude_keys = ['player', 'bat', 'age_category', 'date', 'time', 'filename']
            keys = [k for k in keys if k not in exclude_keys]
            
            cols = st.columns(4)
            for i, key in enumerate(keys):
                col_idx = i % 4
                with cols[col_idx]:
                    val = data[key]
                    edited_data[key] = st.text_input(f"{key}", value=str(val))

            submitted = st.form_submit_button("Submit to Sheet")
            
            if submitted:
                # Merge the top fields back into edited_data
                # Actually they are already in edited_data dict from the calls above, 
                # but we need to fetch the latest values from the widgets?
                # No, st.form collects values on submit. 'edited_data' dict created above 
                # effectively captures the return values of st.text_input at the moment of render?
                
                # Careful: In st.form, the values are updated on RE-RUN after submit.
                # But when inside the `if submitted:` block, we want the values that were just submitted.
                # Since st.text_input returns the current value, and on submit the script reruns,
                # the values in `edited_data` are correct.
                
                # We need to construct the final payload
                final_payload = edited_data.copy()
                
                # Convert filename to Google Photos Search Hyperlink
                if 'filename' in final_payload and final_payload['filename']:
                    fname = final_payload['filename']
                    # Google Photos Search Link
                    # Formula: =HYPERLINK("https://photos.google.com/search/FILENAME", "FILENAME")
                    # Note: Search is case-insensitive usually, but filename should match.
                    link_formula = f'=HYPERLINK("https://photos.google.com/search/{fname}", "{fname}")'
                    final_payload['filename'] = link_formula
                
                creds = gc.get_credentials()
                if not creds:
                    st.error("Credentials not found!")
                else:
                    sheet_id = creds.get('sheet_id')
                    service_account_file = creds.get('service_account_file')
                    
                    if not sheet_id or sheet_id == "YOUR_SHEET_ID_HERE":
                        st.error("Please configure 'sheet_id' in hittrax-automator.credentials.json")
                    elif not service_account_file:
                         st.error("Service Account file not configured.")
                    else:
                        try:
                            with st.spinner("Syncing with Google Sheet..."):
                                msg = upsert_row_to_sheet(final_payload, service_account_file, sheet_id, worksheet_name="HitTrax Stats")
                            st.success(f"Success! {msg}")
                        except Exception as e:
                            st.error(f"Failed to submit to sheet: {e}")
