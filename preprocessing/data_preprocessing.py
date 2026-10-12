import os
import re
import pandas as pd

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw', 'classification')
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed')
PROCESSED_FILE_PATH = os.path.join(PROCESSED_DATA_DIR, 'classification_processed.csv')

EXPECTED_FILES = [
    'business_data.csv',
    'education_data.csv',
    'entertainment_data.csv',
    'sports_data.csv',
    'technology_data.csv'
]

def check_raw_files_status(raw_dir=RAW_DATA_DIR):
    """
    Check availability and record stats for each raw CSV file.
    """
    status_list = []
    total_records = 0
    categories = set()
    found_count = 0

    for file_name in EXPECTED_FILES:
        file_path = os.path.join(raw_dir, file_name)
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                num_records = len(df)
                num_cols = len(df.columns)
                if 'category' in df.columns:
                    categories.update(df['category'].dropna().unique())
                status_list.append({
                    'file': file_name,
                    'status': 'Found',
                    'records': num_records,
                    'columns': num_cols
                })
                total_records += num_records
                found_count += 1
            except Exception as e:
                status_list.append({
                    'file': file_name,
                    'status': f'Error: {str(e)}',
                    'records': 0,
                    'columns': 0
                })
        else:
            status_list.append({
                'file': file_name,
                'status': 'Missing',
                'records': 0,
                'columns': 0
            })

    return {
        'files': status_list,
        'all_found': found_count == len(EXPECTED_FILES),
        'found_count': found_count,
        'total_expected': len(EXPECTED_FILES),
        'total_raw_records': total_records,
        'categories_found': sorted(list(categories)),
        'total_categories': len(categories)
    }

def validate_raw_datasets(raw_dir=RAW_DATA_DIR):
    """
    Perform deep validation on raw datasets without modifying them.
    """
    check_res = check_raw_files_status(raw_dir)
    if not check_res['all_found'] and check_res['found_count'] == 0:
        return {
            'error': 'Classification dataset not found. Please place the required CSV files in data/raw/classification/.',
            'valid': False
        }

    dfs = []
    for file_info in check_res['files']:
        if file_info['status'] == 'Found':
            fpath = os.path.join(raw_dir, file_info['file'])
            dfs.append(pd.read_csv(fpath))

    if not dfs:
        return {
            'error': 'No readable dataset files available.',
            'valid': False
        }

    combined_df = pd.concat(dfs, ignore_index=True)
    input_shape = combined_df.shape
    
    # Calculate validation metrics
    missing_count = combined_df.isnull().sum().to_dict()
    total_missing = combined_df.isnull().sum().sum()
    duplicate_count = combined_df.duplicated().sum()
    
    # Check invalid categories
    expected_cats = {'Business', 'Education', 'Entertainment', 'Sports', 'Technology'}
    actual_cats = set(combined_df['category'].dropna().astype(str).str.strip().str.title())
    invalid_cats = list(actual_cats - expected_cats)
    
    # Check empty text fields
    h_col = 'headlines' if 'headlines' in combined_df.columns else ('headline' if 'headline' in combined_df.columns else None)
    h_vals = combined_df[h_col].fillna('') if h_col else ""
    d_vals = combined_df['description'].fillna('') if 'description' in combined_df.columns else ""
    c_vals = combined_df['content'].fillna('') if 'content' in combined_df.columns else ""
    combined_text = h_vals + " " + d_vals + " " + c_vals
    empty_text_records = (combined_text.str.strip() == '').sum()

    return {
        'valid': True,
        'total_records': len(combined_df),
        'dataset_shape': [input_shape[0], input_shape[1]],
        'missing_values_by_column': missing_count,
        'total_missing_values': int(total_missing),
        'duplicate_records': int(duplicate_count),
        'invalid_categories': invalid_cats,
        'empty_text_records': int(empty_text_records),
        'categories': sorted(list(actual_cats))
    }

def clean_text(text):
    """
    Convert text to lowercase and normalize whitespace.
    """
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def run_preprocessing_pipeline(raw_dir=RAW_DATA_DIR, output_path=PROCESSED_FILE_PATH):
    """
    Execute ETL Pipeline:
    1. Extract: Load 5 CSVs
    2. Transform: Combine text, handle missing values, deduplicate, normalize whitespace
    3. Load: Save to classification_processed.csv
    """
    status = check_raw_files_status(raw_dir)
    if status['found_count'] == 0:
        return {
            'success': False,
            'message': 'Classification dataset not found. Please place the required CSV files in data/raw/classification/.'
        }

    dfs = []
    for file_info in status['files']:
        if file_info['status'] == 'Found':
            fpath = os.path.join(raw_dir, file_info['file'])
            df = pd.read_csv(fpath)
            dfs.append(df)

    raw_df = pd.concat(dfs, ignore_index=True)
    input_records = len(raw_df)

    # Missing & duplicate counts before cleaning
    missing_before = int(raw_df.isnull().sum().sum())
    duplicates_before = int(raw_df.duplicated().sum())

    # Combine text fields: headline/headlines, description, content
    headline_col = 'headlines' if 'headlines' in raw_df.columns else ('headline' if 'headline' in raw_df.columns else None)
    headline = raw_df[headline_col].fillna('') if headline_col else ""
    description = raw_df['description'].fillna('') if 'description' in raw_df.columns else ""
    content = raw_df['content'].fillna('') if 'content' in raw_df.columns else ""

    # Clean individual parts then combine
    raw_df['text'] = (headline + ". " + description + ". " + content).apply(clean_text)
    raw_df['category'] = raw_df['category'].astype(str).str.strip().str.title()

    # Filter out empty text or invalid categories
    clean_df = raw_df[raw_df['text'].str.strip() != ''].copy()
    
    # Remove duplicate text records
    clean_df = clean_df.drop_duplicates(subset=['text', 'category']).reset_index(drop=True)
    
    # Select final columns: text, category, word_count, char_count
    clean_df['word_count'] = clean_df['text'].apply(lambda t: len(t.split()))
    clean_df['char_count'] = clean_df['text'].apply(len)
    clean_df['headline'] = headline if isinstance(headline, pd.Series) else clean_df['text'].str[:50]
    
    final_df = clean_df[['headline', 'description', 'content', 'text', 'category', 'word_count', 'char_count']]

    output_records = len(final_df)
    removed_records = input_records - output_records

    # Save to processed directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)

    return {
        'success': True,
        'message': 'Preprocessing completed successfully.',
        'metrics': {
            'input_records': input_records,
            'output_records': output_records,
            'removed_records': removed_records,
            'missing_values': missing_before,
            'duplicate_records': duplicates_before,
            'output_path': output_path,
            'categories': sorted(final_df['category'].unique().tolist()),
            'category_counts': final_df['category'].value_counts().to_dict()
        }
    }

if __name__ == '__main__':
    res = run_preprocessing_pipeline()
    print("ETL Result:", res)
