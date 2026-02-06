import os
from PIL import Image
import torch # AI processing mate
from transformers import BlipProcessor, BlipForConditionalGeneration
from yt_dlp import YoutubeDL
try:
    from moviepy.editor import ImageClip, AudioFileClip
except ImportError:
    from moviepy import ImageClip, AudioFileClip

# --- SETTINGS ---
PHOTO_FOLDER = 'photos'
OUTPUT_FOLDER = 'output'
if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)

print("🚀 AI Models Load thai rahya che... (Best Quality Filtering Active)")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def get_image_score(image_path):
    """AI logic photo ni quality ane content check karva mate"""
    try:
        raw_image = Image.open(image_path).convert('RGB')
        
        # Check image size (Quality check)
        width, height = raw_image.size
        resolution_score = (width * height) / 1000000  # Resolution na adhare score
        
        # AI Description generator
        inputs = processor(raw_image, return_tensors="pt")
        out = model.generate(**inputs)
        desc = processor.decode(out[0], skip_special_tokens=True).lower()
        
        # 'Aesthetic' keywords check
        quality_keywords = ['nature', 'beautiful', 'portrait', 'landscape', 'scenery', 'bright', 'colorful', 'ocean', 'mountain']
        keyword_score = sum(2 for word in quality_keywords if word in desc)
        
        total_score = resolution_score + keyword_score
        return total_score, desc
    except:
        return 0, ""

def main():
    # 1. Badha photos ni list lo
    all_files = [f for f in os.listdir(PHOTO_FOLDER) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    
    if not all_files:
        print("❌ Error: 'photos' folder ma photos muko!")
        return

    print(f"🔍 Total {len(all_files)} photos malya. Best photos shodhvu chu...")
    
    # 2. Filtering Logic: Badha photo scan kari ne top 10 select karo
    scored_photos = []
    for f in all_files:
        path = os.path.join(PHOTO_FOLDER, f)
        score, desc = get_image_score(path)
        scored_photos.append({'name': f, 'score': score, 'desc': desc})
    
    # Score na adhare Sort karo (High to Low)
    best_photos = sorted(scored_photos, key=lambda x: x['score'], reverse=True)[:10]

    print(f"✨ Top {len(best_photos)} Best Quality photos select thai gaya che!")

    # 3. Final Video Creation Loop
    for i, photo_data in enumerate(best_photos):
        try:
            photo_name = photo_data['name']
            photo_desc = photo_data['desc']
            photo_path = os.path.join(PHOTO_FOLDER, photo_name)
            
            print(f"\n🎬 Creating Best Reel {i+1}: {photo_name} (Score: {photo_data['score']:.2f})")
            print(f"📸 Mood: {photo_desc}")
            
            # Step 2: YouTube Audio
            search_query = f"ytsearch1:{photo_desc} superhit old hindi bollywood song"
            audio_file = f"temp_audio_{i}.mp3"
            
            ydl_opts = {
                'format': 'ba/b',
                'outtmpl': f'temp_audio_{i}',
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '64'}],
                'quiet': True,
                'download_sections': [{'end_time': 20, 'start_time': 0}],
                'force_keyframes_at_cuts': True,
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([search_query])
            
            # Step 3: Video Merge
            video_path = os.path.join(OUTPUT_FOLDER, f"best_reel_{i+1}.mp4")
            clip = ImageClip(photo_path).set_duration(15).resize(height=1080)
            audio = AudioFileClip(audio_file).set_duration(15)
            
            video = clip.set_audio(audio)
            video.write_videofile(video_path, fps=24, codec="libx264", audio_codec="libmp3lame")
            
            audio.close()
            clip.close()
            if os.path.exists(audio_file): os.remove(audio_file)
            
            print(f"✅ Reel Saved: {video_path}")
            
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()