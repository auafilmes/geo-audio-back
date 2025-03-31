
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import shutil
import uuid
import os
from supabase import create_client

# Configurar Supabase
SUPABASE_URL = "https://kwrrtjtvslhpchxeseuw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3cnJ0anR2c2xocGNoeGVzZXV3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMzODU0MzUsImV4cCI6MjA1ODk2MTQzNX0._4x2DQeTQvBSDW5zOJzd_I9YqYFrGDywFabLYwYKFi8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pasta para arquivos estáticos
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Modelo Pydantic
class TourPoint(BaseModel):
    id: str = None
    name: str
    latitude: float
    longitude: float
    radius: float
    media_type: str
    media_url: str
    description: str
    language: str

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[-1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join("static", filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"url": f"/static/{filename}"}

@app.get("/static/{file_path:path}")
async def serve_media(file_path: str):
    full_path = os.path.join("static", file_path)
    return FileResponse(full_path)

@app.post("/points/")
async def create_point(point: TourPoint):
    point.id = uuid.uuid4().hex
    data = supabase.table("points").insert(point.dict()).execute()
    if data.data:
        return data.data[0]
    raise HTTPException(status_code=400, detail="Failed to insert point")

@app.get("/points/", response_model=List[TourPoint])
async def list_points():
    data = supabase.table("points").select("*").execute()
    return data.data

@app.delete("/points/{point_id}")
async def delete_point(point_id: str):
    data = supabase.table("points").delete().eq("id", point_id).execute()
    if data.data:
        return {"status": "deleted", "id": point_id}
    raise HTTPException(status_code=404, detail="Point not found")
