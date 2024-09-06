import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import yt_dlp
from fastapi.middleware.cors import CORSMiddleware
from logging import info, error
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen import File 

# Crear la aplicación FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las solicitudes de origen
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos HTTP
    allow_headers=["*"],  # Permitir todos los encabezados
)

# Establecer la ruta de descargas dentro del proyecto
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

def print_proceso_terminado():
    print('Descarga completada')
    print('-------------------------------------------------------')

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
            print('')
            title = info_dict.get('title', None)
            artist = info_dict.get('uploader', None)
            album = info_dict.get('album', None)  # Intenta obtener el álbum si está disponible
            mp3_file = os.path.join(download_dir, f"{info_dict['title']}.mp3")
            print('mp3 file data')

            mp3_file = os.path.join(download_dir, f"{info_dict['title']}.mp3")

            return mp3_file
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error en el link: {link} - {e}')

@app.post("/download_audio/")
def download_audio(request: DownloadRequest):
    mp3_file = start_download(request.url)
    # if not os.path.exists(mp3_file):
    #     raise HTTPException(status_code=404, detail="File not found")

    def iterfile():
        with open(mp3_file, mode="rb") as file_like:
            yield from file_like

    response = StreamingResponse(iterfile(), media_type="audio/mpeg", headers={"Content-Disposition": f"attachment; filename={os.path.basename(mp3_file)}"})

    return response

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

# Ejemplo de uso
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)