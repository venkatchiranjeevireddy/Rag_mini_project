"""
Evaluation Module for Policy RAG Assistant

This script evaluates the RAG system using a predefined set of questions
covering different scenarios: answerable, partially answerable, and unanswerable.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict
import pandas as pd

from app import (
    setup_rag_pipeline,
    hybrid_retrieve,
    call_llm,
    PROMPT_V1,
    PROMPT_V2
)

# =============================================================================
# EVALUATION QUESTION SET
# =============================================================================

EVALUATION_QUESTIONS = [
    {
        "id": 1,
        "question": "Within how many hours can a customer cancel an order after placing it?",
        "category": "factual",
        "expected_type": "answerable",
        "notes": "Directly stated in the order cancellation policy"
    },
    {
        "id": 2,
        "question": "How many days does a customer have to request a refund after receiving a product?",
        "category": "factual",
        "expected_type": "answerable",
        "notes": "Clearly mentioned in the refund eligibility section"
    },
    {
        "id": 3,
        "question": "Are digital or downloadable products eligible for a refund?",
        "category": "policy",
        "expected_type": "answerable",
        "notes": "Listed under non-refundable items"
    },
    {
        "id": 4,
        "question": "If an order is cancelled within the allowed time, how long does it take to receive the refund?",
        "category": "factual",
        "expected_type": "answerable",
        "notes": "Refund timeline mentioned for cancelled orders"
    },
    {
        "id": 5,
        "question": "Can a customer get a partial refund for an unused portion of a subscription?",
        "category": "policy",
        "expected_type": "answerable",
        "notes": "Covered under subscription cancellation rules"
    },
    {
        "id": 6,
        "question": "What conditions must a product meet to be eligible for a refund?",
        "category": "factual",
        "expected_type": "answerable",
        "notes": "Product condition requirements listed in refund eligibility"
    },
    {
        "id": 7,
        "question": "What happens if a customer cancels an order after it has already been shipped?",
        "category": "edge_case",
        "expected_type": "partially_answerable",
        "notes": "Policy states cancellation may not be possible but does not detail outcomes"
    },
    {
        "id": 8,
        "question": "Who is responsible for paying customs duties on international shipments?",
        "category": "shipping",
        "expected_type": "answerable",
        "notes": "International shipping section specifies responsibility"
    },
    {
        "id": 9,
        "question": "Does the warranty cover damage caused by accidental drops?",
        "category": "warranty",
        "expected_type": "answerable",
        "notes": "Explicitly excluded under warranty exclusions"
    },
    {
        "id": 10,
        "question": "How long is the warranty period from the date of purchase?",
        "category": "warranty",
        "expected_type": "answerable",
        "notes": "Warranty duration is clearly stated"
    },
    {
        "id": 11,
        "question": "Will original shipping charges be refunded when a product is returned?",
        "category": "policy",
        "expected_type": "answerable",
        "notes": "Shipping cost refund rules mentioned in refund process"
    },
    {
        "id": 12,
        "question": "What action should a customer take to initiate a warranty claim?",
        "category": "procedure",
        "expected_type": "answerable",
        "notes": "Warranty claims process explained in shipping & warranty policy"
    },
    {
        "id": 13,
        "question": "Is same-day delivery available for all domestic orders?",
        "category": "out_of_scope",
        "expected_type": "unanswerable",
        "notes": "No mention of same-day delivery in shipping policy"
    },
    {
        "id": 14,
        "question": "Can a customer receive a refund without providing proof of purchase?",
        "category": "edge_case",
        "expected_type": "answerable",
        "notes": "Refund policy explicitly requires proof of purchase"
    }
]

# =============================================================================
# EVALUATION RUBRIC
# =============================================================================

RUBRIC = """
EVALUATION RUBRIC:
-----------------

✅ PASS (3 points):
- Answer is accurate and grounded in retrieved context
- No hallucinations or external knowledge
- Appropriate confidence level
- Correctly handles missing information

⚠️ PARTIAL (2 points):
- Answer mostly correct but includes minor issues
- May have slight hallucinations or assumptions
- Confidence level not well-calibrated

