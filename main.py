from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import logging
import re
import os

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)

# CORS middleware settings
origins = [
    "https://joe2g.github.io",  # Your deployed frontend URL
    "http://localhost:8000",    # Localhost for backend
    "http://localhost:5500",    # Localhost for frontend
    "http://127.0.0.1:8000",    # Localhost with different notation
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    type: str  # 'audio' or 'video'

def sanitize_filename(title: str) -> str:
    """Sanitize the filename to remove unwanted characters and limit length."""
    sanitized = re.sub(r'[\\/*?:"<>|]', "", title)
    return sanitized[:255]  # Limit filename length

@app.post('/download')
async def download_media(request: DownloadRequest):
    url = request.url
    download_type = request.type
    
    if download_type not in ['audio', 'video']:
        logging.error(f"Invalid type provided: {download_type}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 'type'. Use 'audio' or 'video'.")

    try:
        # Set download options
        ydl_opts = {
            'format': 'bestaudio/best' if download_type == 'audio' else 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',  # Save file as title.extension
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if download_type == 'audio' else [],
            'ffmpeg_location': r'C:\Users\DELL\Desktop\DFY\ffmpeg.exe',
            'noplaylist': True  # Download single video, not playlist
        }
        
        # Use yt-dlp to download the media from YouTube
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url.strip(), download=True)
            video_title = info_dict.get('title', None)
            if video_title is None:
                raise HTTPException(status_code=404, detail="No video found.")

            title_sanitized = sanitize_filename(video_title)
            filename = f"{title_sanitized}.mp3" if download_type == 'audio' else f"{title_sanitized}.mp4"

            # Check if the file exists and serve it
            if os.path.exists(filename):
                def iterfile():
                    with open(filename, 'rb') as file:
                        yield from file

                return StreamingResponse(iterfile(), media_type='audio/mpeg' if download_type == 'audio' else 'video/mp4', headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                })
            else:
                raise HTTPException(status_code=404, detail="Downloaded file not found.")
    
    except Exception as e:
        logging.error(f"Error occurred during download: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during the download process.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
