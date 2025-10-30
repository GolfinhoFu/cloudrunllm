# LLM V3 Service

Serviço monolítico para processamento de pitches e assistente de empreendedorismo, construído com:
- **Gemini 2.0 Flash** (processamento de áudio nativo)
- **RAG com FAISS** (base de conhecimento)
- **Flask API** (endpoints REST)
- **Google Cloud Run** (deploy serverless)

## 📋 Características

### ✅ Implementado
- **Modo AnimaGuy**: Chat assistente com RAG e histórico de sessão
- **Modo Pitch**: Análise por 4 investidores simulados (Shark Tank)
- **Processamento de Áudio**: Gemini processa áudio nativamente (sem STT separado)
- **RAG Completo**: Base de conhecimento com FAISS
- **Auto-scaling**: Cloud Run gerencia instâncias automaticamente
- **Validação Robusta**: Validadores de entrada para segurança

### 🎯 Configuração Final
- **Escalonamento**: Auto-scaling nativo (sem min/max instances)
- **Custo Estimado**: ~$5-15/mês para <10 req/dia
- **Performance**: 
  - Cold start: 5-8s
  - Warm: 2-8s (dependendo do modo)

## 🏗️ Arquitetura

```
llm_V3/
├── main.py                 # Flask API principal
├── config.py              # Configurações
├── requirements.txt       # Dependências Python
├── Dockerfile            # Container definition
├── deploy.sh             # Script de deploy
├── .dockerignore         # Arquivos ignorados no build
│
├── handlers/             # Processadores de requisições
│   ├── animaguy_handler.py
│   └── pitch_handler.py
│
├── services/             # Integrações externas
│   ├── rag_service.py       # FAISS + embeddings
│   ├── gemini_service.py    # Google Gemini API
│   └── storage_service.py   # Google Cloud Storage
│
├── models/               # Prompts e templates
│   └── prompts.py
│
└── utils/                # Utilitários
    ├── firestore_client.py  # Histórico de sessões
    └── validators.py        # Validação de inputs
```

## 🚀 Deploy

### Pré-requisitos

1. **Google Cloud Project** configurado
2. **Gemini API Key** obtida
3. **GCS Bucket** com índice RAG:
   - `faiss_index.bin`
   - `text_chunks.json`
4. **gcloud CLI** instalado e autenticado

### Passos

1. **Clone/Navegue até o diretório**:
```bash
cd llm_V3
```

2. **Edite o `deploy.sh`** com suas configurações:
```bash
PROJECT_ID="seu-project-id"
GCS_RAG_BUCKET_NAME="seu-rag-bucket"
GEMINI_API_KEY="sua-api-key"
```

3. **Execute o deploy**:
```bash
chmod +x deploy.sh
./deploy.sh
```

4. **Aguarde** o deploy completar (~5-10 minutos)

## 📡 API

### Endpoint: `/process`

**Método**: `POST`  
**Content-Type**: `multipart/form-data`

### Modo AnimaGuy (Chat)

**Request**:
```bash
curl -X POST https://seu-servico.run.app/process \
  -F 'mode=animaguy' \
  -F 'text=Como fazer um bom pitch?' \
  -F 'session_id=opcional-session-id'
```

**Response**:
```json
{
  "answer": "Resposta do AnimaGuy...",
  "session_id": "uuid-da-sessao"
}
```

### Modo Pitch (Análise)

**Request com Áudio**:
```bash
curl -X POST https://seu-servico.run.app/process \
  -F 'mode=pitch' \
  -F 'audio_file=@pitch.mp3'
```

**Request com Texto**:
```bash
curl -X POST https://seu-servico.run.app/process \
  -F 'mode=pitch' \
  -F 'text=Meu pitch é sobre...'
```

**Response**:
```json
{
  "investor_feedbacks": [
    {
      "investor": "O Cético",
      "persona": "Focado em números...",
      "investorAnswer": "Análise... Estou fora.",
      "score": 7.5
    },
    // ... mais 3 investidores
  ],
  "transcription_text": ""
}
```

### Health Check

```bash
curl https://seu-servico.run.app/health
```

## 🔧 Configuração Local

### Para desenvolvimento:

1. **Crie ambiente virtual**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

2. **Instale dependências**:
```bash
pip install -r requirements.txt
```

3. **Configure variáveis de ambiente**:
```bash
export PROJECT_ID="seu-project-id"
export GCS_RAG_BUCKET_NAME="seu-rag-bucket"
export GEMINI_API_KEY="sua-api-key"
```

4. **Baixe índice RAG manualmente** ou coloque em `knowledge_base/`:
   - `faiss_index.bin` → `/tmp/faiss_index.bin`
   - `text_chunks.json` → `/tmp/text_chunks.json`

5. **Execute localmente**:
```bash
python main.py
```

Acesse: `http://localhost:8080`

## 📦 Dependências Principais

- **Flask 3.0**: Framework web
- **gunicorn 21.2**: Servidor WSGI
- **google-generativeai 0.3**: API Gemini
- **faiss-cpu 1.7**: Busca vetorial
- **google-cloud-storage 2.10**: GCS
- **google-cloud-firestore 2.13**: Firestore

## 🔍 Monitoramento

### Logs no Cloud Run:
```bash
gcloud run services logs read llm-v3-service \
  --region=southamerica-east1 \
  --limit=50
```

### Métricas:
- Acesse: [Cloud Console](https://console.cloud.google.com/run)
- Monitore: Latência, Erros, Uso de CPU/RAM

## ⚙️ Parâmetros de Performance

- **Memory**: 2GB
- **CPU**: 1 vCPU
- **Timeout**: 300s (5 minutos)
- **CPU Boost**: Habilitado (reduz cold start)
- **Concurrency**: 80 (padrão Cloud Run)

## 🐛 Troubleshooting

### Cold Start Lento
- O índice RAG é baixado na inicialização (~2-3s)
- CPU Boost já está habilitado
- Normal para primeira requisição após idle

### RAG Não Funciona
- Verifique se o bucket GCS existe
- Confirme que `faiss_index.bin` e `text_chunks.json` estão no bucket
- Veja logs para erros de download

### Erro de API Key
- Valide a `GEMINI_API_KEY` nas variáveis de ambiente
- Confirme que a key tem permissões para Gemini API

## 📝 Próximos Passos (Opcional)

- [ ] Adicionar Google Search Grounding para AnimaGuy
- [ ] Implementar cache de embeddings
- [ ] Adicionar métricas customizadas
- [ ] CI/CD pipeline automatizado
- [ ] Testes unitários e de integração

## 📄 Licença

Projeto interno - Anima Educação

---

**Versão**: 3.0  
**Última atualização**: Outubro 2025  
**Autor**: Alexandre
