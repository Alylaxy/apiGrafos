import json
from collections import deque

def carregar_labirinto(nome_arquivo):
    with open(nome_arquivo, "r") as f:
        labirinto = json.load(f)
    return labirinto

def bfs_labirinto(labirinto):
    num_vertices = len(labirinto["vertices"])
    arestas = labirinto["arestas"]

    # Criar o grafo como um dicionário de adjacências
    grafo = {v["id"]: [] for v in labirinto["vertices"]}
    for aresta in arestas:
        grafo[aresta["origemId"]].append(aresta["destinoId"])
        # Adiciona aresta reversa se o grafo não for direcional
        if not any(a["origemId"] == aresta["destinoId"] and a["destinoId"] == aresta["origemId"] for a in arestas):
            grafo[aresta["destinoId"]].append(aresta["origemId"])

    # BFS para verificar se todos os vértices são visitáveis
    visitados = set()
    fila = deque([0])  # Começa da entrada (vértice 0)

    while fila:
        atual = fila.popleft()
        if atual not in visitados:
            visitados.add(atual)
            for vizinho in grafo[atual]:
                if vizinho not in visitados:
                    fila.append(vizinho)

    return len(visitados) == num_vertices

def verificar_labirinto(nome_arquivo):
    labirinto = carregar_labirinto(nome_arquivo)
    if bfs_labirinto(labirinto):
        print("Todos os vértices do labirinto são acessíveis!")
    else:
        print("Nem todos os vértices do labirinto são acessíveis.")

# Teste com um labirinto gerado
nome_arquivo = input("Digite o nome do arquivo JSON do labirinto: ")
verificar_labirinto(nome_arquivo)
