# Track B: AI Engineer Assessment ("Mini RAG")

This repository contains the submission for the Intern - Software & AI Developer assessment from Predusk Technology Pvt. Ltd.

**Candidate:** Aarya Abhijit Joshi

---

### Live Application URL

The fully deployed application is accessible here:

**https://mini-rag-service-728202155198.asia-south2.run.app/**

### My Resume

You can find my resume at the following link:

**https://drive.google.com/file/d/1hUDs4tekHkkc_DWHlulA8bsTB2xW_k2w/view?usp=sharing**

---

## Architecture Diagram

The application follows a standard RAG architecture deployed as a monolithic service on Google Cloud Run. The client-side is plain HTML/CSS/JS served directly by the FastAPI backend.

```
+----------------+      +-------------------------+      +-------------------+
|                |      |                         |      |                   |
|   User's       |----->|   FastAPI Backend       |----->|   Google Gemini   |
|   Browser      |      |   (on Google Cloud Run) |      |   (LLM)           |
|                |      |                         |      |                   |
+----------------+      +-----------+-------------+      +-------------------+
                          |         |         ^
                          |         |         | (Reranked Chunks)
                          |         |         |
      (Query Embedding)   |         | (Top-k Chunks)|
                          V         V         |
                      +----------------+   +----------------+
                      | Google         |   | Cohere         |
                      | Embedding Model|   | Reranker       |
                      +----------------+   +----------------+
                          ^         |
                          |         | (Vector Search)
                          |         |
                          V         V
                      +----------------+
                      | Qdrant Cloud   |
                      | (Vector DB)    |
                      +----------------+

```

## Tech Stack

- **Backend:** Python, FastAPI
- **LLM:** Google Gemini 1.5 Flash
- **Embeddings:** Google `text-embedding-004` (768 dimensions)
- **Reranker:** Cohere `rerank-english-v3.0`
- **Vector Database:** Qdrant Cloud (Hosted)
- **Containerization:** Docker
- **Cloud Hosting:** Google Cloud Run (Serverless)
- **Frontend:** HTML, CSS, JavaScript

---

## Project Setup & Quick-Start

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Aarya1104/Advanced-RAG-System
    cd Advanced-RAG-System
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    * Make a copy of `.env.example` and rename it to `.env`.
    * Fill in your API keys and Qdrant URL in the `.env` file.

4.  **Build and run the Docker container:**
    ```bash
    # Build the image
    docker build -t mini-rag-app .

    # Run the container
    docker run -p 8000:8000 --env-file .env mini-rag-app
    ```

5.  Access the application at `http://localhost:8000`.

---

## Configuration Details

This section covers the specific implementation details as required by the assessment.

- **Vector Database (Index Config):**
    - **Provider:** Qdrant Cloud
    - **Collection Name:** `mini-rag-collection`
    - **Vector Dimensionality:** 768
    - **Distance Metric:** Cosine Similarity
    - **Payload Index:** A keyword index is created on the `source` field to enable efficient filtering by document.

- **Chunking Strategy:**
    - **Method:** `RecursiveCharacterTextSplitter` from the LangChain library.
    - **Chunk Size:** 1,000 characters
    - **Chunk Overlap:** 150 characters (~15%)

- **Providers Used:**
    - **Embedding Model:** Google `text-embedding-004`
    - **Reranker:** Cohere `rerank-english-v3.0` (Top 3 results from retrieval are reranked)
    - **LLM for Answering:** Google `gemini-1.5-flash`

---

## Remarks & Trade-offs

- **Citation Reliability:** The current implementation uses a detailed prompt and a few-shot example to encourage the LLM to generate citations. While this works well, LLMs can occasionally miss a citation or cite incorrectly. A more robust system might involve parsing the LLM's reasoning steps or using a model specifically fine-tuned for citation generation.
- **Cost/Token Estimation:** The token and cost estimation is based on the usage metadata returned by the Gemini API. It does not include the costs for embeddings or the Cohere reranker, which are typically minor for this scale but would be included in a production system.
- **Next Steps / Future Improvements:**
    - **Streaming Responses:** To improve perceived performance, the LLM's answer could be streamed to the frontend token-by-token.
    - **More Granular Metadata:** The chunking process could be enhanced to extract more metadata (e.g., page numbers from PDFs, section titles) for more precise citations.
    - **User Feedback Mechanism:** Adding a "thumbs up/down" on answers would allow for collecting data to evaluate and fine-tune the RAG pipeline over time.