import os
import json
import logging
import streamlit as st
import numpy as np
import faiss
from datetime import datetime
from typing import List, Dict, Any

from groq import Groq
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from rank_bm25 import BM25Okapi
# ADD THESE TWO LINES HERE:
from dotenv import load_dotenv
load_dotenv()  # This loads your .env file
print(f"API Key loaded: {os.getenv('GROQ_API_KEY')[:10]}...")

# =============================================================================
# CONFIGURATION
# =============================================================================
POLICY_DIR = "policies"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K = 8
RERANK_K = 3
HYBRID_ALPHA = 0.7  # 70% semantic, 30% keyword

# =============================================================================
# LOGGING SETUP
# =============================================================================
logging.basicConfig(
    filename="rag_trace.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_retrieval(query: str, results: List[Dict], prompt_version: str):
    """Log retrieval results for monitoring"""
    logging.info(f"\n{'='*60}")
    logging.info(f"QUERY: {query}")
    logging.info(f"PROMPT VERSION: {prompt_version}")
    logging.info(f"TIMESTAMP: {datetime.now().isoformat()}")
    logging.info(f"RETRIEVED CHUNKS: {len(results)}")
    for i, r in enumerate(results, 1):
        logging.info(f"  [{i}] Source: {r['source']} | Chunk: {r['chunk_id']} | Score: {r['score']}")
    logging.info(f"{'='*60}\n")

# =============================================================================
# STREAMLIT UI SETUP
# =============================================================================
st.set_page_config(
    page_title="Policy RAG Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Policy RAG Assistant")
st.caption("🚀 Grounded QA with Hybrid Retrieval, Prompt Engineering & Hallucination Control")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    st.markdown(f"""
    **Chunking Strategy:**
    - Chunk Size: `{CHUNK_SIZE}` chars
    - Overlap: `{CHUNK_OVERLAP}` chars
    - Top-K: `{TOP_K}` candidates
    - Final: `{RERANK_K}` chunks
    
    **Hybrid Retrieval:**
    - Semantic: `{int(HYBRID_ALPHA*100)}%`
    - Keyword: `{int((1-HYBRID_ALPHA)*100)}%`
    
    **Models:**
    - LLM: `llama-3.3-70b-versatile` (Groq)
    - Embeddings: `all-MiniLM-L6-v2` (Local)
    """)
    
    if st.button("🔄 Clear Cache & Reload"):
        st.cache_resource.clear()
        st.rerun()

# =============================================================================
# DOCUMENT LOADING
# =============================================================================
def load_documents(folder: str) -> List[Document]:
    """
    Load all PDF and TXT documents from the policies folder.
    
    Returns:
        List of Document objects with metadata
    """
    if not os.path.exists(folder):
        st.error(f"❌ Folder '{folder}' not found. Please create it and add policy documents.")
        st.info("💡 Create a 'policies' folder and add your policy PDFs/TXTs")
        return []
    
    docs = []
    files = [f for f in os.listdir(folder) if f.endswith((".pdf", ".txt"))]
    
    if not files:
        st.warning(f"⚠️ No PDF/TXT files found in '{folder}'. Please add policy documents.")
        return []
    
    for file in files:
        try:
            filepath = os.path.join(folder, file)
            if file.endswith(".pdf"):
                loader = PyPDFLoader(filepath)
            else:
                loader = TextLoader(filepath)
            
            pages = loader.load()
            for p in pages:
                p.metadata["source"] = file
            docs.extend(pages)
            logging.info(f"✅ Loaded: {file} ({len(pages)} pages)")
        except Exception as e:
            st.error(f"❌ Error loading {file}: {e}")
            logging.error(f"Failed to load {file}: {e}")
    
    return docs

# =============================================================================
# SMART CHUNKING WITH EXPLANATION
# =============================================================================
def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Smart chunking strategy for policy documents.
    
    STRATEGY EXPLANATION:
    ---------------------
    Chunk Size: 500 characters (~125 tokens)
    - Policy clauses typically span 100-200 characters
    - This size captures 2-3 related clauses (complete semantic units)
    - Smaller chunks (<400) fragment important context
    - Larger chunks (>600) include irrelevant information
    
    Overlap: 100 characters  
    - Prevents splitting critical information mid-sentence
    - Ensures important clauses appear in multiple chunks
    - Improves recall for boundary cases
    
    Separators: Hierarchical splitting
    - Prioritizes natural document boundaries (paragraphs, sections)
    - Only splits sentences as a fallback
    - Preserves semantic coherence of policy statements
    
    Returns:
        List of chunked Document objects with metadata
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n\n",   # Major sections
            "\n\n",     # Paragraphs
            "\n",       # Line breaks
            ". ",       # Sentences
            "; ",       # Clauses
            ", ",       # Sub-clauses
            " "         # Words (last resort)
        ],
        length_function=len,
        is_separator_regex=False
    )
    
    chunks = splitter.split_documents(documents)
    
    # Add metadata for monitoring
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
        chunk.metadata["char_count"] = len(chunk.page_content)
        chunk.metadata["token_estimate"] = len(chunk.page_content) // 4
    
    logging.info(f"📦 Created {len(chunks)} chunks from {len(documents)} documents")
    
    return chunks

