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
    Analyze this image in detail.
    Include:
    - Mood and emotions
    - Visual elements and atmosphere
    - Possible story or theme

    Based on this analysis, write original song lyrics
    that emotionally match the image.
    Avoid referencing the image directly.
    """

    response = model.generate_content(
        [image, prompt],
        generation_config={
            "temperature": 0.8,
            "top_p": 0.9,
            "max_output_tokens": 400
        }
    )

    return response.text

if __name__ == "__main__":
    lyrics = generate_song_from_image("sample.jpg")
    print("\n🎵 Generated Song Lyrics:\n")
    print(lyrics)