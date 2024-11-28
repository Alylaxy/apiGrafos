from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
import uuid
import asyncio
from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, UUID as SQLUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.schema import PrimaryKeyConstraint
from fastapi.middleware.cors import CORSMiddleware

Base = declarative_base()

# SQLAlchemy models
class Aresta(Base):
    __tablename__ = 'arestas'

    vertice_origem_id = Column(Integer, ForeignKey('vertices.id'), nullable=False)
    vertice_destino_id = Column(Integer, ForeignKey('vertices.id'), nullable=False)
    peso = Column(Integer, nullable=False)
    labirinto_id = Column(Integer, ForeignKey('labirintos.id'),nullable=False)

    # Definindo a chave primária composta
    __table_args__ = (PrimaryKeyConstraint('vertice_origem_id', 'vertice_destino_id', 'labirinto_id', name='pk_aresta'),)

    # Relacionamentos
    vertice_origem = relationship("Vertice", foreign_keys=[vertice_origem_id])
    vertice_destino = relationship("Vertice", foreign_keys=[vertice_destino_id])

    def __repr__(self):
        return f"<Aresta(origem={self.vertice_origem_id}, destino={self.vertice_destino_id}, peso={self.peso})>"

class Vertice(Base):
    __tablename__ = 'vertices'

    id = Column(Integer, nullable=False)
    labirinto_id = Column(Integer, ForeignKey('labirintos.id'), nullable=False)
    tipo = Column(Integer)

    labirinto = relationship("Labirinto", back_populates="vertices")
    
    # Relacionamento com a tabela Aresta para definir as adjacências
    arestas_origem = relationship("Aresta", foreign_keys=[Aresta.vertice_origem_id], back_populates="vertice_origem")
    arestas_destino = relationship("Aresta", foreign_keys=[Aresta.vertice_destino_id], back_populates="vertice_destino")

    __table_args__ = (PrimaryKeyConstraint('id', 'labirinto_id', name='pk_vertice'),)

    def __repr__(self):
        return f"<Vertice(id={self.id}, labirinto_id={self.labirinto_id})>"

class Labirinto(Base):
    __tablename__ = 'labirintos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vertices = relationship("Vertice", back_populates="labirinto")
    entrada = Column(Integer)
    saida = Column(String)
    dificuldade = Column(String)

    info_grupos = relationship("InfoGrupo", back_populates="labirinto")

    def __repr__(self):
        return f"<Labirinto(id={self.id}, entrada={self.entrada}, dificuldade={self.dificuldade})>"

class Grupo(Base):
    __tablename__ = 'grupos'
    
    id = Column(SQLUUID(as_uuid=True), primary_key=True)
    nome = Column(String)
    labirintos_concluidos = Column(String)
    info_grupos = relationship("InfoGrupo", back_populates="grupo")
    sessoes_websocket = relationship("SessaoWebSocket", back_populates="grupo")  

class InfoGrupo(Base):
    __tablename__ = 'info_grupos'

    grupo_id = Column(SQLUUID(as_uuid=True), ForeignKey('grupos.id'), nullable = False)
    labirinto_id = Column(Integer, ForeignKey('labirintos.id'), nullable = False)
    passos = Column(Integer)
    exploracao = Column(Float)

    __table_args__ = (PrimaryKeyConstraint('grupo_id', 'labirinto_id', name='pk_info'),)

    #Relacionamentos
    grupo = relationship("Grupo", foreign_keys=[grupo_id], back_populates="info_grupos")
    labirinto = relationship("Labirinto", foreign_keys=[labirinto_id], back_populates="info_grupos")


class SessaoWebSocket(Base):
    __tablename__ = 'sessoes_websocket'
    
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    grupo_id = Column(SQLUUID, ForeignKey('grupos.id'))  # Use String type for UUID
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

    class Config:
        orm_mode = True  # permite conversão automática de objetos ORM para JSON

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
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/grupo")
async def registrar_grupo(grupo: CriarGrupoDto):
    db = next(get_db())
    grupo_id = uuid.uuid4()
    grupo_db = Grupo(id=grupo_id, nome=grupo.nome)
    db.add(grupo_db)
    for labirinto in db.query(Labirinto).all():
        info_grupo = InfoGrupo(grupo_id=grupo_id, labirinto_id=labirinto.id, passos = 0, exploracao = 0)
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
    db.refresh(vertice_db)

    return {"LabirintoId": labirinto_db.id}

@app.get("/grupos")
async def retorna_grupos():
    db = next(get_db())
    grupos = db.query(Grupo).all()
    grupos_dto = [GrupoDto(id=grupo.id,
                           nome=grupo.nome, 
                           labirintos_concluidos=grupo.labirintos_concluidos.split(",") if grupo.labirintos_concluidos else []) 
                           for grupo in grupos]
    return {"Grupos": grupos_dto}