# =============================================================================
# FAISS INDEX CREATION
# =============================================================================
def build_faiss_index(chunks: List[Document], embedder: HuggingFaceEmbeddings) -> faiss.Index:
    """
    Build FAISS vector store for semantic search.
    
    Args:
        chunks: List of document chunks
        embedder: HuggingFace embeddings model
        
    Returns:
        FAISS index for similarity search
    """
    with st.spinner("🔄 Building FAISS index..."):
        vectors = embedder.embed_documents([c.page_content for c in chunks])
        dim = len(vectors[0])
        
        # Using L2 distance (can also use IndexFlatIP for cosine similarity)
        index = faiss.IndexFlatL2(dim)
        index.add(np.array(vectors).astype("float32"))
        
        logging.info(f"🔍 FAISS index created: {index.ntotal} vectors, dimension {dim}")
    
    return index

# =============================================================================
# BM25 INDEX CREATION
# =============================================================================
def build_bm25_index(chunks: List[Document]) -> BM25Okapi:
    """
    Build BM25 index for keyword-based search.
    
    BM25 is excellent for exact term matching in policy documents
    where specific keywords matter ("14-day", "refund", "cancellation").
    
    Args:
        chunks: List of document chunks
        
    Returns:
        BM25 index
    """
    tokenized_chunks = [chunk.page_content.lower().split() for chunk in chunks]
    bm25 = BM25Okapi(tokenized_chunks)
    logging.info(f"📚 BM25 index created with {len(tokenized_chunks)} documents")
    return bm25

