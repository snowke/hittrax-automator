import glob
import os
from main import analyze_hittrax_image, initialize_application

def main():
    print("Starting Test Parser...")
    
    # 1. Initialize Application (Loads credentials & Model)
    init_result = initialize_application()
    if not init_result:
        print("Failed to initialize application.")
        return
    
    client, model_name = init_result

    # 3. Find Images
    # Looking in ./test/images/ for any .jpg files
    image_dir = os.path.join("test", "images")
    pattern = os.path.join(image_dir, "*.jpg")
    images = glob.glob(pattern)
    
    if not images:
        print(f"No images found matching {pattern}")
        return

    print(f"Found {len(images)} images in '{image_dir}'. Processing...\n")

    # 4. Run Analysis
    for img_path in images:
        print(f"="*40)
        print(f"Processing: {img_path}")
        try:
            result_json = analyze_hittrax_image(img_path, client, model_name)
            print("Result:")
            print(result_json)
        except Exception as e:
            print(f"ERROR analyzing {img_path}: {e}")
        print(f"="*40 + "\n")

    print("Test run complete.")

if __name__ == "__main__":
    main()
