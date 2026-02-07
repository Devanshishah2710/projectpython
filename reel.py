
import os
import json
from PIL import Image
import torch
import time
from transformers import BlipProcessor, BlipForConditionalGeneration
from yt_dlp import YoutubeDL
from moviepy.editor import ImageClip, AudioFileClip
import google.generativeai as genai

# ---------------- CONFIG ----------------
# ⚠️ SECURITY WARNING: Never share this file with the key below inside it.
# Ideally, set this as an environment variable: os.environ["GOOGLE_API_KEY"]
genai.configure(api_key="AIzaSyC8ALOy7YcmLcFD6TGCQfegSNvrwq0j-jk")

PHOTO_FOLDER = "photos"
OUTPUT_FOLDER = "output"
CACHE_FOLDER = "cache"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)

# Use the model confirmed to exist in your list
gemini = genai.GenerativeModel("gemini-2.0-flash-lite-001")# ---------------- LOAD AI (LOCAL) ----------------
print("🚀 Loading BLIP model...")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# ---------------- HELPERS ----------------
def get_caption(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        inputs = processor(img, return_tensors="pt")
        output = model.generate(**inputs)
        return processor.decode(output[0], skip_special_tokens=True)
    except Exception as e:
        print(f"⚠️ Error captioning {image_path}: {e}")
        return "A generic image"

# ---------------- GEMINI: IMAGE SCORING (BATCH) ----------------
import time # Make sure this is imported at the top of your file

# ---------------- GEMINI: IMAGE SCORING (BATCH) ----------------
def score_images_with_gemini(image_data):
    cache_file = f"{CACHE_FOLDER}/image_scores.json"
    
    # Check cache first
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass

    prompt = f"""
    You are an expert Instagram Reels content curator.
    Analyze the following images based on their captions. 
    For each image, provide a JSON object with:
    - "name": (The exact filename provided)
    - "score": (Integer 1-10 based on viral potential)
    - "emotion": (A single adjective describing the mood)
    - "scene_type": (The setting)

    Return ONLY a valid JSON array.

    Input Data:
    {json.dumps(image_data, indent=2)}
    """

    print("   -> Sending request to Gemini...")
    
    # --- NEW RETRY LOGIC ---
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = gemini.generate_content(prompt)
            
            # If successful, parse and save
            cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned_text)
            
            # Safety Merge
            final_data = []
            for img in image_data:
                match = next((item for item in result if item.get("name") == img["name"]), None)
                if match:
                    img.update(match)
                    final_data.append(img)
                else:
                    img.update({"score": 5, "emotion": "Neutral", "scene_type": "General"})
                    final_data.append(img)

            with open(cache_file, "w") as f:
                json.dump(final_data, f, indent=2)
                
            return final_data

        except Exception as e:
            # Check if it's a rate limit error (429)
            if "429" in str(e):
                wait_time = 40 * (attempt + 1) # Wait 40s, then 80s, etc.
                print(f"   ⚠️ Quota exceeded. Waiting {wait_time} seconds before retry {attempt+1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                print(f"❌ Error during Gemini scoring: {e}")
                return []
    
    print("❌ Failed after max retries.")
    return []
# ---------------- GEMINI: MUSIC INTENT ----------------
def get_music_intent(emotion, scene):
    # Sanitize filename to prevent invalid characters
    safe_key = f"{emotion}_{scene}".replace(" ", "_").replace("/", "")
    key = f"{safe_key}.json"
    path = f"{CACHE_FOLDER}/{key}"

    if os.path.exists(path):
        try:
            return json.load(open(path))
        except:
            pass

    prompt = f"""
    Suggest Instagram Reel music attributes.
    
    Emotion: {emotion}
    Scene: {scene}

    Return JSON only:
    {{
      "search_query": "copyright free {emotion} {scene} music",
      "tempo": "medium",
      "genre": "pop"
    }}
    """
    try:
        response = gemini.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        json.dump(data, open(path, "w"), indent=2)
        return data
    except:
        # Fallback if music AI fails
        return {"search_query": "lofi hip hop copyright free", "tempo": "medium", "genre": "lofi"}

# ---------------- MAIN ----------------
def main():
    images = [f for f in os.listdir(PHOTO_FOLDER) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
    if not images:
        print(f"❌ No images found in '{PHOTO_FOLDER}'. Please add some photos.")
        return

    print("🔍 Captioning images (local AI)...")
    image_data = []
    for img in images:
        caption = get_caption(os.path.join(PHOTO_FOLDER, img))
        image_data.append({"name": img, "caption": caption})

    print("🧠 Scoring images with Gemini (batch)...")
    scores = score_images_with_gemini(image_data)
    
    if not scores:
        print("❌ Failed to get scores. Exiting.")
        return

    # Sort by score and take top 10
    top_images = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)[:10]

    for i, img in enumerate(top_images):
        print(f"\n🎬 Creating Reel {i+1}: {img['name']} (Score: {img.get('score')})")
        
        # Safe access to keys using .get() to prevent crashes
        emotion = img.get("emotion", "Happy")
        scene = img.get("scene_type", "General")
        
        music = get_music_intent(emotion, scene)

        audio_file = f"temp_audio_{i}.mp3"
        
        # Prepare YoutubeDL
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": audio_file.replace(".mp3", ""), # yt-dlp adds extension automatically often
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
            # Download first 30s to ensure we have enough for 15s clip
            "download_sections": [{"start_time": 0, "end_time": 30}], 
        }

        # Download Music
        try:
            if os.path.exists(audio_file):
                os.remove(audio_file)
                
            print(f"   🎵 Downloading music: {music['search_query']}...")
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"ytsearch1:{music['search_query']}"])
            
            # YoutubeDL might name it slightly differently, find the file
            final_audio_path = audio_file
            if not os.path.exists(final_audio_path):
                # check for temp_audio_0.mp3 if outtmpl was without extension
                if os.path.exists(audio_file + ".mp3"):
                    final_audio_path = audio_file + ".mp3"
            
            if not os.path.exists(final_audio_path):
                 print("   ⚠️ Audio download failed, skipping this reel.")
                 continue

            # Create Video
            photo_path = os.path.join(PHOTO_FOLDER, img["name"])
            video_path = os.path.join(OUTPUT_FOLDER, f"reel_{i+1}_{img['name']}.mp4")

            # Load and Resize Image (Vertical 9:16)
            clip = ImageClip(photo_path)
            
            # Resize logic to fill 1080x1920 roughly
            # (Simple resize to height 1920, usually safe for vertical reels)
            clip = clip.resize(height=1920) 
            clip = clip.set_duration(15) 
            
            # Center crop if needed (optional, keeping it simple for now)
            # clip = clip.crop(x1=..., y1=...) 

            # Load Audio
            audio = AudioFileClip(final_audio_path).subclip(0, 15)
            
            # Combine
            final_clip = clip.set_audio(audio)
            final_clip.write_videofile(video_path, fps=24, codec="libx264", audio_codec="aac")

            # Cleanup
            final_clip.close()
            audio.close()
            clip.close()
            if os.path.exists(final_audio_path):
                os.remove(final_audio_path)

            print(f"✅ Saved: {video_path}")

        except Exception as e:
            print(f"❌ Error processing {img['name']}: {e}")

if __name__ == "__main__":
    main()