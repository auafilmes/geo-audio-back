
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import shutil
import uuid
import os
import sqlite3

app = FastAPI()

# CORS habilitado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criar pasta static
os.makedirs("static", exist_ok=True)

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Conectar SQLite
conn = sqlite3.connect('points.db', check_same_thread=False)
cursor = conn.cursor()

# Criar tabela
cursor.execute('''
CREATE TABLE IF NOT EXISTS points (
    id TEXT PRIMARY KEY,
    name TEXT,
    latitude REAL,
    longitude REAL,
    radius REAL,
    media_type TEXT,
    media_url TEXT,
    description TEXT,
    language TEXT
)
''')
conn.commit()

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

@app.post("/points/")
async def create_point(point: TourPoint):
    point.id = uuid.uuid4().hex
    cursor.execute('''
        INSERT INTO points (id, name, latitude, longitude, radius, media_type, media_url, description, language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (point.id, point.name, point.latitude, point.longitude, point.radius, point.media_type, point.media_url, point.description, point.language))
    conn.commit()
    return point

@app.get("/points/", response_model=List[TourPoint])
async def list_points():
    cursor.execute('SELECT * FROM points')
    points = cursor.fetchall()
    return [TourPoint(id=row[0], name=row[1], latitude=row[2], longitude=row[3],
                      radius=row[4], media_type=row[5], media_url=row[6],
                      description=row[7], language=row[8]) for row in points]

@app.delete("/points/{point_id}")
async def delete_point(point_id: str):
    cursor.execute('DELETE FROM points WHERE id = ?', (point_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Point not found")
    conn.commit()
    return {"status": "deleted", "id": point_id}
