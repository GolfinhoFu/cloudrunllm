# N8N Workflow Design for LLM V3

Este documento descreve o design de dois fluxos de trabalho N8N para replicar a funcionalidade do serviço Python LLM V3.

## Workflow 1: AnimaGuy Chat Assistant

Este fluxo de trabalho lida com a lógica do assistente de bate-papo, incluindo gerenciamento de sessão, recuperação de informações (RAG) e geração de respostas.

### Visão Geral do Fluxo

`Webhook Trigger` -> `IF (Check Mode)` -> `Set Session ID` -> `HTTP Request (RAG)` -> `Firestore (Get History)` -> `Code (Build Prompt)` -> `Gemini` -> `Code (Update History)` -> `Firestore (Save History)` -> `Respond to Webhook`

---

### Detalhes dos Nós

#### 1. **Webhook Trigger**
- **Nome do Nó:** `Start`
- **Método HTTP:** `POST`
- **Caminho do Webhook:** `animaguy-chat`
- **Descrição:** Recebe a solicitação do usuário. Espera um corpo JSON com `text` (mensagem do usuário) e `session_id` (opcional).

#### 2. **IF Node**
- **Nome do Nó:** `Check for Session ID`
- **Condição:** `{{ $json.body.session_id }}` - `Is Not Empty`
- **Descrição:** Verifica se um `session_id` foi fornecido na solicitação.

#### 3. **Code Node (Gerar Session ID)**
- **Nome do Nó:** `Generate Session ID`
- **Conectado a:** Saída `false` do nó `Check for Session ID`.
- **Código JavaScript:**
  ```javascript
  const { v4: uuidv4 } = require('uuid');
  const sessionId = uuidv4();

  // Adiciona o novo ID de sessão aos dados existentes
  item.sessionId = sessionId;

  return item;
  ```
- **Descrição:** Gera um novo UUID v4 se nenhum `session_id` for fornecido.

#### 4. **Merge Node**
- **Nome do Nó:** `Merge Session ID`
- **Modo:** `Merge By Index`
- **Descrição:** Mescla os caminhos do fluxo (com e sem um `session_id` gerado) para continuar com um `session_id` unificado.

#### 5. **HTTP Request (RAG Service)**
- **Nome do Nó:** `Get RAG Context`
- **URL:** `[URL_DO_SEU_SERVIÇO_RAG]`
- **Método:** `POST`
- **Corpo:** `JSON`
- **Conteúdo do Corpo:**
  ```json
  {
    "query": "{{ $json.body.text }}"
  }
  ```
- **Nota Importante:** Este nó assume que a lógica RAG (busca de vetores FAISS) está exposta através de um endpoint de API. Replicar a lógica de download e carregamento de arquivos do FAISS diretamente no N8N não é prático. O serviço Python original pode ser adaptado para fornecer este endpoint.
- **Saída Esperada:** Um objeto JSON com uma chave `context`, ex: `{ "context": "..." }`.

#### 6. **Firestore Node (Get History)**
- **Nome do Nó:** `Get Session History`
- **Credenciais:** Suas credenciais do Google Cloud / Firestore.
- **Recurso:** `Document`
- **Operação:** `Get`
- **ID da Coleção:** `sessions`
- **ID do Documento:** `{{ $node["Merge Session ID"].json.sessionId }}`
- **Descrição:** Busca o histórico de bate-papo existente do Firestore.

#### 7. **Code Node (Build Prompt and History)**
- **Nome do Nó:** `Build Prompt and History`
- **Código JavaScript:**
  ```javascript
  const ragContext = $node["Get RAG Context"].json.context || "Nenhum contexto adicional encontrado.";
  const promptTemplate = `Você é Animaguy... (COLE O PROMPT_ANIMAGUY COMPLETO AQUI) ... {context}`;

  const systemPrompt = promptTemplate.replace('{context}', ragContext);

  // Obtém o histórico ou inicializa um array vazio
  const firestoreData = $node["Get Session History"].json;
  let history = [];
  if (firestoreData && firestoreData.history) {
    history = firestoreData.history;
  }

  // Formata para o N8N
  const formattedHistory = history.map(item => ({
    role: item.role,
    parts: [{ text: item.parts[0] }]
  }));

  item.systemPrompt = systemPrompt;
  item.history = formattedHistory;

  return item;
  ```
