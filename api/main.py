from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
import uuid
import asyncio
import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, UUID as SQLUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.schema import PrimaryKeyConstraint
from fastapi.middleware.cors import CORSMiddleware

Base = declarative_base()

# SQLAlchemy models
class MovementHistory(Base):
    __tablename__ = 'movement_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessoes_websocket.id'))
    labirinto_id = Column(Integer, ForeignKey('labirintos.id'))
    grupo_id = Column(SQLUUID(as_uuid=True), ForeignKey('grupos.id'))
    vertex_sequence = Column(String)  # Store as comma-separated string
    timestamp = Column(String)

    session = relationship("SessaoWebSocket", backref="movement_history")

class Aresta(Base):
    __tablename__ = 'arestas'

    vertice_origem_id = Column(Integer, ForeignKey('vertices.id'), nullable=False)
    vertice_destino_id = Column(Integer, ForeignKey('vertices.id'), nullable=False)
    peso = Column(Integer, nullable=False)
    labirinto_id = Column(Integer, ForeignKey('labirintos.id'), nullable=False)

    __table_args__ = (PrimaryKeyConstraint('vertice_origem_id', 'vertice_destino_id', 'labirinto_id', name='pk_aresta'),)

    vertice_origem = relationship("Vertice", foreign_keys=[vertice_origem_id])
    vertice_destino = relationship("Vertice", foreign_keys=[vertice_destino_id])

class Vertice(Base):
    __tablename__ = 'vertices'

    id = Column(Integer, nullable=False)
    labirinto_id = Column(Integer, ForeignKey('labirintos.id'), nullable=False)
    tipo = Column(Integer)

    labirinto = relationship("Labirinto", back_populates="vertices")
    arestas_origem = relationship("Aresta", foreign_keys=[Aresta.vertice_origem_id])
    arestas_destino = relationship("Aresta", foreign_keys=[Aresta.vertice_destino_id])

    __table_args__ = (PrimaryKeyConstraint('id', 'labirinto_id', name='pk_vertice'),)

class Labirinto(Base):
    __tablename__ = 'labirintos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    vertices = relationship("Vertice", back_populates="labirinto")
    entrada = Column(Integer)
    saida = Column(String)
    dificuldade = Column(String)

    info_grupos = relationship("InfoGrupo", back_populates="labirinto")

class Grupo(Base):
    __tablename__ = 'grupos'

    id = Column(SQLUUID(as_uuid=True), primary_key=True)
    nome = Column(String)
    labirintos_concluidos = Column(String)
    info_grupos = relationship("InfoGrupo", back_populates="grupo")
    sessoes_websocket = relationship("SessaoWebSocket", back_populates="grupo")

class InfoGrupo(Base):
    __tablename__ = 'info_grupos'

    grupo_id = Column(SQLUUID(as_uuid=True), ForeignKey('grupos.id'), nullable=False)
    labirinto_id = Column(Integer, ForeignKey('labirintos.id'), nullable=False)
    passos = Column(Integer)
    exploracao = Column(Float)

    __table_args__ = (PrimaryKeyConstraint('grupo_id', 'labirinto_id', name='pk_info'),)

    grupo = relationship("Grupo", foreign_keys=[grupo_id], back_populates="info_grupos")
    labirinto = relationship("Labirinto", foreign_keys=[labirinto_id], back_populates="info_grupos")

class SessaoWebSocket(Base):
    __tablename__ = 'sessoes_websocket'

    id = Column(Integer, primary_key=True, autoincrement=True)
    grupo_id = Column(SQLUUID, ForeignKey('grupos.id'))
    conexao = Column(String)

    grupo = relationship("Grupo", back_populates="sessoes_websocket")

# Pydantic models
class VerticeModel(BaseModel):
    id: int
    tipo: int

class ArestaModel(BaseModel):
    origemId: int
    destinoId: int
    peso: int

class LabirintoModel(BaseModel):
    vertices: List[VerticeModel]
    arestas: List[ArestaModel]
    dificuldade: str

class GrupoModel(BaseModel):
    nome: str
    labirintos_concluidos: Optional[List[int]] = None

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

    class Config:
        orm_mode = True

class CriarGrupoDto(BaseModel):
    nome: str

class WebsocketRequestDto(BaseModel):
    grupo_id: UUID
    labirinto_id: int

class RespostaDto(BaseModel):
    labirinto: int
    grupo: UUID
    vertices: List[int]

class RetornaLabirintosDto(BaseModel):
    labirinto: int
    dificuldade: str

