# TRACE-X — Temporal Relationship & Evidence Correlation Intelligence System

**Multi-Module Intelligence Analysis Platform**

---

## 📌 Project Overview
TRACE-X is an investigation intelligence application designed to process unstructured textual and speech evidence (news articles, incident reports, emails, messages, interview transcripts, and audio recordings) into structured intelligence for analysis.

---

## 🚀 Implemented NLP Concepts

### 1. Text Classification
- **Supervised ML Classifiers**:
  1. **Multinomial Naive Bayes**
  2. **Logistic Regression**
  3. **Linear Support Vector Machine (Linear SVM)**
- **Feature Extraction**: TF-IDF Vectorization (`ngram_range=(1, 2)`, sublinear TF scaling, max 5,000 features).
- **Categories**: Business, Education, Entertainment, Sports, Technology.
- **Evaluation**: Accuracy, Precision, Recall, F1-Score, Confusion Matrices, and Classification Reports.

### 2. Speech Processing
- **Audio Evidence Ingestion**: Supports `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg` formats. Dual-mode support (`Choose audio file` & `Record now`).
- **Speech-to-Text**: Converts spoken audio into text transcripts using Python's `speech_recognition` engine & Web Speech API.
- **Metadata & Statistics**: File size, audio duration, processing time, sentence count, word count, character count, and normalized transcript.
- **Accuracy Evaluation (WER / CER)**: Calculates real Word Error Rate (WER) and Character Error Rate (CER) via Levenshtein edit distance when a reference transcript is provided.

### 3. Multilingual NLP
- **Language Detection & Identification**: Automatic ISO language identification using `langdetect` (supports Tamil `ta`, Hindi `hi`, French `fr`, Spanish `es`, German `de`, English `en`, and 20+ global languages).
- **Text Normalization**: Unicode whitespace normalization, token count, and character count without modifying original evidence.
- **Translation Engine**: Translates foreign evidence into a common English representation using `deep_translator` with graceful offline fallback.
- **Evidence Preservation**: Preserves original evidence alongside normalized & translated outputs (`Original Evidence + Processed Evidence`).

### 4. Named Entity Recognition (NER)
- **Objective**: Identifies and extracts critical entity categories — **PERSON**, **ORGANIZATION**, **LOCATION**, and **MISCELLANEOUS** — from investigation text evidence.
- **Dataset**: Trained and evaluated on the official **CoNLL-2003 English NER dataset** (`data/raw/ner/train.txt`, `valid.txt`, `test.txt`).
- **Tagging Scheme**: **BIO Tagging** scheme (`B-PER`, `I-PER`, `B-ORG`, `I-ORG`, `B-LOC`, `I-LOC`, `B-MISC`, `I-MISC`, `O`).
- **Sequence Labeling Model**: **Conditional Random Fields (CRF)** model (`sklearn-crfsuite`) with token surface features, POS tags, word shape casing, prefix/suffix n-grams, and surrounding context window (-1, +1).
- **Entity Extraction & Grouping**: `extract_entities(text)` maps token predictions to entity spans (`B-PER I-PER` → `John Smith` → `PERSON`).
- **Visual Entity Highlighting**: Dynamic HTML rendering with styled color badges for each entity type.
- **Evaluation**: Evaluated using `seqeval` for strict entity-level Precision, Recall, F1-score, and Support overall and per entity type.

---

## 🎓 Academic Viva & Technical Explanation

### What is Named Entity Recognition (NER)?
> "Named Entity Recognition is an NLP task that identifies and classifies named entities in text into predefined categories such as person, organization, location and miscellaneous entities. In TRACE-X, NER is used to extract important entities from investigation-related evidence so that the entities can later be connected with events, timestamps and relationships."

### Why is NER needed in TRACE-X?
Unstructured text evidence contains crucial names of individuals, suspect organizations, crime scene locations, and key entities. NER converts raw sentences into structured entity records, allowing TRACE-X to build timeline links and evidence correlation networks.

### What is the BIO Tagging Scheme?
- **B (Beginning)**: Marks the first token of a multi-word or single-word entity (e.g. `B-PER` for *"John"*).
- **I (Inside)**: Marks subsequent tokens inside the same entity (e.g. `I-PER` for *"Smith"* in *"John Smith"*).
- **O (Outside)**: Marks tokens that do not belong to any named entity (e.g. *"visited"*).

### Token-Level Prediction vs Entity-Level Evaluation
- **Token-Level Accuracy**: Evaluates whether each individual word token receives the correct tag.
- **Entity-Level Evaluation (seqeval)**: Requires the **exact match** of both boundary and category for an entire entity span (e.g., matching both *"John"* and *"Smith"* as `PERSON`). This provides a stricter, academic-grade metric.

---

## 🛠️ Technology Stack
- **Backend Framework**: Python 3.10, Flask 3.0+
- **NLP & Speech Libraries**: `scikit-learn`, `sklearn-crfsuite`, `seqeval`, `spacy`, `pandas`, `numpy`, `joblib`, `speech_recognition`, `langdetect`, `deep-translator`
- **Frontend**: HTML5, CSS3 (Custom Dark Intelligence Theme), JavaScript (Vanilla JS), Bootstrap 5, FontAwesome Icons
- **Visualization**: Chart.js

---

## 📂 Project Structure

```
TRACE-X P1/
│
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── routes.py                # Blueprint routes & REST endpoints
│   ├── templates/
│   │   ├── base.html            # Main dark layout & persistent sidebar
│   │   ├── dashboard.html       # Dynamic KPI metrics & active modules overview
│   │   ├── scope.html           # Project scope & visual pipeline diagram
│   │   ├── data.html            # Data collection, ETL preprocessing & EDA
│   │   ├── classification.html  # Text classification & custom predictor
│   │   ├── speech.html          # Speech processing & WER/CER evaluation
│   │   ├── multilingual.html    # Multilingual detection & translation
│   │   └── ner.html             # Named Entity Recognition & BIO tag viewer
│   └── static/
│       ├── css/style.css        # High-contrast dark theme styling
│       └── js/app.js            # Client JavaScript handlers & Chart.js
│
├── data/
│   ├── raw/
│   │   ├── classification/      # Raw category CSVs
│   │   └── ner/                 # CoNLL-2003 train.txt, valid.txt, test.txt
│   └── processed/               # classification_processed.csv & ner/ner_stats.json
│
├── preprocessing/               # Data preprocessing ETL script
├── eda/                         # Exploratory data analysis script
├── classification/              # Text classification training & saved models
├── speech/                      # Speech processing script, uploads & results
├── multilingual/                # Multilingual NLP script & results
├── ner/                         # NER processing, CRF model & seqeval evaluation
│   ├── ner_processing.py        # CoNLL parser, CRF trainer, extract_entities()
│   ├── ner_evaluation.py        # seqeval entity evaluation
│   ├── models/                  # crf_ner_model.pkl
│   └── results/                 # ner_metrics.json
│
├── run.py                       # Server entry point
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## ⚡ How to Run the Application

1. **Navigate to project directory**:
   ```bash
   cd "/Users/deepthi/Desktop/TRACE-X P1"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch Flask Server**:
   ```bash
   python run.py
   ```

4. **Open Web Browser**:
   Navigate to [http://127.0.0.1:5055](http://127.0.0.1:5055)
