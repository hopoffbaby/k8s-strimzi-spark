import pandas as pd
import os

# Configuration
PARQUET_FILE_PATH = 'allseasons.parquet'  # Replace with your actual Parquet file path
HOT_THRESHOLD = 30    # Days since last access to be considered "Hot"
COLD_THRESHOLD = 180  # Days since last access to be considered "Cold"

# Function to convert bytes to human-readable format
def bytes_to_human_readable(num, suffix='B'):
    """
    Converts bytes to a human-readable format (e.g., KB, MB, GB).

    Parameters:
    - num (int or float): The number of bytes.
    - suffix (str): The suffix to use (default is 'B' for bytes).

    Returns:
    - str: Human-readable string representation of the byte value.
    """
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Y{suffix}"

# Read the Parquet file
print("Reading the Parquet file...")
df = pd.read_parquet(PARQUET_FILE_PATH)

# Display basic information
print("\nDataFrame Info:")
print(df.info())

print("\nSample Data:")
print(df.head())

# Define Hot, Warm, and Cold Status
def categorize_hot_cold(days, hot_threshold=HOT_THRESHOLD, cold_threshold=COLD_THRESHOLD):
    if days <= hot_threshold:
        return 'Hot'
    elif days >= cold_threshold:
        return 'Cold'
    else:
        return 'Warm'

print("\nCategorizing data into Hot, Warm, and Cold based on days_since_last_access...")
df['access_status'] = df['days_since_last_access'].apply(categorize_hot_cold)

# Handle negative days_since_last_access if any
negative_days = df[df['days_since_last_access'] < 0]
if not negative_days.empty:
    print(f"\nFound {len(negative_days)} entries with negative days_since_last_access. Setting them to 0.")
    df.loc[df['days_since_last_access'] < 0, 'days_since_last_access'] = 0
    df['access_status'] = df['days_since_last_access'].apply(categorize_hot_cold)

# Summary Statistics based on Total Size
print("\nGenerating summary statistics based on total size...")

summary = df.groupby('access_status').agg(
    total_size_bytes=pd.NamedAgg(column='size', aggfunc='sum'),
    average_size_bytes=pd.NamedAgg(column='size', aggfunc='mean'),
    median_size_bytes=pd.NamedAgg(column='size', aggfunc='median'),
    max_size_bytes=pd.NamedAgg(column='size', aggfunc='max'),
    min_size_bytes=pd.NamedAgg(column='size', aggfunc='min')
).reset_index()

# Convert sizes to human-readable format
summary['total_size'] = summary['total_size_bytes'].apply(bytes_to_human_readable)
summary['average_size'] = summary['average_size_bytes'].apply(bytes_to_human_readable)
summary['median_size'] = summary['median_size_bytes'].apply(bytes_to_human_readable)
summary['max_size'] = summary['max_size_bytes'].apply(bytes_to_human_readable)
summary['min_size'] = summary['min_size_bytes'].apply(bytes_to_human_readable)

# Drop the original byte columns
summary = summary.drop(columns=['total_size_bytes', 'average_size_bytes', 'median_size_bytes', 'max_size_bytes', 'min_size_bytes'])

print("\nSummary Statistics by Access Status (Based on Total Size):")
print(summary)

# Pivot Tables based on Total Size

# 1. Total Size by File Extension and Department
print("\nCreating Pivot Table: Total Size by File Extension and Department...")
pivot_extension_department = df.pivot_table(
    index='file_extension',
    columns='department',
    values='size',
    aggfunc='sum'
).fillna(0)

# Convert to human-readable format
pivot_extension_department_hr = pivot_extension_department.applymap(bytes_to_human_readable)

# Sort by overall total size
pivot_extension_department['overall_total_size'] = pivot_extension_department.sum(axis=1)
pivot_extension_department_sorted = pivot_extension_department.sort_values(by='overall_total_size', ascending=False).drop(columns='overall_total_size')
pivot_extension_department_hr_sorted = pivot_extension_department_sorted.applymap(bytes_to_human_readable)

print("\nPivot Table: Total Size by File Extension and Department")
print(pivot_extension_department_hr_sorted)

# 2. Total Size of Hot, Warm, Cold Files by Season
print("\nCreating Pivot Table: Total Size of Hot, Warm, Cold Files by Season...")
pivot_season_status = df.pivot_table(
    index='season',
    columns='access_status',
    values='size',
    aggfunc='sum'
).fillna(0)

# Convert to human-readable format
pivot_season_status_hr = pivot_season_status.applymap(bytes_to_human_readable)

print("\nPivot Table: Total Size of Hot, Warm, Cold Files by Season")
print(pivot_season_status_hr)

# 3. Total Size of Files by File Extension and Access Status
print("\nCreating Pivot Table: Total File Size by File Extension and Access Status...")
pivot_size_extension_status = df.pivot_table(
    index='file_extension',
    columns='access_status',
    values='size',
    aggfunc='sum'
).fillna(0)

# Convert to human-readable format
pivot_size_extension_status_hr = pivot_size_extension_status.applymap(bytes_to_human_readable)

# Sort by 'Hot' size descending
if 'Hot' in pivot_size_extension_status_hr.columns:
    pivot_size_extension_status_hr_sorted = pivot_size_extension_status_hr.sort_values(by='Hot', ascending=False)
else:
    pivot_size_extension_status_hr_sorted = pivot_size_extension_status_hr

print("\nPivot Table: Total File Size by File Extension and Access Status")
print(pivot_size_extension_status_hr_sorted)

# 4. Total Size of Files by Department and Access Status
print("\nCreating Pivot Table: Total Size of Files by Department and Access Status...")
pivot_department_status = df.pivot_table(
    index='department',
    columns='access_status',
    values='size',
    aggfunc='sum'
).fillna(0)

# Convert to human-readable format
pivot_department_status_hr = pivot_department_status.applymap(bytes_to_human_readable)

# Sort by 'Hot' size descending
if 'Hot' in pivot_department_status_hr.columns:
    pivot_department_status_hr_sorted = pivot_department_status_hr.sort_values(by='Hot', ascending=False)
else:
    pivot_department_status_hr_sorted = pivot_department_status_hr

print("\nPivot Table: Total Size of Files by Department and Access Status")
print(pivot_department_status_hr_sorted)

# Export Pivot Tables to CSV with Human-Readable Sizes
print("\nExporting pivot tables to CSV files with human-readable sizes...")

# Ensure the output directory exists
output_dir = 'output_pivot_tables'
os.makedirs(output_dir, exist_ok=True)

# Save pivot tables
pivot_extension_department_hr_sorted.to_csv(os.path.join(output_dir, 'pivot_extension_department_hr.csv'))
pivot_season_status_hr.to_csv(os.path.join(output_dir, 'pivot_season_status_hr.csv'))
pivot_size_extension_status_hr_sorted.to_csv(os.path.join(output_dir, 'pivot_size_extension_status_hr.csv'))
pivot_department_status_hr_sorted.to_csv(os.path.join(output_dir, 'pivot_department_status_hr.csv'))
summary.to_csv(os.path.join(output_dir, 'summary_statistics_hr.csv'), index=False)

print(f"Pivot tables exported to the '{output_dir}' directory.")

# Optional: Save the updated DataFrame with access_status and human-readable size
print("\nSaving processed data with access_status and human-readable size...")
df['size_hr'] = df['size'].apply(bytes_to_human_readable)
processed_output_path = os.path.join(output_dir, 'processed_data_with_status_hr.csv')
df.to_csv(processed_output_path, index=False)
print(f"Processed data saved to '{processed_output_path}'.")