@app.get("/labirintos")
async def get_labirintos():
    db = next(get_db())
    labirintos = db.query(Labirinto).all()
    
    if not labirintos:
        print("Nenhum labirinto encontrado no banco de dados.")
    
    lista_labirintos = []
    for labirinto in labirintos:
        print(f"Labirinto encontrado: ID={labirinto.id}, Dificuldade={labirinto.dificuldade}")
        lista_labirintos.append(RetornaLabirintosDto(labirinto=labirinto.id, dificuldade=labirinto.dificuldade))    
    return {"labirintos": lista_labirintos}

@app.get("/labirintos/{grupo_id}")
async def get_info_labirintos(grupo_id: UUID):
    db = next(get_db())
    # Consultar as informações relacionadas ao grupo
    informacoesGrupo = db.query(InfoGrupo).filter(InfoGrupo.grupo_id == grupo_id).all()
    # Verificar se o grupo foi encontrado
    if not informacoesGrupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
        # Criar os DTOs para cada labirinto associado ao grupo
    informacoesGrupoDto = []
    for info in informacoesGrupo:
        labirinto = info.labirinto  # Acessa o objeto Labirinto relacionado
        grupo = info.grupo  # Acessa o objeto Grupo relacionado
        
        # Criar o DTO para cada InfoGrupo
        labirintoDto = LabirintoDto(
            LabirintoId=labirinto.id,
            Dificuldade=labirinto.dificuldade,
            Completo=labirinto.id in grupo.labirintos_concluidos.split(',') if grupo.labirintos_concluidos else False,
            Passos=info.passos,
            Exploracao=info.exploracao
        )
        informacoesGrupoDto.append(labirintoDto)
    # Retorna os DTOs
    return {"labirintos": informacoesGrupoDto}

@app.get("/placar")
async def get_placar():
    db = next(get_db())
    dados = db.query(InfoGrupo).all()
    placar = {}

    for dado in dados:
        grupo = dado.grupo.nome  # Nome do grupo
        if grupo not in placar:
            placar[grupo] = {
                "grupo": grupo,
                "labirintos": []
            }
        
        # Adiciona o labirinto e suas estatísticas à lista de labirintos do grupo
        placar[grupo]["labirintos"].append({
            "labirinto": dado.labirinto_id,
            "passos": dado.passos,
            "exploracao": dado.exploracao
        })

    # Converte o dicionário em uma lista para retornar
    return list(placar.values())


@app.get("/sessoes")
async def get_websocket_sessions(nome_grupo: Optional[str] = None):
    db = next(get_db())  # Obtém manualmente a sessão do banco de dados
    query = db.query(SessaoWebSocket)

    # Filtra pelo nome do grupo, se fornecido
    if nome_grupo:
        query = query.join(Grupo).filter(Grupo.nome.ilike(f"%{nome_grupo}%"))

    sessoes = query.all()

    result = []
    for sessao in sessoes:
        result.append({
            "id": sessao.id,
            "grupo_id": str(sessao.grupo_id),
            "conexao": sessao.conexao,
            "grupo_nome": sessao.grupo.nome if sessao.grupo else None
        })

    return result


manager = ConnectionManager()

