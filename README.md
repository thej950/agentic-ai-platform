# Agentic AI Platform

This repository contains the Phase 7 question-answering foundation for an enterprise-style Agentic AI Platform built with FastAPI.

## Project Structure

```text
agentic-ai-platform/
├── app/
│   ├── api/
│   │   ├── health.py
│   │   ├── upload.py
│   │   ├── process.py
│   │   ├── chunk.py
│   │   ├── embed.py
│   │   ├── retrieve.py
│   │   └── ask.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── services/
│   │   ├── document_service.py
│   │   ├── pdf_processor.py
│   │   ├── chunk_service.py
│   │   ├── embedding_service.py
│   │   ├── retrieval_service.py
│   │   ├── llm_service.py
│   │   └── prompt_builder.py
│   ├── agents/
│   ├── rag/
│   ├── models/
│   ├── schemas/
│   │   ├── upload_response.py
│   │   ├── process_response.py
│   │   ├── chunk_response.py
│   │   ├── embedding_response.py
│   │   ├── retrieval_response.py
│   │   ├── ask_request.py
│   │   └── ask_response.py
│   ├── utils/
│   └── main.py
├── uploads/
├── processed/
├── chunks/
├── vector_store/
├── tests/
├── logs/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Features

- FastAPI application configuration
- `GET /health` endpoint
- `POST /upload` endpoint for PDF files only
- `POST /process/{document_id}` endpoint for local PDF text extraction
- `POST /chunk/{document_id}` endpoint for local chunk generation
- `POST /embed/{document_id}` endpoint for local embedding generation with FAISS
- `POST /retrieve` endpoint for local FAISS-based document chunk retrieval
- `POST /ask` endpoint for question answering using the retrieval pipeline and a mock LLM abstraction
- `POST /agent-chat` endpoint for confidence-routed agent orchestration over the shared RAG pipeline
- Configurable Top-K retrieval requests
- APIRouter-based API structure
- Local vector-storage persistence in the `vector_store/` directory
- Reusable embedding service using `SentenceTransformer("all-MiniLM-L6-v2")`
- Reusable retrieval service using the same local `SentenceTransformer("all-MiniLM-L6-v2")`
- Reusable prompt builder and mock LLM abstraction for deterministic, context-grounded answers
- Modular HR, IT, and Finance agents that reuse `RetrievalService`, `PromptBuilder`, and `LLMService`
- `AgentOrchestrator` service for deterministic agent registration, confidence routing, and default fallback behavior
- Local FAISS index saved at `vector_store/index.faiss`
- Chunk metadata saved at `vector_store/metadata.json`
- Logging and `HTTPException` handling for retrieval and ask failures

## Run Locally

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment variables:

```bash
cp .env.example .env
```

4. Start the application:

```bash
uvicorn app.main:app --reload
```

5. Open the API docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Health Check

```bash
curl http://127.0.0.1:8000/health
```

## Document Upload

Use the Swagger UI or send a `multipart/form-data` request with a PDF file:

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -F "file=@sample.pdf"
```

## Document Processing

Once a PDF has been uploaded and the `document_id` is known, process it locally:

```bash
curl -X POST "http://127.0.0.1:8000/process/<document_id>"
```

## Document Chunking

After the document has been processed, generate chunks:

```bash
curl -X POST "http://127.0.0.1:8000/chunk/<document_id>"
```

## Document Embedding

After the document has been chunked, generate embeddings and save the local FAISS index:

```bash
curl -X POST "http://127.0.0.1:8000/embed/<document_id>"
```

The embedding response includes:

- `document_id`
- `chunks_embedded`
- `embedding_model`
- `vector_store`
- `status`

## Retrieval

Use the retrieve endpoint to search the local FAISS vector store for the most relevant chunks:

```bash
curl -X POST "http://127.0.0.1:8000/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the leave policy?",
    "top_k": 5
  }'
```

The response includes:

- `question`
- `results[]` with `chunk_id`, `document_id`, `chunk_number`, `similarity_score`, and `chunk_text`

## Ask

Use the ask endpoint to run a full retrieval-to-answer flow using the local mock LLM abstraction:

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the leave policy?",
    "top_k": 5
  }'
