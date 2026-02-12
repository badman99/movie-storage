import os
import sys
import json
import subprocess

def run_command(command):
    print(f"Executing: {command}")
    subprocess.run(command, shell=True, check=True)

def get_best_audio_track(input_file):
    print("🕵️‍♂️ Finding Best Audio Track...")
    cmd = f"ffprobe -v quiet -print_format json -show_streams '{input_file}'"
    result = subprocess.check_output(cmd, shell=True)
    data = json.loads(result)
    
    first_audio_index = None
    
    # सारे स्ट्रीम्स को स्कैन करो
    for stream in data['streams']:
        if stream['codec_type'] == 'audio':
            index = stream['index']
            
            # सबसे पहले मिलने वाले ऑडियो ट्रैक को 'Fallback' के लिए सेव कर लो
            if first_audio_index is None:
                first_audio_index = index
            
            # अब चेक करो क्या ये हिंदी है?
            tags = stream.get('tags', {})
            lang = tags.get('language', '').lower()
            title = tags.get('title', '').lower()
            
            if 'hin' in lang or 'hindi' in title:
                print(f"✅ Found Official Hindi Track at index: {index}")
                return index
    
    # अगर लूप खत्म हो गया और हिंदी नहीं मिला, तो पहला ऑडियो ट्रैक यूज़ करो
    if first_audio_index is not None:
        print(f"⚠️ Hindi nahi mila, using first available audio track (Index: {first_audio_index})")
        return first_audio_index
    else:
        # अगर कोई भी ऑडियो ट्रैक नहीं मिला (बहुत ही रेयर)
        print("❌ No audio track found at all!")
        return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 engine.py <url> <name>")
        return

    movie_url = sys.argv[1]
    raw_name = "raw_movie_file" # एक्सटेंशन हटा दिया ताकि MP4/MKV दोनों चले
    final_name = sys.argv[2]
    if not final_name.endswith('.webm'):
        final_name += ".webm"

    # 1. Download
    print(f"📥 Downloading Movie from: {movie_url}")
    run_command(f"curl -L '{movie_url}' -o '{raw_name}'")

    # 2. Find Best Audio Track
    audio_index = get_best_audio_track(raw_name)

    # 3. Transcode to VP9 (Data Saver Mode)
    print(f"🎬 Compressing to VP9 + Opus (WebM)...")
    
    # अगर ऑडियो मिला है तो उसे मैप करो, वरना सिर्फ वीडियो (मूक फिल्म 😂)
    audio_map = f"-map 0:{audio_index}" if audio_index is not None else ""
    
    ffmpeg_cmd = (
        f"ffmpeg -i '{raw_name}' -map 0:v:0 {audio_map} "
        f"-c:v libvpx-vp9 -crf 30 -b:v 0 -cpu-used 4 "
        f"-c:a libopus -b:a 128k "
        f"'{final_name}'"
    )
    run_command(ffmpeg_cmd)

    # 4. Upload to GitHub Release
    print(f"📤 Uploading to Release...")
    tag = f"v{os.getpid()}"
    run_command(f"gh release create {tag} --title 'Movie: {final_name}' --notes 'Badal Pro Engine Success' '{final_name}'")

    print(f"🚀 Mission Accomplished, Badal Bhai! Raula Jam Gaya! 😎👊")

if __name__ == "__main__":
    main()
