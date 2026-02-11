import google.generativeai as genai
import os
import json
from PIL import Image

# Tamara API key thi configure karo
genai.configure(api_key="AIzaSyBrnVIqCR3lorCL2mEtMY_MZyI8lF_ZCnU")

def get_songs_for_multiple_images(folder_path):
    # 1. Folder check karvo ane files list karvi
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' nathi maltu.")
        return

    all_files = os.listdir(folder_path)
    
    # Khali image files filter karvani (png, jpg, jpeg)
    image_files = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    # Sorting (optional) - jethi dar vakhte order same rahe
    image_files.sort()

    # 2. Logic: Khali pehla 3 j images pick karvana
    selected_files = image_files[:3]
    
    if not selected_files:
        print("Koi images nathi folder ma.")
        return

    print(f"Processing these images: {selected_files}")

    # Images ne PIL format ma open karvi padse API mate
    loaded_images = []
    for file_name in selected_files:
        img_path = os.path.join(folder_path, file_name)
        loaded_images.append(Image.open(img_path))

    # 3. Updated Prompt (JSON output mate)
    prompt = """
    Analyze the attached 3 images.
    For EACH image, identify the perfect Bollywood song (Hindi).

    CRITICAL INSTRUCTION FOR LYRICS:
    - You MUST quote the EXACT EXISTING lyrics from the real song.
    - Do NOT write lyrics based on what you see in the image (e.g., if there is a horse, do not write lyrics about horses unless the real song has them).
    - If you don't know the exact lyrics, choose a different song.
    
    Return result as a JSON array with exactly 3 objects:
    [
      {
        "image_index": 1, 
        "song_title": "Title - Movie",
        "lyrics": "Real lyrics here (Hindi/Hinglish)"
      }
    ]
    Output ONLY raw JSON.
    
    """
    # 4. SINGLE API CALL: Prompt ane badhi images ek sathe list ma pass karvani
    # List structure: [Prompt Text, Image1, Image2, Image3]
    content_payload = [prompt] + loaded_images

    try:
        # Model select karo (Flash fast che, Pro vadhare smart che)
        model = genai.GenerativeModel('gemini-2.5-flash') 
        
        response = model.generate_content(content_payload)
        
        # 5. Response Parsing
        # Kadi vaar API code block (```json) ma response ape, ene clean karvo pade
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        
        results = json.loads(clean_text)

        # Output jova mate loop
        for i, item in enumerate(results):
            original_filename = selected_files[i] # File name match karva mate
            print(f"\n--- Result for: {original_filename} ---")
            print(f"Song: {item.get('song_title')}")
            print(f"Lyrics: {item.get('lyrics')}")

        return results

    except Exception as e:
        print("Error aavi:", e)
        # Debugging mate raw response jovu pade
        if 'response' in locals():
            print("Raw Response:", response.text)

# Function Call
# Tamaru folder 'photos' current directory ma hovu joie
get_songs_for_multiple_images("photos")