```

The response includes:

- `question`
- `answer`
- `sources[]` with `document_id`, `chunk_number`, and `similarity_score`

## Phase 10 Intelligent Intent Classification

Phase 10 upgrades local agent orchestration from keyword-first routing to confidence-based intent classification. It does not change the completed upload, processing, chunking, embedding, retrieval, ask, Bedrock-ready LLM, or agent execution phases.

The agent architecture is intentionally simple and production-friendly:

- `app/agents/base_agent.py` defines `BaseAgent`, `AgentClassification`, the shared execution contract, and the common RAG flow.
- `app/agents/hr_agent.py` classifies HR topics such as leave, attendance, holidays, salary, benefits, employee policy, and recruitment.
- `app/agents/it_agent.py` classifies IT topics such as passwords, VPN, login, email, software, network, laptop, and systems.
- `app/agents/finance_agent.py` classifies finance topics such as invoices, expenses, payments, tax, budget, purchases, reimbursement, and finance.
- `app/agents/default_agent.py` handles requests when no specialist reaches the confidence threshold.
- `app/services/orchestrator.py` registers specialist agents, asks every agent to classify the question, sorts by confidence, and chooses the highest-confidence route.
- `app/api/agent_chat.py` exposes the `POST /agent-chat` API.

Each agent reuses the existing services:

- `RetrievalService` for FAISS-backed chunk retrieval
- `PromptBuilder` for context-grounded prompt creation
- `LLMService` for mock or Bedrock-backed answer generation

No retrieval, prompt, or LLM logic is duplicated inside individual agents.

### Classification Flow

The orchestrator follows this flow for every `POST /agent-chat` request:

1. Receive the question.
2. Ask every specialist agent to run `classify(question)`.
3. Collect `can_handle`, `confidence`, and `reason` from each agent.
4. Log each agent confidence.
5. Sort classifications by confidence in descending order.
6. Select the highest-confidence specialist when confidence is `0.50` or higher.
7. Use `DefaultAgent` when the highest specialist confidence is below `0.50`.
8. Execute the selected agent through the shared RAG pipeline.

### Agent Registration

Agents are registered in `AgentOrchestrator._register_agents()` in deterministic order:

1. `HRAgent`
2. `ITAgent`
3. `FinanceAgent`

The highest-confidence agent handles the request. `DefaultAgent` is created separately as the fallback and is used only when no specialist meets the confidence threshold.

### Agent Chat

Use the agent chat endpoint to run a routed agent flow:

```bash
curl -X POST "http://127.0.0.1:8000/agent-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many annual leave days are available?"
  }'
```

The response includes:

- `selected_agent`
- `confidence`
- `classification_reason`
- `question`
- `answer`
- `sources[]` with `document_id`, `chunk_number`, and `similarity_score`

Example response:

```json
{
  "selected_agent": "HRAgent",
  "confidence": 0.95,
  "classification_reason": "Detected HR policy intent.",
  "question": "How many annual leave days are available?",
  "answer": "Based on the uploaded documents:\n\nEmployees receive 18 annual leave days...",
  "sources": [
    {
      "document_id": "example-document-id",
      "chunk_number": 5,
      "similarity_score": 0.54
    }
  ]
}
```

### Adding a New Agent

To add a new enterprise agent:

1. Create a new file in `app/agents/`.
2. Subclass `BaseAgent`.
3. Implement `classify(question: str) -> AgentClassification`.
4. Register the agent in `AgentOrchestrator._register_agents()`.

The new agent should continue to use the inherited `handle(question)` method unless it has a strong product reason to customize behavior.

## Phase 8 Bedrock Integration

The `POST /ask` API remains unchanged. The only change in this phase is the LLM implementation selected from configuration:

- `USE_MOCK_LLM=true` → uses the existing mock implementation
- `USE_MOCK_LLM=false` → uses `BedrockLLMService` through `boto3`

### Required IAM permissions

The AWS identity used by the application must be allowed to call Bedrock Runtime:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

### AWS CLI configuration

Configure AWS credentials and default region locally:

```bash
aws configure
aws sts get-caller-identity
```

### Required environment variables

Add the following to `.env`:

```env
USE_MOCK_LLM=false
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

### Notes

- No hardcoded AWS credentials are used.
- The app keeps the same `/ask` contract and only swaps the LLM backend at runtime.
- Bedrock is used only for model inference; no Lambda, orchestrator, or multiple-agent behavior is introduced.