# Websocket manager
class ConnectionManager:
    def __init__(self):
        # Dictionary to store session connections
        # Format: {session_id: [list of WebSocket connections]}
        self.session_connections = {}

    async def connect(self, websocket: WebSocket, session_id: int):
        await websocket.accept()
        if session_id not in self.session_connections:
            self.session_connections[session_id] = []
        self.session_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: int):
        if session_id in self.session_connections:
            if websocket in self.session_connections[session_id]:
                self.session_connections[session_id].remove(websocket)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]

    async def broadcast_to_session(self, message: str, session_id: int):
        if session_id in self.session_connections:
            for connection in self.session_connections[session_id]:
                try:
                    await connection.send_text(message)
                except:
                    continue

# Database setup
engine = create_engine(
    'sqlite:///./db.sqlite3',
    pool_size=200,  # Increase pool size
    max_overflow=200,  # Increase max overflow
    pool_timeout=60,  # Increase timeout
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=True
)
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()

@app.post("/grupo")
async def registrar_grupo(grupo: CriarGrupoDto):
    db = next(get_db())
    grupo_id = uuid.uuid4()
    grupo_db = Grupo(id=grupo_id, nome=grupo.nome)
    db.add(grupo_db)
    for labirinto in db.query(Labirinto).all():
        info_grupo = InfoGrupo(grupo_id=grupo_id, labirinto_id=labirinto.id, passos=0, exploracao=0)
        db.add(info_grupo)
    db.commit()
    grupo_dto = GrupoDto(id=grupo_db.id, nome=grupo_db.nome, labirintos_concluidos=[])
    return {"GrupoId": grupo_dto.id}

@app.post("/labirinto")
async def criar_labirinto(labirinto: LabirintoModel):
    db = next(get_db())
    labirinto_db = Labirinto(entrada=0, dificuldade=labirinto.dificuldade)
    db.add(labirinto_db)
    db.commit()
    db.refresh(labirinto_db)

    for vertice in labirinto.vertices:
        vertice_db = Vertice(
            id=vertice.id,
            labirinto_id=labirinto_db.id,
            tipo=vertice.tipo
        )
        if vertice.tipo == 2:
            labirinto_db.saida = (labirinto_db.saida or "") + f"{vertice.id}, "
        db.add(vertice_db)

    for aresta in labirinto.arestas:
        aresta_db = Aresta(
            vertice_origem_id=aresta.origemId,
            labirinto_id=labirinto_db.id,
            vertice_destino_id=aresta.destinoId,
            peso=aresta.peso
        )
        db.add(aresta_db)

    db.commit()
    return {"LabirintoId": labirinto_db.id}

@app.get("/grupos")
async def retorna_grupos():
    db = next(get_db())
    grupos = db.query(Grupo).all()
    grupos_dto = [GrupoDto(
        id=grupo.id,
        nome=grupo.nome,
        labirintos_concluidos=grupo.labirintos_concluidos.split(",") if grupo.labirintos_concluidos else []
    ) for grupo in grupos]
    return {"Grupos": grupos_dto}

@app.get("/labirintos")
async def get_labirintos():
    db = next(get_db())
    labirintos = db.query(Labirinto).all()
    lista_labirintos = [
        RetornaLabirintosDto(labirinto=lab.id, dificuldade=lab.dificuldade)
        for lab in labirintos
    ]
    return {"labirintos": lista_labirintos}


@app.get("/sessoes")
async def get_websocket_sessions(nome_grupo: Optional[str] = None):
    db = next(get_db())
    try:
        # Basic query for sessions
        query = db.query(SessaoWebSocket)

        # Join with Grupo if we need to filter by name
        if nome_grupo:
            query = query.join(Grupo).filter(Grupo.nome.ilike(f"%{nome_grupo}%"))

        sessoes = query.all()

        result = []
        for sessao in sessoes:
            # Get grupo info
            grupo = db.query(Grupo).filter(Grupo.id == sessao.grupo_id).first()

            # Get latest history for this session
            history = db.query(MovementHistory)\
                .filter(MovementHistory.session_id == sessao.id)\
                .order_by(MovementHistory.timestamp.desc())\
                .first()

            session_data = {
                "id": sessao.id,
                "grupo_id": str(sessao.grupo_id),
                "conexao": sessao.conexao,
                "grupo_nome": grupo.nome if grupo else None,
                "ultima_atividade": history.timestamp if history else None,
                "moves_count": len(history.vertex_sequence.split(',')) if history and history.vertex_sequence else 0,
                "labirinto_id": history.labirinto_id if history else None
            }
            result.append(session_data)

        return result
    finally:
        db.close()

