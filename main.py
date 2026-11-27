import os, tempfile
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def delete_file(path: str):
    if os.path.exists(path): os.remove(path)

@app.get("/")
def serve_home():
    return FileResponse("index.html")

@app.get("/download")
def download_video(url: str, format_type: str = "mp4", background_tasks: BackgroundTasks = None):
    temp_dir = tempfile.mkdtemp()
    out = os.path.join(temp_dir, "%(title)s.%(ext)s")
    opts = {"outtmpl": out, "quiet": True}
    if os.path.exists("cookies.txt"): opts["cookiefile"] = "cookies.txt"
    if format_type == "mp3":
        opts.update({"format": "bestaudio/best", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]})
    else:
        opts.update({"format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "merge_output_format": "mp4"})
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fn = os.path.splitext(ydl.prepare_filename(info))[0] + (".mp3" if format_type == "mp3" else ".mp4")
        background_tasks.add_task(delete_file, fn)
        return FileResponse(path=fn, filename=os.path.basename(fn), media_type="application/octet-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
