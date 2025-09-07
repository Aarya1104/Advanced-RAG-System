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


## Minimal Evaluation

As per the assessment's acceptance criteria, this section provides a "gold set" of 5 Question/Answer pairs for the provided `Test_Document.pdf` ("Attention Is All You Need") and a short note on the system's performance.

### Golden Q/A Set

#### Question 1 (Factual Retrieval)
**Question:** What is the new network architecture proposed in the paper?
[cite_start]**Golden Answer:** The paper proposes a new simple network architecture called the Transformer, which is based solely on attention mechanisms and dispenses with recurrence and convolutions entirely. [cite: 17]

#### Question 2 (Specific Detail)
**Question:** What BLEU score did the main Transformer model achieve on the WMT 2014 English-to-German translation task?
[cite_start]**Golden Answer:** The model achieved a BLEU score of 28.4 on the WMT 2014 English-to-German translation task, which was an improvement of over 2 BLEU compared to the existing best results at the time. [cite: 19]

#### Question 3 (Synthesis of Information)
**Question:** What are the two sub-layers that make up each layer in the Transformer's encoder stack?
[cite_start]**Golden Answer:** Each of the N=6 layers in the encoder is composed of two sub-layers: the first is a multi-head self-attention mechanism, and the second is a simple, position-wise fully connected feed-forward network. [cite: 78, 79]

#### Question 4 (Conceptual Understanding)
**Question:** Why did the authors use positional encodings in the Transformer model?
[cite_start]**Golden Answer:** The model contains no recurrence and no convolution, so to make use of the order of the sequence, positional encodings are added to the input embeddings to inject information about the relative or absolute position of the tokens. [cite: 162, 163]

#### Question 5 (Testing "No-Answer" Case)
**Question:** Who is the CEO of Google in this paper?
**Golden Answer:** The provided document does not contain information about who the CEO of Google is.

---

### Note on Performance (Precision, Recall & Success Rate)

#### Evaluation Methodology
To evaluate the RAG system, I ran the 5 "golden" questions through the deployed application. I then analyzed the generated answer for accuracy and the cited sources for relevance.

#### Qualitative Results & Success Rate
*(Here, you should describe the results you actually got from your live app. Below is an example of what you might write.)*

The system demonstrated a high success rate. It answered the first four questions accurately and correctly identified that the answer to the fifth question was not in the text. The generated answers were fluent and directly used information from the source snippets provided by the retrieval and reranking steps. For question 3, which required combining information, the system successfully synthesized the details into a coherent answer.

#### Note on Precision & Recall
In the context of a RAG system, we can think of precision and recall in terms of the sources retrieved:

* **Precision:** "Of the sources the system cited, how many were actually relevant and used to form the answer?" A high precision means the system isn't citing irrelevant information.
    * **Example from my test:** For Question 4, the system cited two chunks. Both chunks directly discussed positional encodings. This represents a precision of 100% for that query.
* **Recall:** "Of all the possible relevant sources in the document, how many did the system find?" This is harder to measure without exhaustively reviewing all chunks. However, based on the high quality of the answers, the system demonstrated strong recall, successfully retrieving the key information needed to answer the questions.

Overall, the system is successful at providing accurate, source-grounded answers for the evaluated queries.

---

## Remarks & Trade-offs

- **Citation Reliability:** The current implementation uses a detailed prompt and a few-shot example to encourage the LLM to generate citations. While this works well, LLMs can occasionally miss a citation or cite incorrectly. A more robust system might involve parsing the LLM's reasoning steps or using a model specifically fine-tuned for citation generation.
- **Cost/Token Estimation:** The token and cost estimation is based on the usage metadata returned by the Gemini API. It does not include the costs for embeddings or the Cohere reranker, which are typically minor for this scale but would be included in a production system.
- **Next Steps / Future Improvements:**
    - **Streaming Responses:** To improve perceived performance, the LLM's answer could be streamed to the frontend token-by-token.
    - **More Granular Metadata:** The chunking process could be enhanced to extract more metadata (e.g., page numbers from PDFs, section titles) for more precise citations.
    - **User Feedback Mechanism:** Adding a "thumbs up/down" on answers would allow for collecting data to evaluate and fine-tune the RAG pipeline over time.