@app.get("/session-histories/{labirinto_id}")
async def get_session_histories(labirinto_id: int):
    db = next(get_db())
    histories = db.query(MovementHistory).filter_by(labirinto_id=labirinto_id).all()

    return {
        "histories": [
            {
                "session_id": h.session_id,
                "grupo_id": str(h.grupo_id),
                "moves": h.vertex_sequence,
                "timestamp": h.timestamp
            }
            for h in histories
        ]
    }

@app.websocket("/ws/{grupo_id}/{labirinto_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    grupo_id: UUID,
    labirinto_id: int,
    session_id: Optional[int] = None,
    observer: bool = False
):
    db = next(get_db())

    # Create or get session
    if not session_id:
        ws_session = SessaoWebSocket(grupo_id=grupo_id, conexao=str(websocket.url))
        db.add(ws_session)
        db.commit()
        db.refresh(ws_session)
        session_id = ws_session.id
    else:
        ws_session = db.query(SessaoWebSocket).filter_by(id=session_id).first()
        if not ws_session:
            await websocket.close(code=4000, reason="Invalid session")
            return

    # Connect to session
    await manager.connect(websocket, session_id)

    # if observer:
    #     await manager.broadcast_to_session(f"New observer joined session {session_id}", session_id)
    # else:
    #     await manager.broadcast_to_session(f"Player joined session {session_id}", session_id)

    try:
        # Load maze and initial position
        labirinto = db.query(Labirinto).filter(Labirinto.id == labirinto_id).first()
        if not labirinto:
            await manager.broadcast_to_session("Labirinto não encontrado.", session_id)
            return

        vertice_atual = db.query(Vertice).filter(
            Vertice.labirinto_id == labirinto_id,
            Vertice.id == labirinto.entrada
        ).first()

        if not vertice_atual:
            await manager.broadcast_to_session("Vértice de entrada não encontrado.", session_id)
            return

        # Get movement history if exists
        history_record = db.query(MovementHistory).filter_by(session_id=session_id).first()
        historico = [0]  # Start with initial vertex
        if history_record:
            historico = [int(x) for x in history_record.vertex_sequence.split(',') if x]

        # Send initial vertex information
        arestas = db.query(Aresta).filter(Aresta.vertice_origem_id == vertice_atual.id).all()
        adjacentes = [(a.vertice_destino_id, a.peso) for a in arestas]
        await manager.broadcast_to_session(
            f"Vértice atual: {vertice_atual.id}, Tipo: {vertice_atual.tipo}, Adjacentes(Vertice, Peso): {adjacentes}",
            session_id
        )

        step_count = len(historico)

        # Main game loop
        while True:
            if observer:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                    if data == "historico":
                        await manager.broadcast_to_session(str(historico), session_id)
                    elif data == "labirinto":
                        await manager.broadcast_to_session(f"Labirinto atual: {labirinto_id}", session_id)
                except:
                    break
            else:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)

                    if data.startswith("ir:"):
                        vertice_desejado_id = int(data.split(":")[1].strip())
                        adjacentes = [a[0] for a in db.query(Aresta.vertice_destino_id)
                                    .filter(Aresta.vertice_origem_id == vertice_atual.id).all()]

                        if vertice_desejado_id not in adjacentes:
                            await manager.broadcast_to_session("Movimento inválido", session_id)
                            continue

                        vertice_atual = db.query(Vertice).filter(
                            Vertice.labirinto_id == labirinto_id,
                            Vertice.id == vertice_desejado_id
                        ).first()

                        historico.append(vertice_atual.id)
                        step_count += 1

                        # Update history in database
                        history_record = db.query(MovementHistory).filter_by(session_id=session_id).first()
                        if history_record:
                            history_record.vertex_sequence = ','.join(map(str, historico))
                        else:
                            history_record = MovementHistory(
                                session_id=session_id,
                                labirinto_id=labirinto_id,
                                grupo_id=grupo_id,
                                vertex_sequence=','.join(map(str, historico)),
                                timestamp=datetime.datetime.now().isoformat()
                            )
                            db.add(history_record)
                        db.commit()

                        # Get updated adjacent vertices
                        arestas = db.query(Aresta).filter(Aresta.vertice_origem_id == vertice_atual.id).all()
                        adjacentes = [(a.vertice_destino_id, a.peso) for a in arestas]

                        # Send updated vertex information
                        await manager.broadcast_to_session(
                            f"Vértice atual: {vertice_atual.id}, Tipo: {vertice_atual.tipo}, Adjacentes(Vertice, Peso): {adjacentes}",
                            session_id
                        )

                    elif data == "historico":
                        await manager.broadcast_to_session(str(historico), session_id)
                    elif data == "labirinto":
                        await manager.broadcast_to_session(f"Labirinto atual: {labirinto_id}", session_id)

                except asyncio.TimeoutError:
                    await manager.broadcast_to_session("Conexão encerrada por inatividade.", session_id)
                    break

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        grupo_info = db.query(InfoGrupo).filter(
            InfoGrupo.grupo_id == str(grupo_id),
            InfoGrupo.labirinto_id == labirinto_id
        ).first()

        if grupo_info:
            grupo_info.passos = step_count
            grupo_info.exploracao = step_count / len(
                db.query(Vertice).filter(Vertice.labirinto_id == labirinto_id).all()
            )
            db.add(grupo_info)
            db.commit()

        # if observer:
        #     await manager.broadcast_to_session(f"Observer left session {session_id}", session_id)
        # else:
        #     await manager.broadcast_to_session(f"Player left session {session_id}", session_id)