@app.websocket("/ws/{grupo_id}/{labirinto_id}")
async def websocket_endpoint(websocket: WebSocket, grupo_id: UUID, labirinto_id: int):
    await manager.connect(websocket)
    db = next(get_db())
    step_count = 1

    try:
        # Obtém o labirinto e seu vértice de entrada
        labirinto = db.query(Labirinto).filter(Labirinto.id == labirinto_id).first()
        if not labirinto:
            await websocket.send_text("Labirinto não encontrado.")
            await manager.disconnect(websocket)
            return
        historico = [0]
        # Obtém o vértice de entrada
        vertice_atual = db.query(Vertice).filter(Vertice.labirinto_id == labirinto_id, Vertice.id == labirinto.entrada).first()

        if not vertice_atual:
            await manager.send_message("Vértice de entrada não encontrado.", websocket)
            await manager.disconnect(websocket)
            return

        arestas = db.query(Aresta).filter(Aresta.vertice_origem_id == vertice_atual.id).all()
        adjacentes = [(a.vertice_destino_id, a.peso) for a in arestas]

        # Envia o vértice de entrada e seus adjacentes para o cliente
        await manager.send_message(f"Vértice atual: {vertice_atual.id}, Tipo: {vertice_atual.tipo}, Adjacentes(Vertice, Peso): {adjacentes}", websocket)

        # Loop para interações do cliente
        while True:
            try:
                # Espera por uma mensagem do cliente com timeout de 60 segundos
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                if data.startswith("historico"):
                    await manager.send_message(str(historico), websocket)
                if data.startswith("ir:"):
                    # Extrai o id do vértice desejado
                    try:
                        vertice_desejado_id = int(data.split(":")[1].strip())
                    except ValueError:
                        await manager.send_message("Comando inválido. Use 'ir: id_do_vertice'", websocket)
                        continue

                    # Verifica se o vértice desejado está nos adjacentes do vértice atual
                    adjacentes = [a[0] for a in db.query(Aresta.vertice_destino_id).filter(Aresta.vertice_origem_id == vertice_atual.id).all()]
                    if vertice_desejado_id not in adjacentes:
                        await manager.send_message("Vértice inválido.", websocket)
                        continue

                    # Move para o vértice desejado
                    vertice_atual = db.query(Vertice).filter(Vertice.labirinto_id == labirinto_id, Vertice.id == vertice_desejado_id).first()

                    if not vertice_atual:
                        await manager.send_message("Erro ao acessar o vértice desejado.", websocket)
                        continue
                    
                    aresta = db.query(Aresta).filter(Aresta.vertice_origem_id == vertice_atual.id).all()

                    if not aresta:
                        await manager.send_message("Vértice sem adjacentes.", websocket)
                        continue

                    arestas = db.query(Aresta).filter(Aresta.vertice_origem_id == vertice_atual.id).all()
                    adjacentes = [(a.vertice_destino_id, a.peso) for a in arestas]
                    step_count += 1
                    historico.append(vertice_atual.id)
                    # Envia o vértice de entrada e seus adjacentes para o cliente
                    await manager.send_message(f"Vértice atual: {vertice_atual.id}, Tipo: {vertice_atual.tipo}, Adjacentes(Vertice, Peso): {adjacentes}", websocket)
                else:
                    await manager.send_message("Comando não reconhecido. Use 'ir: id_do_vertice' para se mover.", websocket)
            
            except asyncio.TimeoutError:
                # Timeout de 60 segundos sem mensagem, desconecta o WebSocket
                await manager.send_message("Conexão encerrada por inatividade.", websocket)
                await manager.disconnect(websocket)
                break

    except WebSocketDisconnect:
        grupo_info = db.query(InfoGrupo).filter(InfoGrupo.grupo_id == str(grupo_id), InfoGrupo.labirinto_id == labirinto_id).first()
        if grupo_info:
            grupo_info.passos = step_count
            grupo_info.exploracao = step_count / len(db.query(Vertice).filter(Vertice.labirinto_id == labirinto_id).all())
            db.add(grupo_info)
            db.commit()
        manager.disconnect(websocket)
        db.query(SessaoWebSocket).filter(SessaoWebSocket.conexao == websocket.url).delete()
        await manager.broadcast(f"Grupo {grupo_id} desconectado.")

@app.post("/generate-websocket/")
async def generate_websocket_link(connection: WebsocketRequestDto):
    db = next(get_db())
    grupo = db.query(Grupo).filter(Grupo.id == connection.grupo_id).first()
    labirinto = db.query(Labirinto).filter(Labirinto.id == connection.labirinto_id).first()

    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    if not labirinto:
        raise HTTPException(status_code=404, detail="Labirinto não encontrado")
    
    ws_url = f"ws://apigrafos.onrender.com/ws/{connection.grupo_id}/{connection.labirinto_id}"
    
    # Salva a sessão no banco de dados
    sessao_ws = SessaoWebSocket(grupo_id=connection.grupo_id, conexao=ws_url)
    db.add(sessao_ws)
    db.commit()
    
    return {"websocket_url": ws_url}

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
    # Verifica se o labirinto foi concluído
    if vertices[0] != labirinto.entrada or vertices[-1] not in saida:
        raise HTTPException(status_code=400, detail="Labirinto não foi concluído")

    # Check if each consecutive pair in vertices list has an edge connecting them
    for i in range(len(vertices) - 1):
        vertice_atual_id = vertices[i]
        vertice_proximo_id = vertices[i + 1]

        # Query the database to check if there is an edge between vertice_atual_id and vertice_proximo_id
        aresta = db.query(Aresta).filter(
            Aresta.vertice_origem_id == vertice_atual_id,
            Aresta.vertice_destino_id == vertice_proximo_id,
            Aresta.labirinto_id == labirinto.id
        ).first()

        # If no edge exists between consecutive vertices, return an error
        if not aresta:
            raise HTTPException(status_code=400, detail=f"Caminho inválido: vértices {vertice_atual_id} e {vertice_proximo_id} não estão conectados")

    # Se chegou até aqui, o caminho é válido e o labirinto foi concluído com sucesso
    # (Aqui você pode marcar o labirinto como concluído ou atualizar o progresso do grupo)
    grupo.labirintos_concluidos = grupo.labirintos_concluidos + f",{labirinto.id}" if grupo.labirintos_concluidos else str(labirinto.id)
    db.add(grupo)
    db.commit()

    return {"message": "Labirinto concluído com sucesso"}

    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)