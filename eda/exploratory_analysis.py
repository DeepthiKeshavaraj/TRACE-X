import os
import pandas as pd
import numpy as np

PROCESSED_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'data',
    'processed',
    'classification_processed.csv'
)

def get_eda_summary(file_path=PROCESSED_FILE_PATH):
    """
    Generate exploratory data analysis summary statistics and distribution data.
    """
    if not os.path.exists(file_path):
        return {
            'exists': False,
            'message': 'Processed classification dataset not found. Please run preprocessing first.'
        }

    df = pd.read_csv(file_path)
    if df.empty:
        return {
            'exists': False,
            'message': 'Processed dataset is empty.'
        }

    total_records = len(df)
    cols = list(df.columns)
    
    # Category Distribution
    cat_counts = df['category'].value_counts().to_dict()
    cat_percentages = {cat: round((cnt / total_records) * 100, 2) for cat, cnt in cat_counts.items()}

    # Text length stats
    word_counts = df['word_count'].tolist()
    char_counts = df['char_count'].tolist()

    word_stats = {
        'min': int(np.min(word_counts)),
        'max': int(np.max(word_counts)),
        'mean': float(round(np.mean(word_counts), 2)),
        'median': float(round(np.median(word_counts), 2)),
        'std': float(round(np.std(word_counts), 2))
    }

    char_stats = {
        'min': int(np.min(char_counts)),
        'max': int(np.max(char_counts)),
        'mean': float(round(np.mean(char_counts), 2)),
        'median': float(round(np.median(char_counts), 2)),
        'std': float(round(np.std(char_counts), 2))
    }

    # Generate histogram bins for text lengths (word counts)
    counts, bin_edges = np.histogram(word_counts, bins=6)
    histogram_bins = []
    for i in range(len(counts)):
        histogram_bins.append({
            'bin': f"{int(bin_edges[i])}-{int(bin_edges[i+1])} words",
            'count': int(counts[i])
        })

    # Sample records preview
    sample_records = df[['headline', 'category', 'word_count']].head(5).to_dict(orient='records')

    return {
        'exists': True,
        'dataset_shape': [total_records, len(cols)],
        'total_records': total_records,
        'total_categories': len(cat_counts),
        'categories': list(cat_counts.keys()),
        'category_counts': cat_counts,
        'category_percentages': cat_percentages,
        'word_stats': word_stats,
        'char_stats': char_stats,
        'histogram_bins': histogram_bins,
        'sample_records': sample_records
    }

if __name__ == '__main__':
    res = get_eda_summary()
    print("EDA Result:", res)