@app.get("/labirintos/{labirinto_id}/arestas", response_model=List[dict])
def get_arestas(labirinto_id: int):
    db = next(get_db())
    try:
        # First check if the maze exists
        labirinto = db.query(Labirinto).filter(Labirinto.id == labirinto_id).first()
        if not labirinto:
            raise HTTPException(status_code=404, detail="Labirinto não encontrado.")

        # Get all edges for this maze
        arestas = db.query(Aresta).filter(Aresta.labirinto_id == labirinto_id).all()

        if not arestas:
            raise HTTPException(status_code=404, detail="Labirinto não possui arestas.")

        return [
            {
                "origem": aresta.vertice_origem_id,
                "destino": aresta.vertice_destino_id,
                "peso": aresta.peso
            }
            for aresta in arestas
        ]
    finally:
        db.close()

@app.post("/generate-websocket/")
async def generate_websocket_link(connection: WebsocketRequestDto):
    db = next(get_db())
    grupo = db.query(Grupo).filter(Grupo.id == connection.grupo_id).first()
    labirinto = db.query(Labirinto).filter(Labirinto.id == connection.labirinto_id).first()

    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    if not labirinto:
        raise HTTPException(status_code=404, detail="Labirinto não encontrado")

    ws_url = f"ws://localhost:8000/ws/{connection.grupo_id}/{connection.labirinto_id}"

    sessao_ws = SessaoWebSocket(grupo_id=connection.grupo_id, conexao=ws_url)
    db.add(sessao_ws)
    db.commit()

    return {"websocket_url": ws_url, "session_id": sessao_ws.id}

@app.get("/placar/{grupo_id}")
async def get_placar_por_grupo(grupo_id: UUID):
    db = next(get_db())
    grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()

    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")

    dados = db.query(InfoGrupo).filter(InfoGrupo.grupo_id == grupo_id).all()

    placar = {
        "grupo": grupo.nome,
        "labirintos": [
            {
                "labirinto": dado.labirinto_id,
                "passos": dado.passos,
                "exploracao": dado.exploracao
            }
            for dado in dados
        ]
    }

    return placar

@app.post("/resposta")
async def enviar_resposta(resposta: RespostaDto):
    db = next(get_db())
    grupo = db.query(Grupo).filter(Grupo.id == resposta.grupo).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")

    labirinto = db.query(Labirinto).filter(Labirinto.id == resposta.labirinto).first()
    if not labirinto:
        raise HTTPException(status_code=404, detail="Labirinto não encontrado")

    vertices = resposta.vertices
    saida = [int(s) for s in labirinto.saida.split(",") if s.strip()]

    if vertices[0] != labirinto.entrada or vertices[-1] not in saida:
        raise HTTPException(status_code=400, detail="Labirinto não foi concluído")

    # Check if each consecutive pair in vertices list has an edge connecting them
    for i in range(len(vertices) - 1):
        vertice_atual_id = vertices[i]
        vertice_proximo_id = vertices[i + 1]

        aresta = db.query(Aresta).filter(
            Aresta.vertice_origem_id == vertice_atual_id,
            Aresta.vertice_destino_id == vertice_proximo_id,
            Aresta.labirinto_id == labirinto.id
        ).first()

        if not aresta:
            raise HTTPException(status_code=400, detail="Caminho inválido")

    grupo.labirintos_concluidos = (
        grupo.labirintos_concluidos + f",{labirinto.id}"
        if grupo.labirintos_concluidos
        else str(labirinto.id)
    )
    db.add(grupo)
    db.commit()

    return {"message": "Labirinto concluído com sucesso"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