- **Descrição:** Insere o contexto RAG no template do prompt e formata o histórico do Firestore para o formato exigido pelo nó Gemini.

#### 8. **Google Vertex AI / Gemini Node**
- **Nome do Nó:** `Generate AnimaGuy Response`
- **Credenciais:** Suas credenciais do Google Cloud.
- **Recurso:** `Chat`
- **Modelo:** `gemini-1.5-flash` (ou o modelo desejado)
- **Prompt do Sistema:** `{{ $node["Build Prompt and History"].json.systemPrompt }}`
- **Entrada do Usuário:** `{{ $json.body.text }}`
- **Histórico:** Habilitar e usar a expressão `{{ $node["Build Prompt and History"].json.history }}`.

#### 9. **Code Node (Update History)**
- **Nome do Nó:** `Update History`
- **Código JavaScript:**
  ```javascript
  // Obtém o histórico do nó de construção do prompt
  const history = $node["Build Prompt and History"].json.history.map(item => ({
      role: item.role,
      parts: [item.parts[0].text] // Converte de volta para o formato de string simples
  }));

  // Adiciona a nova mensagem do usuário
  history.push({
    role: "user",
    parts: [$json.body.text]
  });

  // Adiciona a nova resposta do modelo
  history.push({
    role: "model",
    parts: [$json.answer] // 'answer' é a saída padrão do nó Gemini
  });

  item.updatedHistory = { "history": history }; // Formato para salvar no Firestore

  return item;
  ```
- **Descrição:** Adiciona a pergunta do usuário e a resposta do Gemini ao histórico da conversa.

#### 10. **Firestore Node (Save History)**
- **Nome do Nó:** `Save Session History`
- **Credenciais:** Suas credenciais do Google Cloud / Firestore.
- **Recurso:** `Document`
- **Operação:** `Update` (ou `Set` com `Merge` habilitado)
- **ID da Coleção:** `sessions`
- **ID do Documento:** `{{ $node["Merge Session ID"].json.sessionId }}`
- **Corpo:** `{{ $node["Update History"].json.updatedHistory }}`
- **Descrição:** Salva o histórico atualizado de volta no Firestore.

#### 11. **Respond to Webhook**
- **Nome do Nó:** `Send Response`
- **Responder com:** `JSON`
- **Corpo JSON:**
  ```json
  {
    "answer": "{{ $node["Generate AnimaGuy Response"].json.answer }}",
    "session_id": "{{ $node["Merge Session ID"].json.sessionId }}"
  }
  ```
- **Descrição:** Envia a resposta final de volta ao usuário.

---

## Workflow 2: Pitch Analysis

Este fluxo de trabalho lida com a análise de "pitches" de negócios, que podem ser enviados como texto ou áudio. Ele utiliza um modelo Gemini multimodal para processar o áudio nativamente e retorna uma análise estruturada de "investidores".

### Visão Geral do Fluxo

`Webhook Trigger` -> `HTTP Request (RAG)` -> `IF (Check Audio)` -> `[Caminho de Áudio] Code (Build Audio Prompt)` -> `[Caminho de Áudio] Gemini (Multimodal)` -> `[Caminho de Texto] Code (Build Text Prompt)` -> `[Caminho de Texto] Gemini (Text-only)` -> `Merge` -> `Code (Parse JSON)` -> `Respond to Webhook`

---

### Detalhes dos Nós

#### 1. **Webhook Trigger**
- **Nome do Nó:** `Start Pitch Analysis`
- **Método HTTP:** `POST`
- **Caminho do Webhook:** `pitch-analysis`
- **Modo de Resposta:** `Using 'Respond to Webhook' Node`
- **Descrição:** Recebe a solicitação `multipart/form-data`. Espera `text` (opcional) e `audio_file` (opcional). O N8N lida com o upload do arquivo e o disponibiliza na seção `binary` dos dados.

#### 2. **HTTP Request (RAG Service)**
- **Nome do Nó:** `Get RAG Context for Pitch`
- **URL:** `[URL_DO_SEU_SERVIÇO_RAG]`
- **Método:** `POST`
- **Corpo:** `JSON`
- **Conteúdo do Corpo:**
  ```json
  {
    "query": "{{ $json.body.text || 'dicas de pitch para investidores' }}"
  }
  ```
