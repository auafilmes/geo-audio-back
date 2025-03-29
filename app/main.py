
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import shutil
import uuid
import os

app = FastAPI()

# Adicionando CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou especifique: ["https://seusite.netlify.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criar pasta static se não existir
os.makedirs("static", exist_ok=True)

# Montar pasta static para servir arquivos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Estrutura dos pontos turísticos
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

points_db: List[TourPoint] = []

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[-1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join("static", filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"url": f"/static/{filename}"}

@app.post("/points/")
async def create_point(point: TourPoint):
    point.id = uuid.uuid4().hex
    points_db.append(point)
    return point

@app.get("/points/")
async def list_points():
    return points_db


@app.delete("/points/{point_id}")
async def delete_point(point_id: str):
    global points_db
    initial_count = len(points_db)
    points_db = [p for p in points_db if p.id != point_id]
    if len(points_db) < initial_count:
        return {{ "status": "deleted", "id": point_id }}
    return JSONResponse(status_code=404, content={{ "error": "Point not found" }})
