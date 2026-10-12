import os
import joblib
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROCESSED_FILE_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'classification_processed.csv')
MODELS_DIR = os.path.join(BASE_DIR, 'classification', 'models')
RESULTS_DIR = os.path.join(BASE_DIR, 'classification', 'results')

BEST_MODEL_PATH = os.path.join(MODELS_DIR, 'classification_model.pkl')
VECTORIZER_PATH = os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl')
RESULTS_CSV_PATH = os.path.join(RESULTS_DIR, 'classification_results.csv')

def train_and_evaluate_models(processed_path=PROCESSED_FILE_PATH):
    """
    Train 3 classifiers (Multinomial NB, Logistic Regression, Linear SVM) using TF-IDF features.
    Saves the best model, vectorizer, and evaluation results.
    """
    if not os.path.exists(processed_path):
        return {
            'success': False,
            'message': 'Processed dataset not found. Please run preprocessing first.'
        }

    df = pd.read_csv(processed_path)
    if df.empty or 'text' not in df.columns or 'category' not in df.columns:
        return {
            'success': False,
            'message': 'Processed dataset is invalid or missing required columns.'
        }

    X = df['text'].astype(str)
    y = df['category'].astype(str)
    labels = sorted(list(y.unique()))

    # Stratified Train/Test Split (80% Train, 20% Test)
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # TF-IDF Vectorization
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True,
        min_df=1,
        max_df=0.95
    )

    X_train_tfidf = vectorizer.fit_transform(X_train_raw)
    X_test_tfidf = vectorizer.transform(X_test_raw)

    models = {
        'Multinomial Naive Bayes': MultinomialNB(alpha=0.1),
        'Logistic Regression': LogisticRegression(C=1.0, max_iter=1000, random_state=42),
        'Linear Support Vector Machine': LinearSVC(C=1.0, random_state=42)
    }

    results = {}
    comparison_rows = []
    best_f1 = -1.0
    best_model_name = None
    best_model_obj = None

    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    for name, model in models.items():
        # Fit model
        model.fit(X_train_tfidf, y_train)
        y_pred = model.predict(X_test_tfidf)

        # Calculate metrics
        acc = accuracy_score(y_test, y_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted', zero_division=0)
        
        # Classification report dict
        report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred, labels=labels).tolist()

        # Save individual model
        model_filename = f"model_{name.lower().replace(' ', '_')}.pkl"
        model_filepath = os.path.join(MODELS_DIR, model_filename)
        joblib.dump(model, model_filepath)

        metrics_data = {
            'accuracy': float(round(acc * 100, 2)),
            'precision': float(round(prec * 100, 2)),
            'recall': float(round(rec * 100, 2)),
            'f1_score': float(round(f1 * 100, 2)),
            'classification_report': report_dict,
            'confusion_matrix': cm,
            'labels': labels
        }

        results[name] = metrics_data

        comparison_rows.append({
            'Model': name,
            'Accuracy': float(round(acc * 100, 2)),
            'Precision': float(round(prec * 100, 2)),
            'Recall': float(round(rec * 100, 2)),
            'F1 Score': float(round(f1 * 100, 2))
        })

        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model_obj = model

    # Save vectorizer and best model
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(best_model_obj, BEST_MODEL_PATH)

    # Save summary results to CSV
    res_df = pd.DataFrame(comparison_rows)
    res_df.to_csv(RESULTS_CSV_PATH, index=False)

    return {
        'success': True,
        'train_records': len(X_train_raw),
        'test_records': len(X_test_raw),
        'categories_count': len(labels),
        'best_model_name': best_model_name,
        'best_accuracy': float(round(results[best_model_name]['accuracy'], 2)),
        'best_f1_score': float(round(results[best_model_name]['f1_score'], 2)),
        'comparison': comparison_rows,
        'details': results,
        'labels': labels
    }

def load_prediction_model(model_name=None):
    """
    Load vectorizer and model for custom predictions.
    """
    if not os.path.exists(VECTORIZER_PATH):
        return None, None, "Vectorizer not found. Please train models first."

    vectorizer = joblib.load(VECTORIZER_PATH)

    if model_name:
        target_filename = f"model_{model_name.lower().replace(' ', '_')}.pkl"
        target_path = os.path.join(MODELS_DIR, target_filename)
        if os.path.exists(target_path):
            model = joblib.load(target_path)
            return vectorizer, model, model_name

    if os.path.exists(BEST_MODEL_PATH):
        model = joblib.load(BEST_MODEL_PATH)
        return vectorizer, model, "Best Model (Saved)"

    return None, None, "No trained model available."

def predict_custom_text(text, model_name=None):
    """
    Predict category and confidence score for custom text.
    """
    vectorizer, model, active_model_name = load_prediction_model(model_name)
    if not model or not vectorizer:
        return {
            'success': False,
            'message': active_model_name or "Model not loaded."
        }

    cleaned_text = str(text).lower().strip()
    if not cleaned_text:
        return {
            'success': False,
            'message': 'Input text cannot be empty.'
        }

    vec = vectorizer.transform([cleaned_text])
    predicted_cat = model.predict(vec)[0]

    probabilities = {}
    confidence = None
    has_proba = False

    if hasattr(model, "predict_proba"):
        has_proba = True
        probs = model.predict_proba(vec)[0]
        classes = model.classes_
        for cls, prob in zip(classes, probs):
            probabilities[cls] = float(round(prob * 100, 2))
        confidence = probabilities.get(predicted_cat, 0.0)
    elif hasattr(model, "decision_function"):
        scores = model.decision_function(vec)[0]
        classes = model.classes_
        # Apply softmax to decision function for display probabilities
        exp_scores = np.exp(scores - np.max(scores))
        probs = exp_scores / exp_scores.sum()
        for cls, prob in zip(classes, probs):
            probabilities[cls] = float(round(prob * 100, 2))
        confidence = probabilities.get(predicted_cat, 0.0)
        has_proba = True

    return {
        'success': True,
        'predicted_category': str(predicted_cat),
        'confidence': confidence,
        'has_probabilities': has_proba,
        'probabilities': probabilities,
        'model_used': active_model_name
    }

def get_saved_model_metrics():
    """
    Load saved evaluation results from CSV if present.
    """
    if os.path.exists(RESULTS_CSV_PATH):
        try:
            df = pd.read_csv(RESULTS_CSV_PATH)
            return df.to_dict(orient='records')
        except Exception:
            return []
    return []

if __name__ == '__main__':
    res = train_and_evaluate_models()
    print("Training Result:", res['best_model_name'], "Acc:", res['best_accuracy'])
