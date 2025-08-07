from flask import Flask, request, jsonify
from moviepy import VideoFileClip
import os
import uuid
import subprocess
import yt_dlp
import pysrt


app = Flask(__name__)
VIDEO_DIR = "videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

SHORTS_DIR = "shorts"
os.makedirs(SHORTS_DIR, exist_ok=True)






@app.route('/generate-texte', methods=['POST'])
def generate_texte():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL manquante'}), 400

    # Créer un dossier temporaire pour cette vidéo
    folder_id = str(uuid.uuid4())
    temp_folder = os.path.join("temp", folder_id)
    os.makedirs(temp_folder, exist_ok=True)

    # Télécharger les sous-titres
    output_path = os.path.join(temp_folder, "%(title)s.%(ext)s")
    try:
        subprocess.run([
            "yt-dlp",
            "--write-auto-sub",
            "--sub-lang", "fr",
            "--skip-download",
            "-o", output_path,
            url
        ], check=True)

    except subprocess.CalledProcessError:
        return jsonify({'error': 'Erreur lors du téléchargement des sous-titres'}), 500

    # Rechercher un fichier .vtt ou .srt
    subtitle_file = None
    for file in os.listdir(temp_folder):
        if file.endswith(".vtt") or file.endswith(".srt"):
            subtitle_file = os.path.join(temp_folder, file)
            break

    if not subtitle_file:
        return jsonify({'error': 'Aucun sous-titre trouvé'}), 404

    # Si VTT, convertir en SRT pour parsing facile
    if subtitle_file.endswith(".vtt"):
        srt_file = subtitle_file.replace(".vtt", ".srt")
        subprocess.run([
            "ffmpeg",
            "-i", subtitle_file,
            srt_file
        ])
        subtitle_file = srt_file

    # Lire et convertir en texte brut
    subs = pysrt.open(subtitle_file)
    full_text = "\n".join([sub.text for sub in subs])

    # Nettoyer
    return jsonify({"transcription": full_text})




@app.route('/telecharger-video', methods=['POST'])
def telecharger_video():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL manquante"}), 400

    try:
        video_id = str(uuid.uuid4())
        output_path = os.path.join(VIDEO_DIR, f"{video_id}.mp4")

        ydl_opts = {
            'outtmpl': output_path,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
            'merge_output_format': 'mp4'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return jsonify({"video_path": output_path, "video_id": video_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500





@app.route('/generate-short', methods=['POST'])
def generate_short():
    data = request.get_json()
    video_path = data.get("video_path")
    timestamps = data.get("timestamps")  # format : [{"start": "00:05:47", "end": "00:06:18"}, ...]

    if not video_path or not timestamps:
        return jsonify({"error": "Données manquantes"}), 400

    shorts_generated = []

    try:
        for idx, ts in enumerate(timestamps):
            clip = VideoFileClip(video_path).subclipped(ts["start"], ts["end"])
            short_path = os.path.join(SHORTS_DIR, f"short_{idx + 1}.mp4")
            clip.write_videofile(short_path, codec="libx264", audio_codec="aac")
            shorts_generated.append(short_path)

        return jsonify({"shorts": shorts_generated})

    except Exception as e:
        return jsonify({"error": str(e)}), 500






if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)