- **Descrição:** Busca contexto relevante para a análise do pitch. Usa o texto do pitch se disponível, caso contrário, usa uma consulta genérica.

#### 3. **IF Node**
- **Nome do Nó:** `Check for Audio File`
- **Condição:** `{{ $binary.audio_file }}` - `Is Not Empty`
- **Descrição:** Verifica se um arquivo de áudio foi enviado na solicitação.

#### 4. **Code Node (Build Audio Prompt)**
- **Nome do Nó:** `Build Audio Prompt`
- **Conectado a:** Saída `true` do nó `Check for Audio File`.
- **Código JavaScript:**
  ```javascript
  const ragContext = $node["Get RAG Context for Pitch"].json.context || "Analise o pitch com base em suas melhores práticas.";
  const promptTemplate = `Atue como um painel de 4 investidores... (COLE O PROMPT_PITCH_INSTRUCTION COMPLETO AQUI) ... {context}`;

  // O conteúdo do pitch é o áudio, então usamos um placeholder
  const prompt = promptTemplate.replace('{context}', ragContext)
                                 .replace('{pitch_content}', '(Áudio do pitch anexado)');

  item.prompt = prompt;

  return item;
  ```
- **Descrição:** Constrói o prompt para análise de áudio, informando ao modelo que o pitch está no anexo de áudio.

#### 5. **Google Vertex AI / Gemini Node (Multimodal)**
- **Nome do Nó:** `Analyze Audio Pitch`
- **Conectado a:** `Build Audio Prompt`
- **Credenciais:** Suas credenciais do Google Cloud.
- **Recurso:** `Prompt`
- **Modelo:** `gemini-1.5-pro` (ou um modelo multimodal)
- **Entrada do Prompt:** `{{ $node["Build Audio Prompt"].json.prompt }}`
- **Anexos:**
    - **Propriedade de Entrada:** `={{ $binary.audio_file }}`
    - **Nome da Propriedade:** `file`
- **Descrição:** Envia o prompt e o arquivo de áudio para o Gemini. O modelo processará ambos de forma nativa.

#### 6. **Code Node (Build Text Prompt)**
- **Nome do Nó:** `Build Text Prompt`
- **Conectado a:** Saída `false` do nó `Check for Audio File`.
- **Código JavaScript:**
  ```javascript
  const ragContext = $node["Get RAG Context for Pitch"].json.context || "Analise o pitch com base em suas melhores práticas.";
  const promptTemplate = `Atue como um painel de 4 investidores... (COLE O PROMPT_PITCH_INSTRUCTION COMPLETO AQUI) ... {context}`;

  const pitchContent = $json.body.text;
  const prompt = promptTemplate.replace('{context}', ragContext)
                                 .replace('{pitch_content}', pitchContent);

  item.prompt = prompt;

  return item;
  ```
- **Descrição:** Constrói o prompt para análise de texto, inserindo o texto do pitch diretamente.

#### 7. **Google Vertex AI / Gemini Node (Text-only)**
- **Nome do Nó:** `Analyze Text Pitch`
- **Conectado a:** `Build Text Prompt`
- **Credenciais:** Suas credenciais do Google Cloud.
- **Recurso:** `Prompt`
- **Modelo:** `gemini-1.5-flash`
- **Entrada do Prompt:** `{{ $node["Build Text Prompt"].json.prompt }}`
- **Descrição:** Envia o prompt com o texto do pitch para análise.

#### 8. **Merge Node**
- **Nome do Nó:** `Merge Analysis Results`
- **Modo:** `Merge By Index`
- **Descrição:** Mescla os resultados dos caminhos de áudio e texto.

