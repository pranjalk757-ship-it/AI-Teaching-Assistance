from youtube_transcript_api import YouTubeTranscriptApi
import subprocess
from faster_whisper import WhisperModel

import json
import os


os.makedirs("audios",exist_ok=True)
os.makedirs("transcripts",exist_ok=True)

api = YouTubeTranscriptApi()
model = WhisperModel(
    "large-v2",
    device="cpu",
    compute_type="int8"
)

video_urls = []

with open("video_urls.txt",'r') as file:
    for line in file:
        video_url = line.strip()
        if(video_url):
            video_urls.append(video_url)

# print("video urls ",video_urls)

for video_url in video_urls:
    #  finding Title of Video
    result = subprocess.run(["yt-dlp","--get-title",video_url],capture_output=True,text=True)
    title = result.stdout.strip()
    chunk = []
    full_text = ""
    if "youtu.be" in video_url:
        video_id = video_url.split('/')[-1].split("?")[0]
    else:
        video_id = video_url.split('v=')[1].split("&")[0]
    try:
        # video_id = "VwN91x5i25g"
        transcript = api.fetch(video_id,languages=["en", "en-US", "en-GB"])
        for snippet in transcript:
            try:
                chunk.append({"start":snippet.start,"end":snippet.start + snippet.duration,"text":snippet.text})
                full_text += snippet.text + " "
            except Exception as e:
                print("Transcript Error",e)
        print("Done Transcript")
    except Exception as e:
        print("Downloading audio")
        # defining file name
        audio_file = f"{title}.mp3"
        # downloading audio from youtube
        subprocess.run(["yt-dlp","-x","--audio-format","mp3","-o",f"audios/{video_id}",video_url])
        # Transcribing audio
        segments,info = model.transcribe(f"audios/{video_id}.mp3",language="en")
        for segment in segments:
            chunk.append({"start":segment.start,"end":segment.end,"text":segment.text})
            full_text += segment.text + " "
        print("Done audio transcribe")
        
    chunk_meta_data = {"video_id":video_id,"video_name":title,"chunk":chunk,"text":full_text}
    with open(f"transcripts/{video_id}.json",'w') as f:
        json.dump(chunk_meta_data,f,indent=4)
