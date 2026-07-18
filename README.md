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
- Configurable Top-K retrieval requests
- APIRouter-based API structure
- Local vector-storage persistence in the `vector_store/` directory
- Reusable embedding service using `SentenceTransformer("all-MiniLM-L6-v2")`
- Reusable retrieval service using the same local `SentenceTransformer("all-MiniLM-L6-v2")`
- Reusable prompt builder and mock LLM abstraction for deterministic, context-grounded answers
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