#### 9. **Code Node (Parse JSON Response)**
- **Nome do Nó:** `Parse JSON Response`
- **Código JavaScript:**
  ```javascript
  // A saída do Gemini pode incluir ```json ... ```, então precisamos extrair o JSON puro.
  let geminiOutput = $json.text; // Saída padrão do nó Gemini

  if (geminiOutput.includes('```json')) {
    geminiOutput = geminiOutput.split('```json')[1].split('```')[0].trim();
  }

  try {
    item.parsedJson = JSON.parse(geminiOutput);
    item.transcription_text = ""; // Adiciona o campo para consistência
  } catch (error) {
    // Se a análise falhar, retorne um erro estruturado
    item.parsedJson = { "error": "Falha ao analisar a resposta do modelo.", "raw_output": geminiOutput };
  }

  return item;
  ```
- **Descrição:** Extrai e analisa o bloco de código JSON da resposta do Gemini. Lida com possíveis problemas de formatação.

#### 10. **Respond to Webhook**
- **Nome do Nó:** `Send Pitch Feedback`
- **Responder com:** `JSON`
- **Corpo JSON:** `{{ $node["Parse JSON Response"].json.parsedJson }}`
- **Descrição:** Envia o feedback estruturado do investidor de volta ao usuário.

---

## Guia de Implementação e Configuração

Esta seção fornece instruções sobre como configurar e implantar os fluxos de trabalho N8N descritos acima.

### Pré-requisitos

1.  **Instância do N8N:** Você precisa ter uma instância do N8N em execução (Cloud, auto-hospedada, etc.).
2.  **Credenciais do Google Cloud:**
    - Crie uma **Conta de Serviço** no seu projeto do Google Cloud.
    - Conceda as seguintes permissões a esta conta de serviço:
        - `Vertex AI User` (para acesso ao Gemini)
        - `Cloud Datastore User` (para acesso ao Firestore)
    - Crie e baixe uma **chave JSON** para esta conta de serviço.
3.  **API RAG em Execução:** A lógica de busca vetorial FAISS precisa ser exposta como um endpoint de API. O script Python original pode ser adaptado para criar um microsserviço que:
    - Recebe uma consulta (`query`) via `POST`.
    - Carrega o índice `faiss_index.bin` e `text_chunks.json`.
    - Realiza a busca de similaridade.
    - Retorna o contexto relevante em um objeto JSON: `{ "context": "..." }`.
    - **A URL deste serviço será usada nos nós "HTTP Request" dos fluxos de trabalho.**

### Configuração no N8N

#### 1. Configurar Credenciais do Google

- No N8N, vá para **Credentials** e clique em **Add credential**.
- Procure por **Google** e selecione "Google APIs".
- Em **Authentication**, escolha **Service Account**.
- Cole o conteúdo completo do seu arquivo **JSON da conta de serviço** no campo fornecido.
- Dê um nome à credencial (ex: `Google Cloud Service Account`) e salve.

#### 2. Criar os Fluxos de Trabalho

- Crie um novo fluxo de trabalho no N8N.
- Usando o guia de design acima, adicione e configure cada nó um por um.
- **Copie e cole os snippets de código JavaScript** nos nós `Code`.
- **Preencha os templates de prompt** nos nós `Code` com os prompts completos do arquivo `models/prompts.py`.
- Nos nós **Firestore** e **Gemini**, selecione a credencial do Google Cloud que você criou.
- **Atualize a URL** nos nós `HTTP Request` para apontar para o seu serviço de API RAG.

#### 3. Salvar e Ativar os Fluxos de Trabalho

- Salve cada fluxo de trabalho.
- Ative-os usando o seletor no canto superior direito.
- Seu endpoint de webhook para cada fluxo de trabalho estará ativo e pronto para receber solicitações.

### Como Usar

#### Modo AnimaGuy

Envie uma solicitação `POST` para a sua URL de webhook `animaguy-chat`:

**URL:** `[SUA_URL_N8N]/webhook/animaguy-chat`
**Método:** `POST`
**Corpo (JSON):**
```json
{
  "text": "Como posso tornar meu pitch mais atraente?",
  "session_id": "opcional-uuid-da-sessao"
}
```

#### Modo Pitch

Envie uma solicitação `POST` (`multipart/form-data`) para a sua URL de webhook `pitch-analysis`:

**URL:** `[SUA_URL_N8N]/webhook/pitch-analysis`
**Método:** `POST`
**Corpo (form-data):**
- **Para texto:**
    - `mode`: `pitch`
    - `text`: `Minha ideia é um app que conecta donos de animais de estimação...`
- **Para áudio:**
    - `mode`: `pitch`
    - `audio_file`: (anexe seu arquivo de áudio aqui)
