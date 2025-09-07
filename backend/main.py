from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import time  # Import the time module

from . import rag_logic
from .config import settings
from qdrant_client import QdrantClient

app = FastAPI()

qdrant_client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
)

# --- Pydantic Models ---


class PasteRequest(BaseModel):
    text: str
    filename: str


class Source(BaseModel):
    citation_num: int
    source_file: str
    text: str


class QueryRequest(BaseModel):
    query: str
    selected_doc: str | None = None

# NEW: Updated response model with all stats


class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    duration: float
    prompt_tokens: int
    completion_tokens: int
    cost: float

# --- Endpoints ---


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        filename = file.filename
        result_message = rag_logic.process_and_upload_document(
            contents, filename)
        return {"message": result_message}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.post("/api/paste")
async def paste_text(request: PasteRequest):
    try:
        file_bytes = request.text.encode("utf-8")
        result_message = rag_logic.process_and_upload_document(
            file_bytes, request.filename)
        return {"message": result_message}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.get("/api/documents")
async def get_documents():
    try:
        scrolled_points, _ = qdrant_client.scroll(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            limit=1000,
            with_payload=["source"],
            with_vectors=False,
        )
        unique_sources = sorted(list(
            {point.payload['source'] for point in scrolled_points if 'source' in point.payload}))
        return {"documents": unique_sources}
    except Exception as e:
        raw_error_msg = str(e)
        if "doesn't exist!" in raw_error_msg or "Not found: Collection" in raw_error_msg:
            return {"documents": []}
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch documents from database: {raw_error_msg}")


@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    start_time = time.time()  # Start timing
    try:
        result = await rag_logic.answer_query(request.query, request.selected_doc)

        end_time = time.time()  # End timing
        result['duration'] = round(end_time - start_time, 2)

        return result
    except Exception as e:
        print(f"Error during query processing: {e}")
        raise HTTPException(
            status_code=500, detail="An error occurred while processing your query.")


# --- SERVE FRONTEND ---
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def read_index():
    return FileResponse('frontend/index.html')
