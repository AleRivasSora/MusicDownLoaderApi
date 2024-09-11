import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import yt_dlp
from fastapi.middleware.cors import CORSMiddleware
from logging import info, error
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen import File 


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

port = int(os.environ.get("PORT", 8000))
download_dir = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(download_dir, exist_ok=True)

class DownloadRequest(BaseModel):
    url: str

class DownloadResponse(BaseModel):
    message: str
    title: str

def clear():
    if os.name == 'nt':  # 'nt' indica Windows
        os.system('cls')
    else:
        os.system('clear')

def start_download(link):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
        'noplaylist': True,  
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            title = info_dict.get('title', None)
            author = info_dict.get('uploader', None)
            album = info_dict.get('album', None)
            genre = info_dict.get('genre', None)
            print('-------------------------------------------------------')
            print(f'Título: {title}')
            print(f'Autor: {author}')
            print(f'Álbum: {album}')
            print('')
            mp3_file = os.path.join(download_dir, f"{info_dict['title']}.mp3")
            print('mp3 file data')



            return {
                "mp3_file": mp3_file,
                "metadata": {
                    "title": title,
                    "author": author,
                    "album": album
                }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error en el link: {link} - {e}')
    

@app.post("/download_audio/")
def download_audio(request: DownloadRequest):
    result = start_download(request.url)
    mp3_file = result["mp3_file"]
    metadata = result["metadata"]

    return JSONResponse(content={
        "message": "Descarga completada",
        "title": metadata["title"],
        "author": metadata["author"],
        "album": metadata["album"],
        "file_url": f"/download_file/{os.path.basename(mp3_file)}"
    })


@app.get("/download_file/{filename}")
def download_file(filename: str):
    file_path = os.path.join(download_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    def iterfile():
        with open(file_path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(iterfile(), media_type="audio/mpeg", headers={"Content-Disposition": f"attachment; filename={filename}"})


@app.get("/donwload_ok/")
def succes_downdloaded(title: str):
 

    mp3_file = os.path.join(download_dir, f"{title}.mp3")

    if not os.path.exists(mp3_file):
        return HTTPException(status_code=404, detail="File not found")

    try:
        os.remove(mp3_file)
        info(f"Deleted downloaded file: {mp3_file}")
        return {"message": "Descarga completada y archivo eliminado"}
    except OSError as e:
        error(f"Error deleting file: {mp3_file} - {e}")
        return HTTPException(status_code=500, detail="Error al eliminar el archivo")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
