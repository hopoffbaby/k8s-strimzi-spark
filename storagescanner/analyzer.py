import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
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
    Load the CSV data with appropriate data types and parse dates.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded DataFrame.
    """
    dtype = {
        'path': 'string',
        'access_time': 'string',
        'modify_time': 'string',
        'change_time': 'string',
        'size': 'int64'
    }
    parse_dates = ['access_time', 'modify_time', 'change_time']

    try:
        df = pd.read_csv(file_path, dtype=dtype, parse_dates=parse_dates)
        logging.info("CSV file loaded successfully.")
        return df
    except FileNotFoundError:
        logging.error(f"'{file_path}' file not found. Please check the file path.")
        exit(1)

# 5. Data Cleaning and Feature Engineering
def clean_and_engineer(df, current_date_str, max_depth):
    """
    Clean the DataFrame and perform feature engineering.

    Args:
        df (pd.DataFrame): The original DataFrame.
        current_date_str (str): Current date as a string.
        max_depth (int or None): Maximum directory depth to analyze. If None, determine dynamically.

    Returns:
        pd.DataFrame: Cleaned and feature-engineered DataFrame.
        int: Actual maximum directory depth in the data.
    """
    start_time = time.time()

    # Drop rows with missing 'path' or 'access_time'
    initial_rows = df.shape[0]
    df = df.dropna(subset=['path', 'access_time'])
    dropped_rows = initial_rows - df.shape[0]
    logging.info(f"Dropped {dropped_rows} rows due to missing 'path' or 'access_time'.")

    # Normalize path separators to '/'
    df['path'] = df['path'].str.replace('\\', '/', regex=False)

    # Calculate days since last access
    current_date = pd.to_datetime(current_date_str)
    df['days_since_access'] = (current_date - df['access_time']).dt.days

    # Extract directory from path using pathlib
    df['directory'] = df['path'].apply(lambda x: str(Path(x).parent))

    # Extract file extension and lowercase it
    df['extension'] = df['path'].str.extract(r'\.([^.]+)$')[0].str.lower()

    # Calculate gap between creation (modify_time) and last access
    df['creation_access_gap'] = (df['access_time'] - df['modify_time']).dt.days

    # Extract the path object and compute depth
    df['path_obj'] = df['path'].apply(lambda x: Path(x))
    df['depth'] = df['path_obj'].apply(lambda p: len(p.parts))

    # Determine the actual maximum directory depth
    actual_max_depth = df['depth'].max() if max_depth is None else min(df['depth'].max(), max_depth)

    # Function to extract directory at a specific depth
    def get_directory_depth(path_obj, depth):
        try:
            return str(Path(*path_obj.parts[:depth]))
        except IndexError:
            return str(path_obj)

    # Create directory depth columns
    for depth in range(1, actual_max_depth + 1):
        col_name = f'dir_depth_{depth}'
        df[col_name] = df['path_obj'].apply(lambda p: get_directory_depth(p, depth))
        logging.info(f"Created column: {col_name}")

    # Extract leaf directory name (the last directory in the path)
    df['leaf_dir'] = df['path_obj'].apply(lambda p: p.parent.name)
    logging.info("Created column: leaf_dir")

    # **Corrected**: Extract last two leaf directories by referencing the parent directory
    df['last_two_leaf_dirs'] = df['path_obj'].apply(
        lambda p: '/'.join(p.parent.parts[-2:]) if len(p.parent.parts) >= 2 else p.parent.parts[-1]
    )
    logging.info("Created column: last_two_leaf_dirs")

    # Convert 'extension', 'directory', 'leaf_dir', and 'last_two_leaf_dirs' to category to save memory
    df['extension'] = df['extension'].astype('category')
    df['directory'] = df['directory'].astype('category')
    df['leaf_dir'] = df['leaf_dir'].astype('category')
    df['last_two_leaf_dirs'] = df['last_two_leaf_dirs'].astype('category')

    # Drop the 'path_obj' column as it's no longer needed
    df = df.drop(columns=['path_obj'])

    end_time = time.time()
    logging.info(f"Data cleaning and feature engineering completed in {end_time - start_time:.2f} seconds.")

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
        None
    """
    # Extract thresholds from arguments
    hot_threshold_days = args.hot_threshold
    cold_threshold_days = args.cold_threshold

    # Analyze Cold Data
    cold_data = df[df['days_since_access'] > cold_threshold_days]
    analyze_cold_data(cold_data, actual_max_depth)

    # Analyze Hot Data
    hot_data = df[df['days_since_access'] <= hot_threshold_days]
    analyze_hot_data(hot_data, actual_max_depth)

    # Analyze Especially Hot Data
    es_hot_data = analyze_es_hot_data(hot_data, actual_max_depth)

    # Analyze Especially Cold Data
    es_cold_data = analyze_es_cold_data(cold_data, actual_max_depth)

    # Additional Insights
    additional_insights(df, hot_data, cold_data)

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

# 11. Additional Insights
def additional_insights(df, hot_data, cold_data):
    """
    Provide additional insights such as total size, file size statistics, top largest files, and last access distribution.

    Args:
        df (pd.DataFrame): The feature-engineered DataFrame.
        hot_data (pd.DataFrame): The hot data DataFrame.
        cold_data (pd.DataFrame): The cold data DataFrame.

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

    # h. Distribution of Last Access Time Bucketed into Months (up to 24 months)
    logging.info("\nDistribution of Last Access Time Bucketed into Months (Up to 24 Months):")
    for month in range(1, 25):
        days = month * 30  # Approximate days in a month
        accessed_in_period = df[df['days_since_access'] <= days]
        total_size_in_period = accessed_in_period['size'].sum()
        logging.info(f"Accessed in last {month} month(s): {sizeof_fmt(total_size_in_period)}")

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

# 12. Main Function
def main():
    # Parse arguments
    args = parse_arguments()

    # Load Data
    df = load_data(args.file)

    # Clean and Engineer Features
    df, actual_max_depth = clean_and_engineer(df, args.current_date, args.max_depth)

    # Analyze Data
    analyze_data(df, args, actual_max_depth)

if __name__ == "__main__":
    main()
