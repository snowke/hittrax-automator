import vertexai
from vertexai.generative_models import GenerativeModel, Part
import scripts.get_credentials as gc
import os

def analyze_hittrax_image(image_path, model):
    """
    Analyzes a HitTrax image using Gemini to extract statistics.
    """
    print(f"Analyzing image: {image_path}")
    
    if not os.path.exists(image_path):
        return f"Error: Image not found at {image_path}"

    with open(image_path, "rb") as f:
        image_data = f.read()

    image_part = Part.from_data(data=image_data, mime_type="image/jpeg")
    
    prompt = """
    You are a data extraction specialist for youth baseball statistics. Look at the provided HitTrax image.

    Focus on the bottom black bar of the computer screen for session stats.

    Extract: Pitch Count (P), At Bats (AB), Hits (H), Extra Base Hits (EBH), Average (AVG), Line Drive % (LD%), Avg Exit Velocity (AvgVel), Max Exit Velocity (MaxVel), Max Distance (MaxDist), Max Points (MaxPoints), and Total Points (TotalPts).

    Look for the age category on the screen (e.g., '10U' or '8U').

    Logic Rule: If '10U' is found, set player='Caden' and bat='CatX 29"'. If '8U' is found, set player='Lucas' and bat='Cat7 27"'.

    Output the result strictly as a JSON object.
    """

    try:
        response = model.generate_content([prompt, image_part])
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
    Loads credentials, configures authentication, and initializes Vertex AI.
    Returns the initialized GenerativeModel or None on failure.
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
    
    print(f"Initializing Vertex AI with project: {project_id}, location: {location}")
    print(f"Using model: {model_name}")
    
    try:
        vertexai.init(project=project_id, location=location)
        model = GenerativeModel(model_name)
        return model
    except Exception as e:
        print(f"Failed to initialize Vertex AI: {e}")
        return None

def main():
    model = initialize_application()
    if not model:
        return
        
    print("Application initialized successfully. Ready to analyze.")

if __name__ == "__main__":
    main()
