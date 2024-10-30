import random
import json

def gerar_labirinto(labirinto_id, num_vertices, num_saidas, direcional=True):
    # Definindo vértices com tipos
    vertices = [{"id": i, "labirintoId": labirinto_id, "tipo": 0} for i in range(num_vertices)]
    vertices[0]["tipo"] = 1  # Entrada (sempre o vértice 0)
    
    # Escolhe saídas aleatórias entre os vértices restantes
    saidas_ids = random.sample(range(1, num_vertices), num_saidas)
    for saida_id in saidas_ids:
        vertices[saida_id]["tipo"] = 2
    
    # Gerando arestas com caminhos de distância aleatória para cada saída
    arestas = []
    for saida_id in saidas_ids:
        # Define uma distância aleatória entre 2 e o número total de vértices
        caminho_distancia = random.randint(2, num_vertices)
        
        # Seleciona um caminho de vértices, sem repetição para essa saída
        caminho = [0]  # Começando da entrada
        vertices_possiveis = list(set(range(1, num_vertices)) - {saida_id})
        caminho.extend(random.sample(vertices_possiveis, min(caminho_distancia - 1, num_vertices - 2)))
        caminho.append(saida_id)  # Finaliza o caminho com o vértice de saída

        # Cria as arestas do caminho específico para essa saída
        for i in range(len(caminho) - 1):
            origem = caminho[i]
            destino = caminho[i + 1]
            # Verificação de duplicata dependendo do tipo de direção
            if direcional:
                # Apenas checa (origem, destino) para evitar duplicatas
                if not any(a["origemId"] == origem and a["destinoId"] == destino for a in arestas):
                    arestas.append({
                        "origemId": origem,
                        "labirintoId": labirinto_id,
                        "destinoId": destino,
                        "peso": 1
                    })
            else:
                # Verifica bidirecionalmente e adiciona ambas direções
                if not any((a["origemId"] == origem and a["destinoId"] == destino) or
                           (a["origemId"] == destino and a["destinoId"] == origem) for a in arestas):
                    arestas.append({
                        "origemId": origem,
                        "labirintoId": labirinto_id,
                        "destinoId": destino,
                        "peso": 1
                    })
                    arestas.append({
                        "origemId": destino,
                        "labirintoId": labirinto_id,
                        "destinoId": origem,
                        "peso": 1
                    })

    # Adicionando arestas extras para tornar o labirinto mais complexo
    for origem in range(num_vertices):
        num_conexoes = random.randint(1, min(3, num_vertices - 1))
        destinos = random.sample(range(num_vertices), num_conexoes)
        
        for destino in destinos:
            if destino != origem:
                if direcional:
                    # Apenas checa (origem, destino) para direcional
                    if not any(a["origemId"] == origem and a["destinoId"] == destino for a in arestas):
                        arestas.append({
                            "origemId": origem,
                            "labirintoId": labirinto_id,
                            "destinoId": destino,
                            "peso": 1
                        })
                else:
                    # Verifica bidirecionalmente e adiciona ambas direções
                    if not any((a["origemId"] == origem and a["destinoId"] == destino) or
                               (a["origemId"] == destino and a["destinoId"] == origem) for a in arestas):
                        arestas.append({
                            "origemId": origem,
                            "labirintoId": labirinto_id,
                            "destinoId": destino,
                            "peso": 1
                        })
                        arestas.append({
                            "origemId": destino,
                            "labirintoId": labirinto_id,
                            "destinoId": origem,
                            "peso": 1
                        })

    # Configurando a saída final
    labirinto = {
        "vertices": vertices,
        "arestas": arestas,
        "entrada": 0,
        "dificuldade": "Basiquinho e pequeno" if num_vertices <= 5 else "Intermediario"
    }
    
    return json.dumps(labirinto, indent=4)

# Exemplo de uso
labirinto_id = int(input("Digite o ID do labirinto: "))
num_vertices = int(input("Digite o número de vértices: "))
num_saidas = int(input("Digite o número de saídas: "))
direcional = input("O labirinto é direcional? (s/n): ").strip().lower() == 's'
print(gerar_labirinto(labirinto_id, num_vertices, num_saidas, direcional))
