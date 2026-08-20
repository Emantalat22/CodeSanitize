# CodeSanitize - Backend

FastAPI backend service powering **CodeSanitize**, providing modular interfaces for syntax parsing, AST analysis, semantics-preserving normalization/transformation, and validation.

## Architecture

- `app/api/`: REST API endpoints and routing.
- `app/models/`: Pydantic v2 data models, request/response contracts.
- `app/parsers/`: Abstract language parser contracts (Tree-sitter / Native AST).
- `app/analyzers/`: Abstract code pattern and AST analyzers.
- `app/transformers/`: Deterministic semantics-preserving transformation contracts.
- `app/validators/`: Formal verification and equivalence testing contracts.
- `app/services/`: Business logic and service orchestration.

## Getting Started

### 1. Install Dependencies

```bash
cd backend
python -m pip install -r requirements.txt
```

### 2. Run Tests

```bash
pytest
```

### 3. Start Development Server

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health Check: `http://127.0.0.1:8000/api/health`
- OpenAPI Swagger Docs: `http://127.0.0.1:8000/docs`
