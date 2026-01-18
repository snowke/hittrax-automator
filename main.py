from google import genai
from google.genai import types
import scripts.get_credentials as gc
import os
import PIL.Image

def analyze_hittrax_image(image_path, client, model_name):
    """
    Analyzes a HitTrax image using Gemini to extract statistics.
    """
    print(f"Analyzing image: {image_path}")
    
    if not os.path.exists(image_path):
        return f"Error: Image not found at {image_path}"

    image = PIL.Image.open(image_path)
    
    prompt = """
    You are a data extraction specialist for youth baseball statistics. Look at the provided HitTrax image.

    Focus on the bottom black bar of the computer screen for session stats.

    Extract: Pitch Count (P), At Bats (AB), Hits (H), Extra Base Hits (EBH), Average (AVG), Line Drive % (LD%), Avg Exit Velocity (AvgVel), Max Exit Velocity (MaxVel), Max Distance (MaxDist), Max Points (MaxPoints), and Total Points (TotalPts).

    Look for the age category on the screen (e.g., '10U' or '8U').

    Logic Rule: If '10U' is found, set player='Caden' and bat='CatX 29"'. If '8U' is found, set player='Lucas' and bat='Cat7 27"'.

    Output the result strictly as a JSON object. Ensure 'age_category' is a key in the output (e.g., '10U', '8U', or 'Unknown').
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt, image]
        )
        text = response.text
        # Clean up code fences if Gemini adds them
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    except Exception as e:
        return f"Error during analysis: {e}"

def initialize_application():
    """
    Loads credentials, configures authentication, and initializes Vertex AI Client.
    Returns (client, model_name) or None on failure.
    """
    creds = gc.get_credentials()
    if not creds:
        return None

    project_id = creds.get("project_id")
    location = creds.get("location")
    service_account_file = creds.get("service_account_file")
    model_name = creds.get("model_name", "gemini-2.5-pro")

    if not project_id or project_id == "YOUR_PROJECT_ID":
        print("Please configure your 'project_id' in hittrax-automator.credentials.json")
        return None

    if service_account_file and service_account_file != "path/to/service-account-key.json":
        print(f"Setting credentials from: {service_account_file}")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_file
    
    print(f"Initializing Vertex AI Client with project: {project_id}, location: {location}")
    print(f"Using model: {model_name}")
    
    try:
        client = genai.Client(vertexai=True, project=project_id, location=location)
        return client, model_name
    except Exception as e:
        print(f"Failed to initialize Vertex AI Client: {e}")
        return None

def main():
    result = initialize_application()
    if not result:
        return
    
    client, model_name = result
    print("Application initialized successfully. Ready to analyze.")

if __name__ == "__main__":
    main()
