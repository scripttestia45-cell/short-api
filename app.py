from flask import Flask, request, jsonify
import os
import uuid
import subprocess
import yt_dlp

app = Flask(__name__)
DOWNLOAD_DIR = "output"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_video(url):
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': filepath,
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return filepath

def cut_clip(input_path, start, duration, output_path):
    cmd = [
        "ffmpeg",
        "-ss", str(start),
        "-i", input_path,
        "-t", str(duration),
        "-vf", "scale=1080:1920,setsar=1",
        "-c:a", "copy",
        "-y",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

@app.route('/generate-shorts', methods=['POST'])
def generate_shorts():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "Missing url parameter"}), 400
    
    video_path = download_video(url)
    
    shorts = []
    clip_duration = 30  # secondes
    for i in range(5):
        start_time = i * 60
        output_filename = f"short_{uuid.uuid4()}.mp4"
        output_path = os.path.join(DOWNLOAD_DIR, output_filename)
        cut_clip(video_path, start_time, clip_duration, output_path)
        clip_url = f"http://localhost:5000/{DOWNLOAD_DIR}/{output_filename}"
        shorts.append(clip_url)
    
    return jsonify({"shorts": shorts})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)