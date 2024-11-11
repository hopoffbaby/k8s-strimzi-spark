import pandas as pd
import numpy as np
import re
import os
import logging
import argparse
import time
from scipy import stats

# 1. Utility Function for Human-Readable Sizes
def sizeof_fmt(num, suffix='B'):
    """
    Convert a size in bytes to a human-readable format.

    Args:
        num (int): Size in bytes.
        suffix (str): Suffix to append (default is 'B' for bytes).

    Returns:
        str: Human-readable size string.
    """
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Y{suffix}"

# 2. Configure Logging
logging.basicConfig(
    filename='analysis_log.txt',
    filemode='w',  # Overwrite the log file each run ('a' to append)
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 3. Parse Command-Line Arguments
def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Analyze file system data.')
    parser.add_argument('--file', type=str, default='race2024.csv', help='Path to the CSV file.')
    parser.add_argument('--current_date', type=str, default='2024-11-07', help='Current date in YYYY-MM-DD format.')
    parser.add_argument('--hot_threshold', type=int, default=30, help='Days threshold for hot data.')
    parser.add_argument('--cold_threshold', type=int, default=180, help='Days threshold for cold data.')
    parser.add_argument('--max_depth', type=int, default=None, help='Maximum directory depth to analyze.')
    args = parser.parse_args()
    return args

# 4. Load Data
def load_data(file_path):
    """
    Load the data using optimized methods.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded DataFrame.
    """
    parquet_file = file_path.replace('.csv', '.parquet')
    if os.path.exists(parquet_file):
        try:
            df = pd.read_parquet(parquet_file)
            logging.info("Parquet file loaded successfully.")
            return df
        except Exception as e:
            logging.error(f"Error loading Parquet file: {e}")
            logging.info("Attempting to load CSV file instead.")
    
    # If Parquet loading fails or file doesn't exist, load CSV
    dtype = {
        'path': 'string',
        'access_time': 'string',
        'modify_time': 'string',
        'change_time': 'string',
        'size': 'int64',
        'file_type': 'string'
    }
    try:
        df = pd.read_csv(
            file_path,
            dtype=dtype,
            engine='pyarrow',
            usecols=['path', 'access_time', 'modify_time', 'size']
        )
        logging.info("CSV file loaded successfully using PyArrow.")
        # Save as Parquet for future use
        df.to_parquet(parquet_file)
        logging.info("Data saved as Parquet for future use.")
    except Exception as e:
        logging.error(f"Error loading CSV file: {e}")
        exit(1)
    return df

# 5. Data Cleaning and Feature Engineering
def clean_and_engineer(df, current_date_str, max_depth):
    """
    Clean the DataFrame and perform feature engineering with optimizations.

    Args:
        df (pd.DataFrame): The original DataFrame.
        current_date_str (str): Current date as a string.
        max_depth (int or None): Maximum directory depth to analyze.

    Returns:
        pd.DataFrame: Cleaned and feature-engineered DataFrame.
        int: Actual maximum directory depth in the data.
    """
    start_time = time.time()
    section_start_time = time.time()

    # Parse dates
    date_columns = ['access_time', 'modify_time']
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # Drop rows with missing 'path' or 'access_time'
    initial_shape = df.shape
    df = df.dropna(subset=['path', 'access_time'])
    logging.info(f"Dropped {initial_shape[0] - df.shape[0]} records with missing 'path' or 'access_time'.")

    # Normalize path separators to '/'
    df['path'] = df['path'].str.replace('\\', '/', regex=False)

    # Calculate days since last access
    current_date = pd.to_datetime(current_date_str)
    df['days_since_access'] = (current_date - df['access_time']).dt.days

    # Identify and log files with future 'access_time'
    future_dates = df[df['access_time'] > current_date]
    future_dates_count = future_dates.shape[0]
    if future_dates_count > 0:
        logging.warning(f"Found {future_dates_count} records with 'access_time' in the future.")
        logging.warning("Listing files with future 'access_time':")
        for _, row in future_dates.iterrows():
            logging.warning(f"File: {row['path']}, Access Time: {row['access_time']}")

    # Exclude records with future 'access_time'
    df = df[df['access_time'] <= current_date]
    logging.info(f"Excluded {future_dates_count} records with future 'access_time'.")

    # Extract directory from path
    df['directory'] = df['path'].str.rsplit('/', n=1).str[0]

    # Pre-compile regex for extension extraction
    ext_pattern = re.compile(r'\.([^.\/]+)$')
    df['extension'] = df['path'].str.extract(ext_pattern, expand=False).str.lower()

    # Calculate gap between creation (modify_time) and last access
    df['creation_access_gap'] = (df['access_time'] - df['modify_time']).dt.days

    # Compute depth of each path
    df['depth'] = df['path'].str.count('/') + 1

    # Determine the actual maximum directory depth
    actual_max_depth = df['depth'].max() if max_depth is None else min(df['depth'].max(), max_depth)
    logging.info(f"Determined maximum directory depth: {actual_max_depth}")

    # Split the path into parts
    df['path_parts'] = df['path'].str.split('/')

    # Optimize directory depth columns
    max_depth = min(actual_max_depth, df['path_parts'].str.len().max())
    path_parts_list = df['path_parts'].tolist()

    # Pre-allocate lists for new columns
    dir_depth_cols = {f'dir_depth_{depth}': [] for depth in range(1, max_depth + 1)}
    leaf_dirs = []
    last_two_leaf_dirs = []

    # For consistent folder structure analysis
    df['mountpoint'] = df['path_parts'].str[1]
    df['season'] = df['path_parts'].str[2]
    df['event'] = df['path_parts'].str[3]

    for parts in path_parts_list:
        # Create directory depth columns
        for depth in range(1, max_depth + 1):
            col_name = f'dir_depth_{depth}'
            if len(parts) >= depth:
                dir_depth_cols[col_name].append('/'.join(parts[:depth]))
            else:
                dir_depth_cols[col_name].append('/'.join(parts))

        # Extract leaf directory name
        leaf_dirs.append(parts[-2] if len(parts) >= 2 else '')

        # Extract last two leaf directories
        if len(parts) >= 3:
            last_two_leaf_dirs.append('/'.join(parts[-3:-1]))
        elif len(parts) >= 2:
            last_two_leaf_dirs.append(parts[-2])
        else:
            last_two_leaf_dirs.append('')

    # Assign new columns to DataFrame
    for col_name, col_data in dir_depth_cols.items():
        df[col_name] = col_data
        logging.info(f"Created column: {col_name}")

    df['leaf_dir'] = leaf_dirs
    logging.info("Created column: leaf_dir")

    df['last_two_leaf_dirs'] = last_two_leaf_dirs
    logging.info("Created column: last_two_leaf_dirs")

    # Identify low cardinality columns
    categorical_cols = ['extension', 'leaf_dir', 'last_two_leaf_dirs', 'mountpoint', 'season', 'event']
    low_cardinality_cols = [col for col in categorical_cols if df[col].nunique() < 1000]
    logging.info(f"Identified {len(low_cardinality_cols)} low cardinality columns for category conversion.")

    # Convert only low cardinality columns to 'category'
    for col in low_cardinality_cols:
        df[col] = df[col].astype('category')
        logging.info(f"Converted column to category: {col}")

    # Drop 'path_parts' column
    df = df.drop(columns=['path_parts'])

    section_end_time = time.time()
    df.processing_time = section_end_time - section_start_time
    logging.info(f"Data cleaning and feature engineering completed in {df.processing_time:.2f} seconds.")

    return df, actual_max_depth

# 6. Analyze Data
def analyze_data(df, args, actual_max_depth):
    """
    Perform analysis on the data.

    Args:
        df (pd.DataFrame): The feature-engineered DataFrame.
        args (argparse.Namespace): Parsed command-line arguments.
        actual_max_depth (int): Actual maximum directory depth in the data.

    Returns:
        dict: Dictionary containing processing times for each section.
    """
    processing_times = {}
    start_time = time.time()

    # Extract thresholds from arguments
    hot_threshold_days = args.hot_threshold
    cold_threshold_days = args.cold_threshold

    # Analyze Cold Data
    section_start_time = time.time()
    cold_data = df[df['days_since_access'] > cold_threshold_days]
    analyze_cold_data(cold_data, actual_max_depth)
    processing_times['analyze_cold_data'] = time.time() - section_start_time

    # Analyze Hot Data
    section_start_time = time.time()
    hot_data = df[df['days_since_access'] <= hot_threshold_days]
    analyze_hot_data(hot_data, actual_max_depth)
    processing_times['analyze_hot_data'] = time.time() - section_start_time

    # Analyze Especially Hot Data
    section_start_time = time.time()
    es_hot_data = analyze_es_hot_data(hot_data, actual_max_depth)
    processing_times['analyze_es_hot_data'] = time.time() - section_start_time

    # Analyze Especially Cold Data
    section_start_time = time.time()
    es_cold_data = analyze_es_cold_data(cold_data, actual_max_depth)
    processing_times['analyze_es_cold_data'] = time.time() - section_start_time

    # Additional Insights
    section_start_time = time.time()
    additional_insights(df, hot_data, cold_data, args)
    processing_times['additional_insights'] = time.time() - section_start_time

    # Analyze File Type Coldness
    section_start_time = time.time()
    analyze_file_type_coldness(df, args)
    processing_times['analyze_file_type_coldness'] = time.time() - section_start_time

    # Analyze Folder Coldness
    section_start_time = time.time()
    analyze_folder_coldness(df, args)
    processing_times['analyze_folder_coldness'] = time.time() - section_start_time

    total_time = time.time() - start_time
    processing_times['total_analysis_time'] = total_time

    return processing_times

# 7. Analyze Cold Data
def analyze_cold_data(cold_data, max_depth):
    """
    Analyze cold data and group by directory depths and leaf directories.

    Args:
        cold_data (pd.DataFrame): The cold data DataFrame.
        max_depth (int): Maximum directory depth.

    Returns:
        None
    """
    total_cold_files = cold_data.shape[0]
    total_cold_size = cold_data['size'].sum()

    logging.info(f"\nTotal Number of Cold Files: {total_cold_files}")
    logging.info(f"Total Size of Cold Data: {sizeof_fmt(total_cold_size)}")

    # Cold Data by File Extension (Include Size, Sort by Size)
    cold_by_extension = cold_data.groupby('extension', observed=True)['size'].sum().sort_values(ascending=False)
    logging.info("\nCold Data by File Extension (Sorted by Total Size):")
    for ext, size in cold_by_extension.items():
        logging.info(f"{ext}: {sizeof_fmt(size)}")

    # Cold Data by Directory Depth Based on Total Size
    logging.info("\nCold Data by Directory Depth:")
    for depth in range(1, max_depth + 1):
        depth_col = f'dir_depth_{depth}'
        unique_values = cold_data[depth_col].nunique()
        if unique_values > 1:
            cold_by_dir = cold_data.groupby(depth_col, observed=True)['size'].sum().sort_values(ascending=False).head(20)
            logging.info(f"\nTop 20 Directories at Depth {depth} with Cold Data (By Total Size):")
            for dir_path, size in cold_by_dir.items():
                logging.info(f"{dir_path}: {sizeof_fmt(size)}")
        else:
            logging.info(f"\nSkipping Depth {depth} as it has only {unique_values} unique value(s).")

    # Cold Data by Leaf Directory
    logging.info("\nCold Data by Leaf Directory (Bottom-Level Directories):")
    cold_by_leaf = cold_data.groupby('leaf_dir', observed=True)['size'].sum().sort_values(ascending=False).head(20)
    for leaf_dir, size in cold_by_leaf.items():
        logging.info(f"{leaf_dir}: {sizeof_fmt(size)}")

    # Cold Data by Last Two Leaf Directories
    logging.info("\nCold Data by Last Two Leaf Directories:")
    cold_by_last_two_leaf = cold_data.groupby('last_two_leaf_dirs', observed=True)['size'].sum().sort_values(ascending=False).head(20)
    for last_two_leaf, size in cold_by_last_two_leaf.items():
        logging.info(f"{last_two_leaf}: {sizeof_fmt(size)}")

# 8. Analyze Hot Data
def analyze_hot_data(hot_data, max_depth):
    """
    Analyze hot data and group by directory depths and leaf directories.

    Args:
        hot_data (pd.DataFrame): The hot data DataFrame.
        max_depth (int): Maximum directory depth.

    Returns:
        None
    """
    total_hot_files = hot_data.shape[0]
    total_hot_size = hot_data['size'].sum()

    logging.info(f"\nTotal Number of Hot Files: {total_hot_files}")
    logging.info(f"Total Size of Hot Data: {sizeof_fmt(total_hot_size)}")

    # Hot Data by File Extension (Include Size, Sort by Size)
    hot_by_extension = hot_data.groupby('extension', observed=True)['size'].sum().sort_values(ascending=False)
    logging.info("\nHot Data by File Extension (Sorted by Total Size):")
    for ext, size in hot_by_extension.items():
        logging.info(f"{ext}: {sizeof_fmt(size)}")

    # Hot Data by Directory Depth Based on Total Size
    logging.info("\nHot Data by Directory Depth:")
    for depth in range(1, max_depth + 1):
        depth_col = f'dir_depth_{depth}'
        unique_values = hot_data[depth_col].nunique()
        if unique_values > 1:
            hot_by_dir = hot_data.groupby(depth_col, observed=True)['size'].sum().sort_values(ascending=False).head(20)
            logging.info(f"\nTop 20 Directories at Depth {depth} with Hot Data (By Total Size):")
            for dir_path, size in hot_by_dir.items():
                logging.info(f"{dir_path}: {sizeof_fmt(size)}")
        else:
            logging.info(f"\nSkipping Depth {depth} as it has only {unique_values} unique value(s).")

    # Hot Data by Leaf Directory
    logging.info("\nHot Data by Leaf Directory (Bottom-Level Directories):")
    hot_by_leaf = hot_data.groupby('leaf_dir', observed=True)['size'].sum().sort_values(ascending=False).head(20)
    for leaf_dir, size in hot_by_leaf.items():
        logging.info(f"{leaf_dir}: {sizeof_fmt(size)}")

    # Hot Data by Last Two Leaf Directories
    logging.info("\nHot Data by Last Two Leaf Directories:")
    hot_by_last_two_leaf = hot_data.groupby('last_two_leaf_dirs', observed=True)['size'].sum().sort_values(ascending=False).head(20)
    for last_two_leaf, size in hot_by_last_two_leaf.items():
        logging.info(f"{last_two_leaf}: {sizeof_fmt(size)}")

# 9. Analyze Especially Hot Data
def analyze_es_hot_data(hot_data, max_depth):
    """
    Analyze especially hot data.

    Args:
        hot_data (pd.DataFrame): The hot data DataFrame.
        max_depth (int): Maximum directory depth.

    Returns:
        pd.DataFrame: Especially hot data subset.
    """
    gap_threshold_days = 365  # Accessed more than a year after creation
    especially_hot_data = hot_data[hot_data['creation_access_gap'] > gap_threshold_days]

    num_es_hot_files = especially_hot_data.shape[0]
    total_es_hot_size = especially_hot_data['size'].sum()

    logging.info(f"\nNumber of Especially Hot Files: {num_es_hot_files}")
    logging.info(f"Total Size of Especially Hot Data: {sizeof_fmt(total_es_hot_size)}")

    # Especially Hot Data by Directory Depth
    logging.info("\nEspecially Hot Data by Directory Depth:")
    for depth in range(1, max_depth + 1):
        depth_col = f'dir_depth_{depth}'
        unique_values = especially_hot_data[depth_col].nunique()
        if unique_values > 1:
            es_hot_by_dir = especially_hot_data.groupby(depth_col, observed=True)['size'].sum().sort_values(ascending=False).head(20)
            logging.info(f"\nTop 20 Directories at Depth {depth} with Especially Hot Data (By Total Size):")
            for dir_path, size in es_hot_by_dir.items():
                logging.info(f"{dir_path}: {sizeof_fmt(size)}")
        else:
            logging.info(f"\nSkipping Depth {depth} as it has only {unique_values} unique value(s).")

    # Especially Hot Data by Leaf Directory
    logging.info("\nEspecially Hot Data by Leaf Directory (Bottom-Level Directories):")
    es_hot_by_leaf = especially_hot_data.groupby('leaf_dir', observed=True)['size'].sum().sort_values(ascending=False).head(20)
    for leaf_dir, size in es_hot_by_leaf.items():
        logging.info(f"{leaf_dir}: {sizeof_fmt(size)}")

    # Especially Hot Data by Last Two Leaf Directories
    logging.info("\nEspecially Hot Data by Last Two Leaf Directories:")
    es_hot_by_last_two_leaf = especially_hot_data.groupby('last_two_leaf_dirs', observed=True)['size'].sum().sort_values(ascending=False).head(20)
    for last_two_leaf, size in es_hot_by_last_two_leaf.items():
        logging.info(f"{last_two_leaf}: {sizeof_fmt(size)}")

    return especially_hot_data

# 10. Analyze Especially Cold Data
def analyze_es_cold_data(cold_data, max_depth):
    """
    Analyze especially cold data.

    Args:
        cold_data (pd.DataFrame): The cold data DataFrame.
        max_depth (int): Maximum directory depth.

    Returns:
        pd.DataFrame: Especially cold data subset.
    """
    access_gap_threshold_days = 7  # Accessed within 7 days of creation
    last_access_threshold_days = 90  # Not accessed again in last 90 days

    especially_cold_data = cold_data[
        (cold_data['creation_access_gap'] <= access_gap_threshold_days) &
        (cold_data['days_since_access'] > last_access_threshold_days)
    ]

    num_es_cold_files = especially_cold_data.shape[0]
    total_es_cold_size = especially_cold_data['size'].sum()

    logging.info(f"\nNumber of Especially Cold Files: {num_es_cold_files}")
    logging.info(f"Total Size of Especially Cold Data: {sizeof_fmt(total_es_cold_size)}")

    # Especially Cold Data by Directory Depth
    logging.info("\nEspecially Cold Data by Directory Depth:")
    for depth in range(1, max_depth + 1):
        depth_col = f'dir_depth_{depth}'
        unique_values = especially_cold_data[depth_col].nunique()
        if unique_values > 1:
            es_cold_by_dir = especially_cold_data.groupby(depth_col, observed=True)['size'].sum().sort_values(ascending=False).head(20)
            logging.info(f"\nTop 20 Directories at Depth {depth} with Especially Cold Data (By Total Size):")
            for dir_path, size in es_cold_by_dir.items():
                logging.info(f"{dir_path}: {sizeof_fmt(size)}")
        else:
            logging.info(f"\nSkipping Depth {depth} as it has only {unique_values} unique value(s).")

    # Especially Cold Data by Leaf Directory
    logging.info("\nEspecially Cold Data by Leaf Directory (Bottom-Level Directories):")
    es_cold_by_leaf = especially_cold_data.groupby('leaf_dir', observed=True)['size'].sum().sort_values(ascending=False).head(20)
    for leaf_dir, size in es_cold_by_leaf.items():
        logging.info(f"{leaf_dir}: {sizeof_fmt(size)}")

    # Especially Cold Data by Last Two Leaf Directories
    logging.info("\nEspecially Cold Data by Last Two Leaf Directories:")
    es_cold_by_last_two_leaf = especially_cold_data.groupby('last_two_leaf_dirs', observed=True)['size'].sum().sort_values(ascending=False).head(20)
    for last_two_leaf, size in es_cold_by_last_two_leaf.items():
        logging.info(f"{last_two_leaf}: {sizeof_fmt(size)}")

    return especially_cold_data

# 11. Analyze File Type Coldness (Feature 1)
def analyze_file_type_coldness(df, args):
    """
    For each of the top 25 file types (by total size), analyze how quickly the data becomes cold.

    Args:
        df (pd.DataFrame): The feature-engineered DataFrame.
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        None
    """
    logging.info("\nAnalyzing File Type Coldness:")
    top_extensions = df.groupby('extension')['size'].sum().sort_values(ascending=False).head(25).index.tolist()

    for ext in top_extensions:
        ext_data = df[df['extension'] == ext]
        total_size = ext_data['size'].sum()
        # Calculate percentage of data that is cold
        cold_data = ext_data[ext_data['days_since_access'] > args.cold_threshold]
        cold_size = cold_data['size'].sum()
        cold_percentage = (cold_size / total_size) * 100 if total_size > 0 else 0
        logging.info(f"Extension: {ext}")
        logging.info(f"  Total Size: {sizeof_fmt(total_size)}")
        logging.info(f"  Cold Data Size: {sizeof_fmt(cold_size)} ({cold_percentage:.2f}% of total)")
        # Analyze how quickly data becomes cold
        # Create a histogram of 'days_since_access'
        bins = [0, 30, 90, 180, 365, 730, np.inf]
        labels = ['<1m', '1-3m', '3-6m', '6-12m', '1-2y', '>2y']
        ext_data['access_age_group'] = pd.cut(ext_data['days_since_access'], bins=bins, labels=labels)
        age_distribution = ext_data.groupby('access_age_group')['size'].sum()
        logging.info(f"  Data Size by Access Age Group:")
        for age_group, size in age_distribution.items():
            logging.info(f"    {age_group}: {sizeof_fmt(size)}")

# 12. Analyze Folder Coldness (Features 4 and 5)
def analyze_folder_coldness(df, args):
    """
    Analyze how quickly data in various folders becomes cold, including consistent folder structures.

    Args:
        df (pd.DataFrame): The feature-engineered DataFrame.
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        None
    """
    logging.info("\nAnalyzing Folder Coldness:")

    # For top 20 folders by total size
    top_folders = df.groupby('dir_depth_3')['size'].sum().sort_values(ascending=False).head(20).index.tolist()
    for folder in top_folders:
        folder_data = df[df['dir_depth_3'] == folder]
        total_size = folder_data['size'].sum()
        cold_data = folder_data[folder_data['days_since_access'] > args.cold_threshold]
        cold_size = cold_data['size'].sum()
        cold_percentage = (cold_size / total_size) * 100 if total_size > 0 else 0
        logging.info(f"Folder: {folder}")
        logging.info(f"  Total Size: {sizeof_fmt(total_size)}")
        logging.info(f"  Cold Data Size: {sizeof_fmt(cold_size)} ({cold_percentage:.2f}% of total)")
        # Analyze how quickly data becomes cold
        bins = [0, 30, 90, 180, 365, 730, np.inf]
        labels = ['<1m', '1-3m', '3-6m', '6-12m', '1-2y', '>2y']
        folder_data['access_age_group'] = pd.cut(folder_data['days_since_access'], bins=bins, labels=labels)
        age_distribution = folder_data.groupby('access_age_group')['size'].sum()
        logging.info(f"  Data Size by Access Age Group:")
        for age_group, size in age_distribution.items():
            logging.info(f"    {age_group}: {sizeof_fmt(size)}")

    # Analyze consistent folder structures
    logging.info("\nAnalyzing Consistent Folder Structures:")
    consistent_folders = df.groupby(['mountpoint', 'season', 'event'])['size'].sum().sort_values(ascending=False).head(20).reset_index()
    for _, row in consistent_folders.iterrows():
        folder_data = df[
            (df['mountpoint'] == row['mountpoint']) &
            (df['season'] == row['season']) &
            (df['event'] == row['event'])
        ]
        total_size = folder_data['size'].sum()
        cold_data = folder_data[folder_data['days_since_access'] > args.cold_threshold]
        cold_size = cold_data['size'].sum()
        cold_percentage = (cold_size / total_size) * 100 if total_size > 0 else 0
        folder_path = f"/{row['mountpoint']}/{row['season']}/{row['event']}"
        logging.info(f"Folder: {folder_path}")
        logging.info(f"  Total Size: {sizeof_fmt(total_size)}")
        logging.info(f"  Cold Data Size: {sizeof_fmt(cold_size)} ({cold_percentage:.2f}% of total)")
        # Analyze how quickly data becomes cold
        bins = [0, 30, 90, 180, 365, 730, np.inf]
        labels = ['<1m', '1-3m', '3-6m', '6-12m', '1-2y', '>2y']
        folder_data['access_age_group'] = pd.cut(folder_data['days_since_access'], bins=bins, labels=labels)
        age_distribution = folder_data.groupby('access_age_group')['size'].sum()
        logging.info(f"  Data Size by Access Age Group:")
        for age_group, size in age_distribution.items():
            logging.info(f"    {age_group}: {sizeof_fmt(size)}")

# Function to interpret correlation coefficients
def interpret_correlation(var1, var2, corr_value):
    """
    Provide layman explanations for correlation coefficients.

    Args:
        var1 (str): First variable name.
        var2 (str): Second variable name.
        corr_value (float): Correlation coefficient.

    Returns:
        str: Explanation of the correlation.
    """
    if var1 == var2:
        return "(Perfect correlation with itself)"

    if corr_value > 0.5:
        return "(Strong positive correlation: as one increases, so does the other)"
    elif 0 < corr_value <= 0.5:
        return "(Moderate positive correlation: as one increases, the other tends to increase)"
    elif -0.5 <= corr_value < 0:
        return "(Moderate negative correlation: as one increases, the other tends to decrease)"
    elif corr_value < -0.5:
        return "(Strong negative correlation: as one increases, the other decreases significantly)"
    else:
        return "(Weak or no correlation)"

# 13. Additional Insights (Updated for Features 2 and 3)
def additional_insights(df, hot_data, cold_data, args):
    """
    Provide additional insights such as total size, file size statistics, top largest files, and last access distribution.

    Args:
        df (pd.DataFrame): The feature-engineered DataFrame.
        hot_data (pd.DataFrame): The hot data DataFrame.
        cold_data (pd.DataFrame): The cold data DataFrame.
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        None
    """
    # Report total size of all files
    total_size = df['size'].sum()
    logging.info(f"\nTotal Size of All Files: {sizeof_fmt(total_size)}")

    # a. File Size Statistics
    size_stats = df['size'].describe()
    median_size = df['size'].median()
    mode_size = df['size'].mode()[0] if not df['size'].mode().empty else np.nan
    geom_mean_size = stats.gmean(df['size'][df['size'] > 0]) if (df['size'] > 0).any() else np.nan
    harmonic_mean_size = stats.hmean(df['size'][df['size'] > 0]) if (df['size'] > 0).any() else np.nan

    logging.info("\nFile Size Statistics:")
    logging.info(f"Count: {int(size_stats['count'])}")
    logging.info(f"Mean: {sizeof_fmt(size_stats['mean'])}")
    logging.info(f"Median: {sizeof_fmt(median_size)}")
    logging.info(f"Mode: {sizeof_fmt(mode_size)}")
    logging.info(f"Standard Deviation: {sizeof_fmt(size_stats['std'])}")
    logging.info(f"Minimum: {sizeof_fmt(size_stats['min'])}")
    logging.info(f"25th Percentile: {sizeof_fmt(size_stats['25%'])}")
    logging.info(f"75th Percentile: {sizeof_fmt(size_stats['75%'])}")
    logging.info(f"Maximum: {sizeof_fmt(size_stats['max'])}")
    if not np.isnan(geom_mean_size):
        logging.info(f"Geometric Mean: {sizeof_fmt(geom_mean_size)}")
    if not np.isnan(harmonic_mean_size):
        logging.info(f"Harmonic Mean: {sizeof_fmt(harmonic_mean_size)}")

    # b. Top 20 Largest Files (Overall)
    top_largest_overall = df.nlargest(20, 'size')[['path', 'size']]
    logging.info("\nTop 20 Largest Files (Overall):")
    for _, row in top_largest_overall.iterrows():
        logging.info(f"{row['path']}: {sizeof_fmt(row['size'])}")

    # c. Top 20 Largest Hot Files
    top_largest_hot = hot_data.nlargest(20, 'size')[['path', 'size']]
    logging.info("\nTop 20 Largest Hot Files:")
    for _, row in top_largest_hot.iterrows():
        logging.info(f"{row['path']}: {sizeof_fmt(row['size'])}")

    # d. Top 20 Largest Cold Files
    top_largest_cold = cold_data.nlargest(20, 'size')[['path', 'size']]
    logging.info("\nTop 20 Largest Cold Files:")
    for _, row in top_largest_cold.iterrows():
        logging.info(f"{row['path']}: {sizeof_fmt(row['size'])}")

    # e. File Modifications Over Time
    df['modify_year_month'] = df['modify_time'].dt.to_period('M')
    modifications_over_time = df['modify_year_month'].value_counts().sort_index()
    logging.info("\nFile Modifications Over Time:")
    for period, count in modifications_over_time.items():
        logging.info(f"{period}: {count}")

    # f. File Extension Size Contribution (Overall)
    size_by_extension = df.groupby('extension', observed=True)['size'].sum().sort_values(ascending=False)
    logging.info("\nTotal Size by File Extension (Overall):")
    for ext, size in size_by_extension.items():
        logging.info(f"{ext}: {sizeof_fmt(size)}")

    # g. Correlation Matrix with Explanations
    correlation = df[['size', 'days_since_access']].corr()
    logging.info("\nCorrelation Matrix:")
    for row in correlation.index:
        for col in correlation.columns:
            corr_value = correlation.loc[row, col]
            explanation = interpret_correlation(row, col, corr_value)
            logging.info(f"{row} vs {col}: {corr_value:.4f} {explanation}")

    # h. Data Accessed Over Time (Feature 2)
    logging.info("\nData Accessed Over Time:")
    current_date = pd.to_datetime(args.current_date)
    df['months_since_access'] = (current_date.year - df['access_time'].dt.year) * 12 + (current_date.month - df['access_time'].dt.month)

    for months_ago in range(1, 25):
        data_accessed = df[df['months_since_access'] <= months_ago]
        total_size = data_accessed['size'].sum()
        logging.info(f"Data accessed in last {months_ago} month(s): {sizeof_fmt(total_size)}")

    # i. Indication of How Quickly Total Data Becomes Cold (Feature 3)
    logging.info("\nIndication of How Quickly Total Data Becomes Cold:")
    total_size = df['size'].sum()
    for days in [30, 90, 180, 365, 730]:
        cold_data = df[df['days_since_access'] > days]
        cold_size = cold_data['size'].sum()
        cold_percentage = (cold_size / total_size) * 100 if total_size > 0 else 0
        logging.info(f"Data not accessed in last {days} day(s): {sizeof_fmt(cold_size)} ({cold_percentage:.2f}% of total)")

# 14. Main Function
def main():
    total_start_time = time.time()

    # Parse arguments
    args = parse_arguments()

    # Log input parameters
    logging.info("Input Parameters:")
    logging.info(f"CSV File Path: {args.file}")
    logging.info(f"Current Date: {args.current_date}")
    logging.info(f"Hot Threshold (days): {args.hot_threshold}")
    logging.info(f"Cold Threshold (days): {args.cold_threshold}")
    logging.info(f"Maximum Directory Depth: {args.max_depth}")

    # Load Data
    load_start_time = time.time()
    df = load_data(args.file)
    load_end_time = time.time()
    load_time = load_end_time - load_start_time

    # Clean and Engineer Features
    df, actual_max_depth = clean_and_engineer(df, args.current_date, args.max_depth)
    clean_engineer_time = df.processing_time

    # Analyze Data
    processing_times = analyze_data(df, args, actual_max_depth)

    total_end_time = time.time()
    total_processing_time = total_end_time - total_start_time

    # Log processing times
    logging.info("\nProcessing Time Summary:")
    logging.info(f"Data Loading Time: {load_time:.2f} seconds")
    logging.info(f"Data Cleaning and Feature Engineering Time: {clean_engineer_time:.2f} seconds")
    for section, time_taken in processing_times.items():
        logging.info(f"{section.replace('_', ' ').title()}: {time_taken:.2f} seconds")
    logging.info(f"Total Processing Time: {total_processing_time:.2f} seconds")

if __name__ == "__main__":
    main()
