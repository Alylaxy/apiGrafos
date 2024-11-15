# **Documentação da API**

## **Introdução**

Esta API permite a criação e gerenciamento de grupos, labirintos e sessões de jogo, além de monitorar progressos e interações em tempo real.

### **Base URL**

`http://localhost:8000`

---

## **Endpoints**

### **1. Registrar Grupo**

- **Método:** `POST`
- **URL:** `/grupo`
- **Descrição:** Cria um novo grupo e inicializa informações relacionadas a todos os labirintos existentes.
- **Body (JSON):**

  ```json
  {
    "nome": "Nome do grupo"
  }
  ```

- **Resposta (JSON):**

  ```json
  {
    "GrupoId": "UUID do grupo criado"
  }
  ```

### **2. Criar Labirinto**

- **Método:** `POST`
- **URL:** `/labirinto`
- **Descrição:** Cria um novo labirinto com seus vértices e arestas.
- **Body (JSON):**

  ```json
  {
    "dificuldade": "Nível de dificuldade",
    "vertices": 
    [
      {
        "id": 1, 
        "tipo": "entrada"
      },
      {
        "id": 2, 
        "tipo": "saida"
      }
    ],
    "arestas": 
    [
      {
        "origemId": 1, 
        "destinoId": 2, 
        "peso": 1}
    ]
  }
  ```

- **Resposta (JSON):**

  ```json
  {
    "LabirintoId": "ID do labirinto criado"
  }
  ```
  
### **3. Listar Grupos**

- **Método:** `GET`
- **URL:** `/grupos`
- **Descrição:** Retorna uma lista de todos os grupos.
- **Resposta (JSON):**

  ```json
  {
    "Grupos": 
    [
      {
        "id": "UUID", 
        "nome": "Nome do grupo", 
        "labirintos_concluidos": []
      }
    ]
  }
  ```

### **4. Listar Labirintos**

- **Método:** `GET`
- **URL:** `/labirintos`
- **Descrição:** Retorna uma lista de todos os labirintos.
- **Resposta (JSON):**

  ```json
  {
    "labirintos": 
    [
      {
        "labirinto": 1, 
        "dificuldade": "Nível de dificuldade"
      }
    ]
  }
  ```

### **5. Informações de Labirintos por Grupo**

- **Método:** `GET`
- **URL:** `/labirintos/{grupo_id}`
- **Descrição:** Retorna os labirintos associados a um grupo específico.
- **Parâmetros:**
  - `grupo_id`: UUID do grupo
- **Resposta (JSON):**

  ```json
  {
    "labirintos": 
    [
      {
        "LabirintoId": 1,
        "Dificuldade": "Nível de dificuldade",
        "Completo": false,
        "Passos": 0,
        "Exploracao": 0
      }
    ]
  }
  ```

### **6. Placar Geral**

- **Método:** `GET`
- **URL:** `/placar`
- **Descrição:** Retorna o progresso de todos os grupos em todos os labirintos.
- **Resposta (JSON):**

  ```json
  [
    {
      "grupo": "Nome do grupo",
      "labirintos": 
      [
        {
          "labirinto": 1, 
          "passos": 10, 
          "exploracao": 0.5
        }
      ]
    }
  ]
  ```

### **7. WebSocket Sessions**

- **Método:** `GET`
- **URL:** `/sessoes`
- **Descrição:** Retorna as sessões WebSocket ativas.
- **Resposta (JSON):**

  ```json
  [
    {
      "id": 1,
      "grupo_id": "UUID do grupo",
      "conexao": "ws://...",
      "grupo_nome": "Nome do grupo"
    }
  ]
  ```

### **8. WebSocket para Labirinto**

- **Método:** `WebSocket`
- **URL:** `/ws/{grupo_id}/{labirinto_id}`
- **Descrição:** Permite interações em tempo real com um labirinto.
- **Mensagens de Cliente:**
  - `"ir: id_do_vertice"`: Move para um vértice conectado.
- **Mensagens de Servidor:**
  - Estado atual: `"Vértice atual: 1, Tipo: entrada, Adjacentes(Vertice, Peso): [(2, 1)]"`

### **9. Gerar Link WebSocket**

- **Método:** `POST`
- **URL:** `/generate-websocket`
- **Descrição:** Gera um link WebSocket para interação em tempo real.
- **Body (JSON):**

  ```json
  {
    "grupo_id": "UUID do grupo",
    "labirinto_id": 1
  }
  ```

- **Resposta (JSON):**

  ```json
  {
    "websocket_url": "ws://localhost:8000/ws/{grupo_id}/{labirinto_id}"
  }
  ```

### **10. Finalizar Labirinto**

- **Método:** `POST`
- **URL:** `/resposta`
- **Descrição:** Valida o percurso finalizado de um labirinto por um grupo.
- **Body (JSON):**

  ```json
  {
    "grupo": "UUID do grupo",
    "labirinto": 1,
    "vertices": [1, 2]
  }
  ```

- **Resposta (JSON):**

  ```json
  {
    "message": "Labirinto concluído com sucesso"
  }
  ```
