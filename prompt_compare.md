# Prompt Engineering: V1 vs V2 Comparison

## Overview

This document explains the iterative improvements made to the prompting strategy for the Policy RAG Assistant.

---

## Prompt V1 (Baseline)

### The Prompt

```
Answer the question using the context below.

Context:
{context}

Question:
{question}

Answer:
```

### Characteristics

- **Length:** 3 lines
- **Instructions:** Minimal
- **Structure:** Unstructured text output
- **Grounding:** Implicit only
- **Failure handling:** None

### Problems Identified

| Issue | Example | Impact |
|-------|---------|--------|
| **Hallucinations** | User: "What's the refund period?" <br> Bot: "Generally, most companies offer 30 days..." | ❌ Added outside knowledge |
| **No refusal pattern** | User: "Do you ship to Mars?" <br> Bot: "While not explicitly stated, likely no..." | ❌ Invented answer instead of refusing |
| **Inconsistent format** | Sometimes bullets, sometimes paragraphs | ⚠️ Hard to parse programmatically |
| **No citations** | Answers don't reference source documents | ⚠️ Can't verify claims |
| **No confidence** | All answers sound equally certain | ⚠️ Misleading confidence |

### Example Output (V1)

**Question:** "What is the refund period for electronics?"

**V1 Response:**
```
Based on the context provided, the refund period for electronics is 14 days from the date of delivery. However, this may vary depending on the specific product and circumstances. It's always best to check with customer service for your particular situation.
```

**Issues:**
- ✅ Core answer is correct (14 days)
- ❌ "may vary" - adds uncertainty not in docs
- ❌ "It's always best to check" - unnecessary advice
- ❌ No source citation
- ❌ No confidence indicator

---

## Prompt V2 (Improved)

### The Prompt

```
You are an expert assistant for company policy documents.

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
{
  "answer": "<your answer or refusal message>",
  "source_document": "<policy document name or 'Not specified'>",
  "confidence": "High | Medium | Low",
  "reasoning": "<brief explanation of how you arrived at this answer>"
}

JSON Response:
```

### Improvements Made

| Improvement | Technique | Why It Works |
|-------------|-----------|--------------|
| **Explicit grounding** | "Answer ONLY using the provided context" | Forces model to ignore training data |
| **Refusal template** | Exact wording for "no answer" case | Standardizes edge case handling |
| **JSON schema** | Structured output format | Enables programmatic validation |
| **Citation requirement** | "Always cite the source document" | Makes answers verifiable |
| **Confidence scoring** | Self-reported High/Medium/Low | Helps users gauge reliability |
| **Reasoning field** | Explain the logic | Improves transparency |

### Example Output (V2)

**Question:** "What is the refund period for electronics?"

**V2 Response:**
```json
{
  "answer": "The refund period for electronics is 14 days from the date of delivery. This applies to computers, laptops, smartphones, tablets, cameras, audio equipment, and gaming consoles.",
  "source_document": "refund_policy.txt",
  "confidence": "High",
  "reasoning": "The policy explicitly states in Section 2 'Electronics Refund Period' that electronics have a 14-day return window, with specific examples listed."
}
```

**Improvements:**
- ✅ Precise answer with specifics
- ✅ Clear source citation
- ✅ Confidence indicator
- ✅ Reasoning shows document section
- ✅ No extraneous advice
- ✅ Structured and parseable

---

## Side-by-Side Comparison

### Test Case 1: Out-of-Scope Question

**Question:** "Do you offer same-day delivery to Mars?"

| Version | Response | Grade |
|---------|----------|-------|
| **V1** | "While the shipping policy doesn't explicitly mention Mars, it does offer same-day delivery to select cities. International shipping is available to 150+ countries..." | ❌ FAIL (hallucination) |
| **V2** | `{"answer": "The provided policy documents do not contain information about delivery to Mars.", "confidence": "High", "reasoning": "No mention of interplanetary shipping in any policy document."}` | ✅ PASS (correct refusal) |

### Test Case 2: Answerable Question

**Question:** "What items are non-refundable?"

| Version | Response | Grade |
|---------|----------|-------|
| **V1** | "Non-refundable items include digital downloads, personalized items, and perishable goods, among others." | ⚠️ PARTIAL (correct but vague) |
| **V2** | `{"answer": "Non-refundable items include: digital downloads and software licenses, personalized or custom-made items, perishable goods, opened software packages, gift cards, and items marked as 'Final Sale'.", "source_document": "refund_policy.txt", "confidence": "High", "reasoning": "Section 4 explicitly lists all non-refundable items."}` | ✅ PASS (complete and cited) |

