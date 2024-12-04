import random
import json

def gerar_labirinto(labirinto_id, num_vertices, num_saidas, direcional=True, com_peso=False):
    vertices = [{"id": i, "tipo": 0} for i in range(num_vertices)]
    vertices[0]["tipo"] = 1  # Entrada (sempre o vértice 0)
    
    saidas_ids = random.sample(range(1, num_vertices), num_saidas)
    for saida_id in saidas_ids:
        vertices[saida_id]["tipo"] = 2
    
    arestas = []
    vertices_na_arvore = {0}
    vertices_faltantes = set(range(1, num_vertices))

    def obter_peso():
        return random.randint(1, 20) if com_peso else 1

    while vertices_faltantes:
        origem = random.choice(list(vertices_na_arvore))
        destino = vertices_faltantes.pop()
        
        arestas.append({
            "origemId": origem,
            "destinoId": destino,
            "peso": obter_peso()
        })
        
        if not direcional:
            arestas.append({
                "origemId": destino,
                "destinoId": origem,
                "peso": obter_peso()
            })
        
        vertices_na_arvore.add(destino)

    if direcional:
        for vertice in range(1, num_vertices):
            if not any(a["origemId"] == vertice and a["destinoId"] == 0 for a in arestas):
                arestas.append({
                    "origemId": vertice,
                    "destinoId": 0,
                    "peso": obter_peso()
                })

    for origem in range(num_vertices):
        num_conexoes = random.randint(1, min(3, num_vertices - 1))
        destinos = random.sample(range(num_vertices), num_conexoes)
        
        for destino in destinos:
            if destino != origem:
                if direcional:
                    if not any(a["origemId"] == origem and a["destinoId"] == destino for a in arestas):
                        arestas.append({
                            "origemId": origem,
                            "destinoId": destino,
                            "peso": obter_peso()
                        })
                else:
                    if not any((a["origemId"] == origem and a["destinoId"] == destino) or
                               (a["origemId"] == destino and a["destinoId"] == origem) for a in arestas):
                        arestas.append({
                            "origemId": origem,
                            "destinoId": destino,
                            "peso": obter_peso()
                        })
                        arestas.append({
                            "origemId": destino,
                            "destinoId": origem,
                            "peso": obter_peso()
                        })

    labirinto = {
        "labirintoId": labirinto_id,
        "vertices": vertices,
        "arestas": arestas,
        "entrada": 0,
        "dificuldade": "Basiquinho e pequeno" if num_vertices <= 5 else "Intermediario"
    }
    
    nome_arquivo = f"{labirinto_id}_labirinto.json"
    with open(nome_arquivo, "w") as f:
        json.dump(labirinto, f, indent=4)

    print(f"Labirinto salvo como {nome_arquivo}")

labirinto_id = int(input("Digite o ID do labirinto: "))
num_vertices = int(input("Digite o número de vértices: "))
num_saidas = int(input("Digite o número de saídas: "))
direcional = input("O labirinto é direcional? (s/n): ").strip().lower() == 's'
com_peso = input("O labirinto terá peso aleatório nas arestas? (s/n): ").strip().lower() == 's'
gerar_labirinto(labirinto_id, num_vertices, num_saidas, direcional, com_peso)
