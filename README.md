# HitTrax Automator

Automating the extraction of baseball statistics from HitTrax session images using Google Vertex AI (Gemini 1.5 Pro).

## Setup

1.  **Environment**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Authentication**:
    *   Create a Google Cloud Project.
    *   **Enable Billing**: Required for Vertex AI.
    *   **Enable Vertex AI API**.
    *   Create a Service Account and download the JSON key.
    *   Update `hittrax-automator.credentials.json`:
        ```json
        {
            "project_id": "your-project-id",
            "location": "us-central1",
            "service_account_file": "path/to/your-key.json",
            "model_name": "gemini-2.5-pro",
            "sheet_id": "your-google-sheet-id"
        }
        ```

3.  **Billing & Limits**:
    *   To prevent excessive costs, go to **Billing** > **Budgets & Alerts** in the GCP Console.
    *   Set a budget (e.g., $10/month) to receive email notifications.
    *   *Note: GCP does not inherently "hard stop" billing without custom scripts. Use Quotas to limit API request rates.*

## Usage

*   **Streamlit App**: `streamlit run app.py` for the web interface.
*   **Test Parser**: Run `python test_parser.py` to process images in `test/images/`.
*   **Main**: `python main.py` (Currently allows integration into other scripts).
