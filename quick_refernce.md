# 📋 Quick Reference Card

## Essential Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="sk-..."
export GROQ_API_KEY="gsk_..."

# Run application
streamlit run app.py

# Run evaluation
python evaluate.py
```

### File Operations
```bash
# Create policies folder
mkdir policies

# Copy sample policies
cp sample_policies/*.txt policies/

# Check logs
tail -f rag_trace.log

# Clear cache
rm -rf .streamlit/cache
```

---

## Key Configuration Parameters

### In `app.py`

```python
# Chunking Configuration
CHUNK_SIZE = 500          # Characters per chunk (100-150 tokens)
CHUNK_OVERLAP = 100       # Character overlap between chunks

# Retrieval Configuration  
TOP_K = 8                 # Candidate chunks to retrieve
RERANK_K = 3              # Final chunks to send to LLM
HYBRID_ALPHA = 0.7        # Semantic weight (0.7 = 70% semantic, 30% keyword)

# Paths
POLICY_DIR = "policies"   # Policy documents folder
```

### Tuning Guide

| Parameter | Lower → Higher | Use Case |
|-----------|----------------|----------|
| `CHUNK_SIZE` | 300 → 800 | Smaller for FAQs, Larger for articles |
| `CHUNK_OVERLAP` | 50 → 200 | Less for speed, More for accuracy |
| `TOP_K` | 3 → 15 | Fewer for speed, More for coverage |
| `RERANK_K` | 2 → 5 | Fewer for speed, More for context |
| `HYBRID_ALPHA` | 0.5 → 0.9 | 0.5 balanced, 0.9 more semantic |

---

## Common Queries & Expected Behavior

### ✅ Should Work Well

| Query | Expected Answer | Source |
|-------|----------------|---------|
| "What is the refund period?" | "30-day general, 14-day electronics..." | refund_policy.txt |
| "Can I cancel anytime?" | "Yes, monthly subscriptions..." | cancellation_policy.txt |
| "How long is shipping?" | "5-7 business days standard..." | shipping_warranty_policy.txt |
| "What items are non-refundable?" | Lists specific items | refund_policy.txt |

### ❌ Should Refuse Gracefully

| Query | Expected Response |
|-------|-------------------|
| "Do you ship to Mars?" | "Documents do not contain information about Mars delivery" |
| "What's your AI policy?" | "No information found" (if not in docs) |
| "How's the weather?" | "Outside scope of policy documents" |

---

## Troubleshooting Quick Fixes

### App Won't Start

```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check port availability
lsof -i :8501  # macOS/Linux
netstat -ano | findstr :8501  # Windows
```

### No Results Retrieved

```bash
# Verify policies folder
ls -la policies/

# Check if documents loaded
# Look for "Pipeline ready: X documents → Y chunks" in UI

# Verify API keys
echo $OPENAI_API_KEY
```

### API Errors

```bash
# Test OpenAI key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test Groq key
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"
```

### Slow Performance

```python
# In app.py, reduce these:
TOP_K = 5           # Instead of 8
RERANK_K = 2        # Instead of 3
CHUNK_SIZE = 400    # Instead of 500
```

---

## Prompt Templates Quick Reference

### Prompt V1 (Baseline)
- Use for: Quick prototyping, informal testing
- Pros: Simple, fast to write
- Cons: Hallucinations, no structure

### Prompt V2 (Production)
- Use for: Real applications, evaluations
- Pros: Grounded, structured, cited
- Cons: Slightly longer responses

---

## Evaluation Questions

```python
# Quick test set (copy-paste ready)
test_questions = [
    "What is the refund period for electronics?",
    "Can I cancel my subscription mid-month?",
    "What happens if my package is damaged?",
    "Do you offer same-day delivery to Mars?",
    "What items are non-refundable?",
    "How long does standard shipping take?",
    "What is your policy on returns for opened software?",
    "Do you provide warranties for third-party products?"
]
```

---

## File Structure Quick View

```
policy-rag-assistant/
├── 📄 app.py                   # Main app - START HERE
├── 📄 evaluate.py              # Evaluation script
├── 📄 requirements.txt         # Dependencies
├── 📄 README.md               # Full documentation
├── 📄 SETUP.md                # Setup guide
├── 📄 PROMPT_COMPARISON.md    # Prompt analysis
├── 📁 policies/               # PUT YOUR POLICIES HERE
├── 📁 sample_policies/        # Example policies
├── 📁 venv/                   # Virtual environment
└── 📄 rag_trace.log           # Runtime logs
```

---

## API Cost Estimates

### Per Query (Approximate)

| Component | Model | Cost | Notes |
|-----------|-------|------|-------|
| Embeddings | Ada-002 | $0.0001 | Query + 3 chunks |
| LLM | Llama3-8B (Groq) | Free | Up to rate limits |

**Daily estimate (100 queries):** ~$0.01

---

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| **Chunk Creation** | ~0.5s for 100 chunks |
| **Index Building** | ~2s for 100 chunks |
| **Query Time** | ~1-2s (hybrid retrieval + LLM) |
| **Memory Usage** | ~200MB for 100 chunks |

---

## Keyboard Shortcuts (Streamlit)

| Shortcut | Action |
|----------|--------|
| `R` | Rerun app |
| `C` | Clear cache |
| `?` | Show keyboard shortcuts |
| `Ctrl+C` | Stop server (terminal) |

---

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-proj-...
GROQ_API_KEY=gsk_...

# Optional
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
POLICY_DIR=policies         # Custom policy folder path
```

---

## Logging Levels

```python
# In app.py, change logging level:
logging.basicConfig(
    filename="rag_trace.log",
    level=logging.INFO,      # Change to DEBUG for verbose logs
    format="%(asctime)s - %(levelname)s - %(message)s"
)
```

| Level | Use When |
|-------|----------|
| `DEBUG` | Debugging retrieval issues |
| `INFO` | Normal operation (default) |
| `WARNING` | Production, only issues |
| `ERROR` | Only critical failures |

---

## Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `openai.error.AuthenticationError` | Invalid API key | Check OPENAI_API_KEY |
| `ModuleNotFoundError: No module named 'faiss'` | Missing dependency | `pip install faiss-cpu` |
| `No policy documents found` | Empty policies folder | Add PDFs/TXTs to policies/ |
| `JSONDecodeError` | Invalid JSON from LLM | Check prompt, may need retry |

---

## Testing Checklist

Before submitting/deploying:

- [ ] App runs without errors
- [ ] Both prompts (V1, V2) work
- [ ] Logs are being written
- [ ] Evaluation script runs
- [ ] Sample questions answered correctly
- [ ] Edge cases handled (Mars question)
- [ ] README is complete
- [ ] API keys are NOT in code

---

## Quick Links

- **Streamlit Docs:** https://docs.streamlit.io
- **LangChain Docs:** https://python.langchain.com
- **FAISS GitHub:** https://github.com/facebookresearch/faiss
- **Groq Docs:** https://console.groq.com/docs
- **OpenAI Embeddings:** https://platform.openai.com/docs/guides/embeddings

---

## One-Liner Commands

```bash
# Full setup from scratch
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && mkdir policies && cp sample_policies/*.txt policies/

# Quick test
python -c "import faiss, streamlit, langchain; print('All imports OK')"

# Count chunks
grep "Created.*chunks" rag_trace.log | tail -1

# View last query
tail -20 rag_trace.log | grep "QUERY"

# Clean restart
rm -rf venv/ rag_trace.log .streamlit/ && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

---

**Pro Tip:** Bookmark this page for quick reference! 📌

**Last Updated:** February 2024