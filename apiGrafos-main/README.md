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
### GET "/iniciar/{Id}"
#### Endpoint para começar o desafio para percorrer o labirinto.
#### Request Params:
    "[Id do grupo]"
#### Response:
  ```JSON
  {
    "Conexao" : "ws://link.pro.handshake.inicial/"
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
        "Completo" : false,
        "Passos" : 0,
        "Exploracao" : 0.0
      },
      {
        "IdLabirinto" : 1,
        "Dificuldade" : "ChoreAqui",
        "Completo" : true,
        "Passos" : 8272,
        "Exploracao" : 0.1
      },
      {
        "IdLabirinto" : 2,
        "Dificuldade" : "PisouNoLego",
        "Completo" : false,
        "Passos" : 40,
        "Exploracao" : 0.001
      }
    ]
  }
  ```

### GET "/sessoes"
#### Retorna todas as sessões WebSocket armazenadas/ativas.
#### USO INTERNO
#### Response:
  ```JSON
    {
      "Sessoes" : [
        {
          "IdGrupo" : "3F4365C5-77F1-405E-A6F2-66BE20521A40",
          "Conexao" : "http://link.pro.handshake.inicial/1"
        },
        {
          "IdGrupo" : "9AAB3144-9CF9-4FCA-BF1C-26BDA4D0C967",
          "Conexao" : "http://link.pro.handshake.inicial/2"
        }
      ]
    }
  ```

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
> O primeiro comando deverá sempre ser "Ir" como evento e no JSON deverá ser
> referenciado o vértice de entrada do labirinto, referenciado pela chave "Entrada" no
> JSON que o usuário receberá ao se conenctar no WebSocket

#### Response:
```json
{
  "Id" : 0,
  "Adjacencia" : [
    1,
    2
  ],
  "Tipo" : 2,
  "Labirinto" : 0
}
```
#### O campo "Adjacencia" é um array com os Ids dos vértices vizinhos.
#### O campo "Tipo" é o tipo de vértice:
  - 0: Normal
  - 1: Saída
  - 2: Entrada
#### O campo "Labirinto" é o Id do labirinto.

### "Desconectar"
#### Comando para desconectar do WebSocket. O servidor irá fechar a conexão.
