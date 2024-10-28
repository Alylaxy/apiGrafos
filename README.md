# Documentação de como usar a API para participar do desafio

## Endpoints

### POST "/grupo"
#### Endpoint para cadastrar o grupo.
#### Body:
  ```JSON
    {
        "Nome" : "[Nome do Grupo]"
    }
  ```
#### Response:
  ```JSON
    {
        "Id" : "3F4365C5-77F1-405E-A6F2-66BE20521A40"
    }
  ```
### POST "/generate-websocket/"
#### Endpoint para começar o desafio para percorrer o labirinto.
#### Request Params:
    ```JSON
    {
      "grupo_id": "[Id do Grupo]",
      "labirinto_id": "[Id do Labirinto]"
    }
    ```
#### Response:
  ```JSON
  {
    "Conexao" : "ws://localhost:8000/ws/link-pro-handshake-inicial/"
  }
  ```

### GET "/labirintos/{Id}"
#### Retorna todos os labirintos disponíveis com dados do grupo escolhido.
#### Request Params:
    "[Id do Grupo]"
#### Response:
  ```JSON
  {
    "Labirintos" : [
      {
        "IdLabirinto" : 0,
        "Dificuldade" : "TesteAqui",
        "Completo" : false
      },
      {
        "IdLabirinto" : 1,
        "Dificuldade" : "ChoreAqui",
        "Completo" : true
      },
      {
        "IdLabirinto" : 2,
        "Dificuldade" : "PisouNoLego",
        "Completo" : false
      }
    ]
  }
  ```

  ## Vale lembrar que você pode acessar o link localhost:8000/docs# que terá uma descrição atualizada dos endpoints do seu programa

---
## Comportamento WebSocket
### Ao se conectar ao WebSocket, um JSON será enviado pelo servidor com as informações do labirinto.
### Formato:
```json
{
  "IdLabirinto" : 0,
  "Dificuldade" : "TesteAqui",
  "Entrada" : 0
}
```
### O campo "Entrada" é o Id do vértice de entrada do labirinto.

## Comandos do WebSocket
### "Ir:[Id do vérticce]"
#### Comando para se mover para um vértice vizinho.
> Atenção!
> Ao entrar no websocket, o primeiro vértice será a posição atual do usuário
> O JSON a seguir será enviado assim que entrar, junto com o anterior.

#### Response:
```json
{
  "Id" : 0,
  "Adjacencia" : [
    [1, 3],
    [2, 13],
    [4, 7]
  ],
  "Tipo" : 2,
  "Labirinto" : 0
}
```

#### O campo "Adjacencia" é um array com os Ids dos vértices vizinhos, e o peso de travessia.
#### O campo "Tipo" é o tipo de vértice:
  - 0: Normal
  - 1: Saída
  - 2: Entrada
#### O campo "Labirinto" é o Id do labirinto.

### "Desconectar"
#### Comando para desconectar do WebSocket. O servidor irá fechar a conexão.
