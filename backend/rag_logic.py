import google.generativeai as genai
import cohere
from qdrant_client import QdrantClient, models
from .config import settings
import uuid
import io
import re

# Library Imports
from pypdf import PdfReader
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- CLIENT INITIALIZATION (No changes) ---
genai.configure(api_key=settings.GOOGLE_API_KEY)
co = cohere.Client(settings.COHERE_API_KEY)
qdrant_client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
)

# --- QDRANT SETUP (MODIFIED TO CREATE PAYLOAD INDEX) ---
try:
    qdrant_client.get_collection(
        collection_name=settings.QDRANT_COLLECTION_NAME)
    print("Qdrant collection already exists.")
except Exception:
    print("Creating Qdrant collection...")
    qdrant_client.create_collection(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=768, distance=models.Distance.COSINE),
    )
    print("Collection created successfully.")

    # *** FIX 1: Create the payload index for the 'source' field. ***
    print("Creating payload index for 'source' field...")
    qdrant_client.create_payload_index(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        field_name="source",
        field_schema=models.PayloadSchemaType.KEYWORD
    )
    print("Payload index created successfully.")


# --- HELPER FUNCTIONS & DOCUMENT PROCESSING (No changes) ---
def _extract_text_from_pdf(file_bytes: bytes) -> str:
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    text = "".join(page.extract_text() or "" for page in reader.pages)
    return text


def _extract_text_from_docx(file_bytes: bytes) -> str:
    doc_file = io.BytesIO(file_bytes)
    doc = Document(doc_file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text


def process_and_upload_document(file_bytes: bytes, filename: str):
    document_text = ""
    if filename.lower().endswith(".pdf"):
        document_text = _extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith(".docx"):
        document_text = _extract_text_from_docx(file_bytes)
    elif filename.lower().endswith(".txt"):
        document_text = file_bytes.decode("utf-8")
    else:
        raise ValueError(
            "Unsupported file type. Please upload a .txt, .pdf, or .docx file.")

    if not document_text.strip():
        raise ValueError(
            "Extracted text is empty. The document might be empty or scanned.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
    )
    chunks = text_splitter.split_text(document_text)

    if not chunks:
        raise ValueError("Document could not be split into chunks.")

    embedding_model = "models/text-embedding-004"
    result = genai.embed_content(
        model=embedding_model,
        content=chunks,
        task_type="RETRIEVAL_DOCUMENT",
        title=filename
    )
    embeddings = result['embedding']

    points = [
        models.PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"text": chunk, "source": filename, "chunk_num": idx + 1}
        )
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    qdrant_client.upsert(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points=points,
        wait=True,
    )
    return f"Successfully processed '{filename}' and uploaded {len(chunks)} chunks to Qdrant."

# --- answer_query function (MODIFIED PROMPT) ---


async def answer_query(query: str, selected_doc: str | None = None) -> dict:
    embedding_model = "models/text-embedding-004"
    embedding_result = genai.embed_content(
        model=embedding_model, content=query, task_type="RETRIEVAL_QUERY")
    if 'embedding' not in embedding_result:
        raise ValueError("Failed to embed the query.")
    query_embedding = embedding_result['embedding']

    query_filter = None
    if selected_doc and selected_doc != "all":
        query_filter = models.Filter(must=[models.FieldCondition(
            key="source", match=models.MatchValue(value=selected_doc))])

    search_results = qdrant_client.search(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query_vector=query_embedding,
        query_filter=query_filter,
        limit=10,
        with_payload=True
    )

    if not search_results:
        return {"answer": "I couldn't find any relevant information in the selected document(s).", "sources": [], "prompt_tokens": 0, "completion_tokens": 0, "cost": 0}

    retrieved_docs_payloads = [result.payload for result in search_results]

    reranked_results = co.rerank(
        query=query,
        documents=[doc['text'] for doc in retrieved_docs_payloads],
        top_n=3,
        model='rerank-english-v3.0'
    )

    final_docs_for_context = [retrieved_docs_payloads[res.index]
                              for res in reranked_results.results]

    context_for_llm = ""
    for i, doc in enumerate(final_docs_for_context):
        context_for_llm += f"Source [{i+1}]: (From File: {doc['source']}, Chunk: {doc.get('chunk_num', 'N/A')})\n"
        context_for_llm += f"{doc['text']}\n\n"

    # *** FIX 2: Added a few-shot example to the prompt for better citation results. ***
    prompt = f"""
    You are a helpful assistant. Your task is to answer the user's query based ONLY on the provided sources.
    - Do not use any prior knowledge.
    - You MUST cite the sources you use in your answer. To cite a source, use the format [X] where X is the source number.
    - Your answer must be grounded in the provided sources. If the answer is not in the sources, state that clearly.
    - List the citations at the end of the sentence or paragraph where the information was used.

    Here is an example of a good answer:
    -----------------
    The sky appears blue due to a phenomenon called Rayleigh scattering [1]. This is where shorter wavelengths of light are scattered more effectively by the particles in the atmosphere [2].
    -----------------
    
    Provided Sources:
    ---
    {context_for_llm}
    ---

    User Query: {query}

    Answer:
    """

    generation_model = genai.GenerativeModel('gemini-1.5-flash')
    response = await generation_model.generate_content_async(prompt)

    prompt_tokens = response.usage_metadata.prompt_token_count
    completion_tokens = response.usage_metadata.candidates_token_count
    cost = ((prompt_tokens / 1_000_000) * 0.35) + \
        ((completion_tokens / 1_000_000) * 0.70)

    answer_text = response.text
    sources_for_response = []

    cited_indices = sorted(list(set(int(i)
                           for i in re.findall(r'\[(\d+)\]', answer_text))))

    for i in cited_indices:
        if 0 < i <= len(final_docs_for_context):
            source_doc = final_docs_for_context[i-1]
            sources_for_response.append({
                "citation_num": i,
                "source_file": source_doc['source'],
                "text": source_doc['text']
            })

    return {
        "answer": answer_text,
        "sources": sources_for_response,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost": cost
    }
