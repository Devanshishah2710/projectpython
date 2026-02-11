import os
import google.generativeai as genai
from PIL import Image

# Configure Gemini
genai.configure(api_key="AIzaSyBrnVIqCR3lorCL2mEtMY_MZyI8lF_ZCnU")

# Use Gemini Pro Vision for image understanding
model = genai.GenerativeModel("models/gemini-2.5-flash")

def generate_song_from_image(image_path: str) -> str:
    image = Image.open(image_path)

    prompt = """
    Analyze the image mood, setting, and emotions. 
    Find the ONE perfect existing Bollywood song (Hindi) that matches this scene.
    
    Output ONLY:
    1. The Song Title & Movie Name.
    2. The exact 3-4 lines of lyrics (in Hinglish) that fit this specific moment.
    
    Do NOT write any introduction, explanation, or original poetry.
    """

    response = model.generate_content(
        [image, prompt],
        generation_config={
            "temperature": 0.7,
            "top_p": 0.9,
            "max_output_tokens": 2048
        }
    )

    return response.text

if __name__ == "__main__":
    lyrics = generate_song_from_image("sample.jpg")
    print("\n🎵 Generated Song Lyrics:\n")
    print(lyrics)