❌ FAIL (1 point):
- Answer contains significant hallucinations
- Uses outside knowledge not in documents
- Fails to refuse when information is missing
- Incorrect or misleading information
"""

# =============================================================================
# EVALUATION FUNCTION
# =============================================================================

def evaluate_rag_system():
    """
    Run comprehensive evaluation of the RAG system.
    Tests both prompt versions against the evaluation question set.
    """
    
    print("="*80)
    print("POLICY RAG SYSTEM EVALUATION")
    print("="*80)
    print(RUBRIC)
    print("\n")
    
    # Initialize pipeline
    print("Initializing RAG pipeline...")
    chunks, faiss_index, bm25_index, embedder = setup_rag_pipeline()
    
    if chunks is None:
        print("❌ Failed to initialize pipeline. Check if policy documents exist.")
        return
    
    print(f"✅ Pipeline ready with {len(chunks)} chunks\n")
    
    results = []
    
    # Evaluate both prompt versions
    for prompt_version in ["V1", "V2"]:
        print(f"\n{'='*80}")
        print(f"EVALUATING PROMPT {prompt_version}")
        print(f"{'='*80}\n")
        
        prompt_template = PROMPT_V1 if prompt_version == "V1" else PROMPT_V2
        
        for item in EVALUATION_QUESTIONS:
            print(f"\n[Question {item['id']}] {item['question']}")
            print(f"Category: {item['category']} | Expected: {item['expected_type']}")
            print("-" * 80)
            
            # Retrieve
            retrieved = hybrid_retrieve(
                query=item['question'],
                chunks=chunks,
                faiss_index=faiss_index,
                bm25_index=bm25_index,
                embedder=embedder
            )
            
            # Build context
            context = "\n\n".join([
                f"[Source: {r['source']}]\n{r['text']}"
                for r in retrieved
            ])
            
            # Generate answer
            prompt = prompt_template.format(
                context=context,
                question=item['question']
            )
            answer = call_llm(prompt)
            
            # Display
            print(f"\n🤖 Answer ({prompt_version}):")
            if prompt_version == "V2":
                try:
                    clean_answer = answer.strip()
                    if clean_answer.startswith("```json"):
                        clean_answer = clean_answer.split("```json")[1].split("```")[0].strip()
                    elif clean_answer.startswith("```"):
                        clean_answer = clean_answer.split("```")[1].split("```")[0].strip()
                    
                    parsed = json.loads(clean_answer)
                    print(json.dumps(parsed, indent=2))
                except:
                    print(answer)
            else:
                print(answer)
            
            print(f"\n📊 Retrieved {len(retrieved)} chunks:")
            for r in retrieved[:3]:  # Show top 3
                print(f"  - {r['source']} (score: {r['score']})")
            
            # Manual scoring prompt
            print(f"\n📝 MANUAL EVALUATION NEEDED:")
            print(f"Score this answer: ✅ (3 pts) | ⚠️ (2 pts) | ❌ (1 pt)")
            score = input("Enter score: ").strip()
            
            # Record result
            results.append({
                "prompt_version": prompt_version,
                "question_id": item['id'],
                "question": item['question'],
                "category": item['category'],
                "expected_type": item['expected_type'],
                "answer": answer[:200] + "..." if len(answer) > 200 else answer,
                "num_chunks": len(retrieved),
                "score": score,
                "timestamp": datetime.now().isoformat()
            })
    
    # =============================================================================
    # SAVE RESULTS
    # =============================================================================
    
    # Save to JSON
    output_file = f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    
    # Create summary
    df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    print(df.groupby(['prompt_version', 'score']).size().unstack(fill_value=0))
    
    # Save CSV
    csv_file = f"evaluation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(csv_file, index=False)
    print(f"\n✅ Summary saved to: {csv_file}")
    
    return results

# =============================================================================
# AUTOMATED EVALUATION (BONUS)
# =============================================================================

def auto_evaluate_hallucination(answer: str, context: str) -> Dict:
    """
    Simple automated hallucination detection.
    
    Checks if answer contains information not present in context.
    This is a basic heuristic - not perfect but useful for quick checks.
    """
    # Check for common hallucination indicators
    hallucination_keywords = [
        "i think", "probably", "might be", "generally", "usually",
        "in my experience", "typically", "most companies"
    ]
    
    answer_lower = answer.lower()
    
    # Check for keywords
    has_uncertainty = any(keyword in answer_lower for keyword in hallucination_keywords)
    
    # Check if key terms in answer appear in context
    # (Very basic - just checking word overlap)
    answer_words = set(answer_lower.split())
    context_words = set(context.lower().split())
    overlap = len(answer_words & context_words) / len(answer_words) if answer_words else 0
    
    return {
        "has_uncertainty_markers": has_uncertainty,
        "word_overlap_ratio": round(overlap, 2),
        "likely_grounded": overlap > 0.3 and not has_uncertainty
    }

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    evaluate_rag_system()