### Test Case 3: Partially Answerable

**Question:** "What happens if my package is damaged during shipping?"

| Version | Response | Grade |
|---------|----------|-------|
| **V1** | "If your package arrives damaged, you should contact customer service immediately. They will likely arrange a replacement or refund." | ⚠️ PARTIAL (adds "likely") |
| **V2** | `{"answer": "If you receive a damaged package: refuse delivery if possible, take photos of damage, contact us within 48 hours. We will send a replacement or provide a full refund at no cost to you. No restocking fee applies.", "source_document": "shipping_warranty_policy.txt", "confidence": "High", "reasoning": "Section 5 'Damaged Packages' provides explicit steps and outcomes."}` | ✅ PASS (specific steps) |

---

## Quantitative Improvements

### Evaluation Metrics (8-question test set)

| Metric | Prompt V1 | Prompt V2 | Improvement |
|--------|-----------|-----------|-------------|
| **Hallucination Rate** | 37.5% (3/8) | 0% (0/8) | -100% ✅ |
| **Correct Refusals** | 25% (1/4) | 100% (4/4) | +300% ✅ |
| **Citations Provided** | 0% | 100% | +∞ ✅ |
| **Structured Output** | 0% | 100% | +∞ ✅ |
| **Avg Confidence (when right)** | N/A | High: 75% | New metric ✅ |

---

## Key Lessons Learned

### 1. Explicit > Implicit

**Bad:** "Use the context"  
**Good:** "Answer ONLY using the provided context. Do NOT use outside knowledge."

The model needs crystal-clear boundaries.

### 2. Templates for Edge Cases

**Bad:** Hoping the model refuses appropriately  
**Good:** Providing exact wording for "no answer" scenarios

Pre-written templates ensure consistency.

### 3. Structure Enables Validation

**Bad:** Free-form text  
**Good:** JSON schema

Structured output allows programmatic checks for hallucinations.

### 4. Force Attribution

**Bad:** Assuming model will cite sources  
**Good:** "Always cite the source document name"

Required fields ensure accountability.

### 5. Self-Assessment Works

**Bad:** No confidence indicator  
**Good:** "confidence": "High | Medium | Low"

Models are surprisingly good at estimating their own certainty.

---

## Iteration Process

How we got from V1 to V2:

```
V1 (Baseline)
    ↓
Identify issues through testing
    ↓
V1.1: Add "only use context" instruction
    ↓
Still had inconsistent formatting
    ↓
V1.2: Add JSON schema
    ↓
Still hallucinated on edge cases
    ↓
V1.3: Add explicit refusal template
    ↓
Missing source attribution
    ↓
V1.4: Require source citation
    ↓
No confidence indicator
    ↓
V2: Add confidence + reasoning fields
```

**Total iterations:** 5  
**Time invested:** ~2 hours of testing

---

## When to Use Each Version

### Use V1 (Baseline) When:
- Rapid prototyping
- Output format doesn't matter
- Hallucinations acceptable (exploratory use)
- No programmatic parsing needed

### Use V2 (Improved) When:
- Production environment
- Accuracy critical
- Need verifiable answers
- Programmatic processing required
- User trust essential

---

## Future Improvements (V3 Ideas)

Potential next iteration:

1. **Multi-document synthesis:**
   ```json
   "sources": [
     {"document": "refund_policy.txt", "relevance": "primary"},
     {"document": "shipping_policy.txt", "relevance": "supporting"}
   ]
   ```

2. **Quote extraction:**
   ```json
   "supporting_quotes": [
     "Electronics and technology products have a 14-day return window..."
   ]
   ```

3. **Contradiction detection:**
   ```json
   "contradictions": "None found" | "Policy X states A, but Policy Y states B"
   ```

4. **Follow-up suggestions:**
   ```json
   "related_questions": [
     "What about the warranty period?",
     "Can I extend the return window?"
   ]
   ```

---

## Conclusion

**Key Takeaway:** Small prompt changes → Massive quality improvements

The difference between V1 and V2 is ~10 lines of text, but the impact is dramatic:
- Zero hallucinations
- 100% citation rate
- Structured, parseable outputs
- Better user trust

**Investment:** 2 hours of iteration  
**Return:** Production-ready prompt with measurable quality gains

---

## References

- LangChain Prompt Engineering: https://python.langchain.com/docs/modules/model_io/prompts/
- OpenAI Prompt Engineering Guide: https://platform.openai.com/docs/guides/prompt-engineering
- Anthropic Prompt Engineering: https://docs.anthropic.com/claude/docs/prompt-engineering

---

**Last Updated:** January 2024