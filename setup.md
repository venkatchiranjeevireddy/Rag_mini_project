# 🚀 Setup Guide - Policy RAG Assistant

This guide will walk you through setting up and running the Policy RAG Assistant from scratch.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- OpenAI API key
- Groq API key
- Terminal/Command Prompt access

---

## Step-by-Step Setup

### 1. Clone or Download the Project

If using Git:
```bash
git clone <your-repository-url>
cd policy-rag-assistant
```

Or download and extract the ZIP file, then navigate to the folder.

---

### 2. Create Virtual Environment (Recommended)

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Streamlit (UI framework)
- LangChain (RAG framework)
- FAISS (vector search)
- Groq SDK (LLM)
- BM25 (keyword search)
- And other dependencies

**Installation time:** ~2-3 minutes

---

### 4. Set Up API Keys

#### Option A: Using .env file (Recommended)

1. Copy the template:
```bash
cp .env.template .env
```

2. Edit `.env` and add your API keys:
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

3. Install python-dotenv (if not already installed):
```bash
pip install python-dotenv
```

4. Add to top of `app.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

#### Option B: Export environment variables

**On macOS/Linux:**
```bash
export OPENAI_API_KEY="your-openai-key"
export GROQ_API_KEY="your-groq-key"
```

**On Windows (Command Prompt):**
```bash
set OPENAI_API_KEY=your-openai-key
set GROQ_API_KEY=your-groq-key
```

**On Windows (PowerShell):**
```bash
$env:OPENAI_API_KEY="your-openai-key"
$env:GROQ_API_KEY="your-groq-key"
```

#### Getting API Keys

**OpenAI:**
1. Go to https://platform.openai.com/api-keys
2. Create account or sign in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

**Groq:**
1. Go to https://console.groq.com/keys
2. Sign up or log in
3. Click "Create API Key"
4. Copy the key (starts with `gsk_`)

---

### 5. Add Policy Documents

Create the `policies` folder:
```bash
mkdir policies
```

Add your policy documents to this folder. Supported formats:
- PDF files (`.pdf`)
- Text files (`.txt`)

**For testing, you can use the sample policies provided:**
```bash
# Copy sample policies
cp sample_policies/*.txt policies/
```

**Sample policies included:**
- `refund_policy.txt`
- `cancellation_policy.txt`
- `shipping_warranty_policy.txt`

---

### 6. Run the Application

```bash
streamlit run app.py
```

The app should automatically open in your browser at:
```
http://localhost:8501
```

If it doesn't open automatically, copy that URL into your browser.

---

## Verification Checklist

Before running, verify:

- [ ] Virtual environment is activated (see `(venv)` in terminal)
- [ ] All packages installed successfully
- [ ] API keys are set (test with `echo $OPENAI_API_KEY` on macOS/Linux)
- [ ] `policies/` folder exists
- [ ] At least one policy document in `policies/` folder
- [ ] No firewall blocking localhost:8501

---

## Common Issues & Solutions

### Issue: "Module not found"

**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

### Issue: "API key not found"

**Solution:**
Check that environment variables are set:
```bash
# On macOS/Linux
echo $OPENAI_API_KEY
echo $GROQ_API_KEY

# On Windows (Command Prompt)
echo %OPENAI_API_KEY%
echo %GROQ_API_KEY%
```

If empty, re-export the variables or check your `.env` file.

### Issue: "No policy documents found"

**Solution:**
```bash
# Verify policies folder exists
ls policies/

# If empty, copy sample policies
cp sample_policies/*.txt policies/
```

### Issue: "Rate limit exceeded"

**Solution:**
- You've hit API rate limits
- Wait a few minutes
- Upgrade your API plan if needed
- For OpenAI, check: https://platform.openai.com/account/limits

### Issue: "FAISS installation fails"

**Solution:**
Try installing manually:
```bash
pip install faiss-cpu --no-cache-dir
```

On Mac M1/M2:
```bash
conda install -c pytorch faiss-cpu
```

### Issue: Port 8501 already in use

**Solution:**
Run on different port:
```bash
streamlit run app.py --server.port 8502
```

---

## Testing the Installation

Once the app is running:

1. **Test simple question:**
   - Type: "What is the refund period for electronics?"
   - Expected: Should retrieve and answer from policy

2. **Test unanswerable question:**
   - Type: "Do you offer delivery to Mars?"
   - Expected: Should say information not in documents

3. **Check logging:**
   - Check that `rag_trace.log` is created
   - Should contain retrieval traces

4. **Test both prompts:**
   - Try same question with V1 and V2
   - Compare outputs

---

## Running Evaluation

To run the evaluation script:

```bash
python evaluate.py
```

This will:
1. Run 8 test questions through both prompts
2. Display retrieved chunks and answers
3. Prompt you for manual scores
4. Save results to JSON and CSV

---

## Project Structure After Setup

```
policy-rag-assistant/
├── venv/                          # Virtual environment (created)
├── policies/                      # Your policies (created)
│   ├── refund_policy.txt
│   ├── cancellation_policy.txt
│   └── shipping_warranty_policy.txt
├── sample_policies/               # Sample files
├── app.py                         # Main application
├── evaluate.py                    # Evaluation script
├── requirements.txt               # Dependencies
├── README.md                      # Documentation
├── SETUP.md                       # This file
├── .env                          # Your API keys (created)
├── .env.template                 # Template
└── rag_trace.log                 # Generated logs (after running)
```

---

## Next Steps

After successful setup:

1. **Customize policies:** Replace sample policies with your actual documents

2. **Run evaluation:** `python evaluate.py` to establish baseline

3. **Tune parameters:** Experiment with chunk sizes in `app.py`:
   ```python
   CHUNK_SIZE = 500      # Try 400, 600
   CHUNK_OVERLAP = 100   # Try 50, 150
   HYBRID_ALPHA = 0.7    # Try 0.5, 0.8
   ```

4. **Improve prompts:** Modify `PROMPT_V2` for your specific use case

5. **Monitor logs:** Check `rag_trace.log` to debug retrieval

---

## Development Mode

For development with auto-reload:

```bash
streamlit run app.py --server.runOnSave true
```

Changes to `app.py` will automatically reload the app.

---

## Deployment (Optional)

To deploy to Streamlit Cloud:

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect your repository
4. Add secrets (API keys) in Streamlit settings
5. Deploy

---

## Getting Help

If you're stuck:

1. **Check logs:** `rag_trace.log`
2. **Verify API keys:** Test with a simple API call
3. **Check dependencies:** `pip list | grep streamlit`
4. **Review errors:** Read full error messages carefully
5. **GitHub Issues:** Open an issue if you found a bug

---

## Success Indicators

You've successfully set up when:

- ✅ App runs without errors
- ✅ Policy documents loaded (shown in UI)
- ✅ Can ask questions and get answers
- ✅ Logs are being written
- ✅ Both prompt versions work
- ✅ Retrieved chunks display correctly

---

**Setup time:** ~10-15 minutes

**Happy RAGing! 🚀**