# =============================================================================
# HYBRID RETRIEVAL (SEMANTIC + KEYWORD)
# =============================================================================
def hybrid_retrieve(
    query: str,
    chunks: List[Document],
    faiss_index: faiss.Index,
    bm25_index: BM25Okapi,
    embedder: HuggingFaceEmbeddings,
    alpha: float = HYBRID_ALPHA
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval combining semantic (FAISS) and keyword (BM25) search.
    
    WHY HYBRID FOR POLICIES:
    ------------------------
    1. Semantic search catches paraphrases:
       - "return item" → "refund request"
       - "send back" → "return policy"
    
    2. Keyword search catches exact terms:
       - "14-day window"
       - "non-refundable"
       - Specific policy numbers/codes
    
    3. Combined scoring balances both:
       - alpha = 0.7 means 70% semantic, 30% keyword
       - This ratio works well for policy docs
    
    Args:
        query: User question
        chunks: Document chunks
        faiss_index: FAISS vector index
        bm25_index: BM25 keyword index
        embedder: Embeddings model
        alpha: Weight for semantic vs keyword (default 0.7)
        
    Returns:
        List of retrieved chunks with scores and metadata
    """
    
    # 1. SEMANTIC RETRIEVAL (FAISS)
    q_vec = embedder.embed_query(query)
    semantic_distances, semantic_indices = faiss_index.search(
        np.array([q_vec]).astype("float32"),
        min(TOP_K * 2, len(chunks))  # Get more candidates
    )
    
    # Normalize L2 distances to similarity scores (0-1)
    max_dist = np.max(semantic_distances[0]) if len(semantic_distances[0]) > 0 else 1
    semantic_scores = 1 - (semantic_distances[0] / (max_dist + 1e-6))
    
    # 2. KEYWORD RETRIEVAL (BM25)
    query_tokens = query.lower().split()
    keyword_scores = bm25_index.get_scores(query_tokens)
    
    # Normalize BM25 scores to 0-1 range
    max_bm25 = np.max(keyword_scores) if np.max(keyword_scores) > 0 else 1
    keyword_scores = keyword_scores / (max_bm25 + 1e-6)
    
    # 3. COMBINE SCORES
    combined_scores = {}
    
    # Add semantic scores
    for idx, score in zip(semantic_indices[0], semantic_scores):
        combined_scores[int(idx)] = alpha * float(score)
    
    # Add keyword scores
    for idx, score in enumerate(keyword_scores):
        if idx in combined_scores:
            combined_scores[idx] += (1 - alpha) * float(score)
        else:
            combined_scores[idx] = (1 - alpha) * float(score)
    
    # 4. RANK AND SELECT TOP-K
    top_indices = sorted(
        combined_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:RERANK_K]
    
    # 5. FORMAT RESULTS
    results = []
    for idx, score in top_indices:
        chunk = chunks[idx]
        results.append({
            "chunk_id": chunk.metadata["chunk_id"],
            "source": chunk.metadata.get("source", "unknown"),
            "page": chunk.metadata.get("page", "N/A"),
            "score": round(score, 4),
            "text": chunk.page_content,
            "char_count": chunk.metadata.get("char_count", 0)
        })
    
    return results

# =============================================================================
# PROMPT TEMPLATES (V1 & V2)
# =============================================================================

PROMPT_V1 = PromptTemplate(
    input_variables=["context", "question"],
    template="""Answer the question using the context below.

Context:
{context}

Question:
{question}

Answer:
"""
)

PROMPT_V2 = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are an expert assistant for company policy documents.

STRICT INSTRUCTIONS:
1. Answer ONLY using the provided context below
2. Do NOT use outside knowledge or make assumptions
3. If the answer is not present or unclear, respond with:
   "The provided policy documents do not contain sufficient information to answer this question."
4. Always cite the source document name in your answer
5. Be precise and quote exact policy terms when relevant

Context:
{context}

Question:
{question}

Respond in valid JSON format:
{{
  "answer": "<your answer or refusal message>",
  "source_document": "<policy document name or 'Not specified'>",
  "confidence": "High | Medium | Low",
  "reasoning": "<brief explanation of how you arrived at this answer>"
}}

JSON Response:
"""
)

# =============================================================================
# LLM INFERENCE (GROQ)
# =============================================================================
def call_llm(prompt: str, model: str = "llama-3.3-70b-versatile") -> str:
    """
    Call Groq LLM for inference.
    
    Args:
        prompt: Formatted prompt string
        model: Groq model name
        
    Returns:
        Model response text
    """
    try:
        # Get API key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Error: GROQ_API_KEY not found in environment variables"
        
        # Initialize client (compatible with different versions)
        try:
            client = Groq(api_key=api_key)
        except TypeError:
            # Fallback for older versions
            from groq import Client
            client = Client(api_key=api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0  # Deterministic for consistency
        )
        answer = response.choices[0].message.content
        logging.info(f"🤖 LLM Response: {answer[:100]}...")
        return answer
    except Exception as e:
        logging.error(f"❌ LLM call failed: {e}")
        return f"Error calling LLM: {str(e)}"

# =============================================================================
# PIPELINE SETUP (CACHED FOR PERFORMANCE)
# =============================================================================
@st.cache_resource
def setup_rag_pipeline():
    """
    Initialize RAG pipeline components.
    Cached to avoid rebuilding on every query.
    
    Returns:
        Tuple of (chunks, faiss_index, bm25_index, embedder)
    """
    # Load documents
    docs = load_documents(POLICY_DIR)
    if not docs:
        return None, None, None, None
    
    # Chunk documents
    chunks = chunk_documents(docs)
    
    # Initialize embedder (using local HuggingFace model)
    embedder = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Build indices
    faiss_index = build_faiss_index(chunks, embedder)
    bm25_index = build_bm25_index(chunks)
    
    st.success(f"✅ Pipeline ready: {len(docs)} documents → {len(chunks)} chunks")
    logging.info(f"✅ Pipeline initialized successfully")
    
    return chunks, faiss_index, bm25_index, embedder

# =============================================================================
# MAIN UI
# =============================================================================

# Initialize pipeline
chunks, faiss_index, bm25_index, embedder = setup_rag_pipeline()

