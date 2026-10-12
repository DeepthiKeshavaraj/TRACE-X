# TRACE-X — Question Answering System (QA) Module

## 📌 Module Overview
The **Question Answering System (QA)** is the 5th core NLP module implemented in **TRACE-X** (Temporal Relationship & Evidence Correlation Intelligence System).

It accepts unstructured investigation evidence text alongside natural language questions, extracts the exact answer span, and highlights the supporting evidence passage.

---

## 🎯 Why QA is Useful in TRACE-X
In forensic and intelligence investigations, analysts review extensive textual evidence (interview transcripts, incident logs, surveillance notes). The QA system accelerates evidence processing by instantly retrieving factual answers (names, locations, timestamps, organizations) with supporting context passages, avoiding manual document searching.

---

## 🧠 Approach & Algorithm Architecture
- **Answering Approach**: Extractive Evidence Retrieval & Entity Span Alignment (spaCy / TF-IDF Vectorization).
- **Pipeline Workflow**:
  1. **Context Preprocessing**: Normalizes text and segments context into clean sentences using spaCy sentence tokenization while preserving entities.
  2. **Question Analysis**: Identifies question intent type (`LOCATION`, `DATE_TIME`, `PERSON`, `ORGANIZATION`, `QUANTITY`) and extracts keywords.
  3. **Sentence Retrieval**: Ranks context sentences using sublinear TF-IDF vectorization, Cosine Similarity, and keyword overlap scoring.
  4. **Answer Span Extraction**: Aligns extracted target entity spans from the supporting sentence matching the question type (e.g. `Chennai` for `LOCATION`, `12 March 2026` for `DATE_TIME`).
  5. **Confidence Scoring**: Computes a dynamic relevance confidence percentage based on sentence similarity and entity category alignment.
  6. **Honest Unknown Handling**: Returns *"The answer could not be found in the supplied evidence."* if no relevant context sentence exceeds the similarity threshold.

---

## 🧪 Evaluation Framework
- **Evaluation Script**: `qa/qa_evaluation.py`
- **Output Report**: `data/outputs/qa/qa_evaluation_report.json`
- **Metrics Evaluated**:
  - **Exact Match (EM)**: 100% normalized string match with ground truth.
  - **Token F1-Score**: Token-level harmonic mean of precision and recall.
- **Empirical Test Results**:
  - Exact Match Score: `100.0%`
  - Mean Token F1 Score: `100.0%`

---

## ⚡ How to Run Tests
To run unit tests for the QA engine:
```bash
python3 -m unittest qa/tests/test_qa_engine.py
```

To run the evaluation suite:
```bash
python3 -m qa.qa_evaluation
```

---

## ⚠️ Current Limitations & Planned Features
- **Current Capability**: Extractive QA over user-provided text context (up to 500,000 characters).
- **Planned Features**: Multi-document retrieval over vector databases (Retrieval-Augmented Generation / RAG) planned for future modules (Knowledge Graph & Retrieval).
