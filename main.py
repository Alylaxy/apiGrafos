from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from uuid import UUID
import uuid
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, UUID as SQLUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import UniqueConstraint

Base = declarative_base()

# SQLAlchemy models
class Vertice(Base):
    __tablename__ = 'vertices'
    
    id = Column(Integer, primary_key=True)
    labirinto_id = Column(Integer, ForeignKey('labirintos.id'))
    adjacentes = Column(String)  # Assuming adjacentes is stored as a comma-separated string
    tipo = Column(Integer)
    labirinto = relationship("Labirinto", back_populates="vertices")

class Labirinto(Base):
    __tablename__ = 'labirintos'
    
    id = Column(Integer, primary_key=True)
    vertices = relationship("Vertice", back_populates="labirinto")
    entrada = Column(Integer)
    dificuldade = Column(String)

class Grupo(Base):
    __tablename__ = 'grupos'
    
    id = Column(SQLUUID(as_uuid=True), primary_key=True)
    nome = Column(String)
    labirintos_concluidos = Column(String)  # Assuming labirintos_concluidos is stored as a comma-separated string

class SessaoWebSocket(Base):
    __tablename__ = 'sessoes_websocket'
    
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    grupo_id = Column(String, ForeignKey('grupos.id'))  # Use String type for UUID
    conexao = Column(String)

# Pydantic models
class VerticeModel(BaseModel):
    id: int
    labirintoId: int
    adjacentes: List[int]
    tipo: int

class LabirintoModel(BaseModel):
    id: int
    vertices: List[VerticeModel]
    entrada: int
    dificuldade: str  

class GrupoModel(BaseModel):
    nome: str
    labirintos_concluidos : Optional[List[int]] = None

# DTOs
class VerticeDto(BaseModel):
    id: int
    adjacentes: List[int]
    tipo: int

class LabirintoDto(BaseModel):
    LabirintoId: int
    Dificuldade: str
    Completo: bool
    Passos: int
    Exploracao: float

class GrupoDto(BaseModel):
    id: UUID
    nome: str
    labirintos_concluidos: Optional[List[int]]

# Create the database and tables
engine = create_engine('sqlite:///./db.sqlite3', echo=True)
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

@app.post("/grupo")
async def registrar_grupo(grupo: GrupoModel):
    db = next(get_db())
    grupo_db = Grupo(id=uuid.uuid4(), nome=grupo.nome)
    db.add(grupo_db)
    db.commit()
    grupo_dto = GrupoDto(id=grupo_db.id, nome=grupo_db.nome, labirintos_concluidos=[])
    return {"GrupoId": grupo_dto.id}


@app.get("/grupos")
async def retorna_grupos():
    db = next(get_db())
    grupos = db.query(Grupo).all()
    grupos_dto = [GrupoDto(id=grupo.id, nome=grupo.nome, labirintos_concluidos=[]) for grupo in grupos]
    return {"Grupos": grupos_dto}

@app.get("/iniciar/{grupo_id}")
async def iniciar_desafio(grupo_id: UUID):
    db = next(get_db())
    grupo_db = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not grupo_db:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    
    pass

@app.get("/labirintos/{grupo_id}")
async def get_labirintos(grupo_id: UUID):
    db = next(get_db())
    grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    labirintos = db.query(Labirinto).all()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    
    labirintos_dto = [LabirintoDto(LabirintoId = labirinto.id, Dificuldade = labirinto.dificuldade, Completo = labirinto.id in grupo.labirintos_concluidos) for labirinto in labirintos]
    
    return {"Labirintos": labirintos_dto}

@app.get("/sessoes")
async def get_websocket_sessions():
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