if chunks is None:
    st.stop()

# Two columns for question input and prompt selection
col1, col2 = st.columns([3, 1])

with col1:
    question = st.text_input(
        "❓ Ask a policy-related question:",
        placeholder="e.g., What is the refund policy for electronics?"
    )

with col2:
    prompt_choice = st.selectbox(
        "🔧 Prompt Version",
        ["Prompt V1 (Baseline)", "Prompt V2 (Improved)"]
    )

# Add example questions
with st.expander("💡 Example Questions"):
    st.markdown("""
    - Within how many hours can a customer cancel an order after placing it?
    - How many days does a customer have to request a refund after receiving a product?
    - Are digital or downloadable products eligible for a refund?
    - If an order is cancelled within the allowed time, how long does it take to receive the refund?
    - What conditions must a product meet to be eligible for a refund?
    """)




# =============================================================================
# QUERY EXECUTION
# =============================================================================

if question:
    with st.spinner("🔍 Retrieving relevant information..."):
        # Retrieve chunks
        retrieved = hybrid_retrieve(
            query=question,
            chunks=chunks,
            faiss_index=faiss_index,
            bm25_index=bm25_index,
            embedder=embedder
        )
        
        # Log retrieval
        log_retrieval(question, retrieved, prompt_choice)
        
        if not retrieved:
            st.warning("⚠️ No relevant information found in the policy documents.")
            logging.warning(f"No results for query: {question}")
        else:
            # Show retrieved chunks (monitoring)
            with st.expander("🔍 Retrieved Chunks (Monitoring)", expanded=False):
                for i, r in enumerate(retrieved, 1):
                    st.markdown(f"""
**[{i}] Document:** `{r['source']}`  
**Page:** `{r['page']}` | **Chunk ID:** `{r['chunk_id']}` | **Score:** `{r['score']}` | **Length:** `{r['char_count']}` chars

---
{r['text']}
---
""")
            
            # Build context from retrieved chunks
            context = "\n\n".join([
                f"[Source: {r['source']}]\n{r['text']}"
                for r in retrieved
            ])
            
            # Select prompt
            prompt_template = PROMPT_V1 if "V1" in prompt_choice else PROMPT_V2
            prompt = prompt_template.format(context=context, question=question)
            
            # Call LLM
            with st.spinner("🤖 Generating answer..."):
                raw_answer = call_llm(prompt)
            
            # Display answer
            st.subheader("💡 Answer")
            
            # Try JSON parsing for V2
            if "V2" in prompt_choice:
                try:
                    # Clean response (remove markdown backticks if present)
                    clean_answer = raw_answer.strip()
                    if clean_answer.startswith("```json"):
                        clean_answer = clean_answer.split("```json")[1].split("```")[0].strip()
                    elif clean_answer.startswith("```"):
                        clean_answer = clean_answer.split("```")[1].split("```")[0].strip()
                    
                    parsed = json.loads(clean_answer)
                    
                    # Display nicely
                    st.markdown(f"**Answer:** {parsed.get('answer', 'N/A')}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"📄 **Source:** {parsed.get('source_document', 'N/A')}")
                    with col2:
                        confidence = parsed.get('confidence', 'N/A')
                        if confidence == "High":
                            st.success(f"✅ **Confidence:** {confidence}")
                        elif confidence == "Medium":
                            st.warning(f"⚠️ **Confidence:** {confidence}")
                        else:
                            st.error(f"❌ **Confidence:** {confidence}")
                    
                    if 'reasoning' in parsed:
                        with st.expander("🧠 Reasoning"):
                            st.write(parsed['reasoning'])
                    
                    # Show raw JSON
                    with st.expander("📋 Raw JSON Response"):
                        st.json(parsed)
                    
                except json.JSONDecodeError:
                    st.warning("⚠️ Response is not valid JSON. Showing raw response:")
                    st.write(raw_answer)
                except Exception as e:
                    st.error(f"Error parsing response: {e}")
                    st.write(raw_answer)
            else:
                # V1 - just show text
                st.write(raw_answer)
            
            # Show prompt used
            with st.expander("📝 Prompt Used", expanded=False):
                st.code(prompt, language="text")

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.caption("📊 Check `rag_trace.log` for detailed retrieval logs | Built with Streamlit + FAISS + BM25 + Groq")