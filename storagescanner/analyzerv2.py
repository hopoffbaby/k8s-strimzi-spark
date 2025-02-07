#!/usr/bin/env python3

import argparse
import pandas as pd
import os
import sys
from pathlib import Path
from datetime import datetime
import logging
import numpy as np
import re

# Helper Functions
def human_readable_size(size, decimal_places=2):
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024
    return f"{size:.{decimal_places}f} PB"

def human_readable_number(number):
    return f"{number:,}"

def human_readable_percentage(percentage, decimal_places=2):
    return f"{percentage:.{decimal_places}f}%"

# Logging Setup
def setup_logging(log_file):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # File Handler
    fh = logging.FileHandler(log_file, mode='w')  # Overwrite previous logs
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Argument Parsing
def parse_arguments():
    parser = argparse.ArgumentParser(description='Analyze file access and data hot/cold-ness.')
    parser.add_argument('csv_file', help='Path to the input CSV file.')
    parser.add_argument('--parquet_file', help='Path to the parquet file for caching.', default=None)
    parser.add_argument('--log_file', help='Path to the log output file.', default='file_analysis.log')
    parser.add_argument('--current_date', help='Current date for analysis (YYYY-MM-DD). Defaults to today.', default=None)
    parser.add_argument('--mount_point', help='Mount point to ignore in path parsing.', default='/mnt/')
    return parser.parse_args()

# Data Loading
def load_data(csv_file, parquet_file=None):
    try:
        if parquet_file and os.path.exists(parquet_file):
            logging.info(f'Loading data from parquet file: {parquet_file}')
            df = pd.read_parquet(parquet_file)
        else:
            logging.info(f'Loading data from CSV file: {csv_file}')
            df = pd.read_csv(
                csv_file,
                parse_dates=['access_time', 'modify_time', 'change_time'],
                infer_datetime_format=True
            )
            if parquet_file:
                logging.info(f'Saving data to parquet file: {parquet_file}')
                df.to_parquet(parquet_file, index=False)
        logging.info('Data loaded successfully.')
        return df
    except Exception as e:
        logging.exception(f'Failed to load data: {e}')
        sys.exit(1)

# Field Extraction
def extract_fields(df, mount_point):
    try:
        logging.info('Extracting season, event, and department from paths.')

        mount_point = mount_point.rstrip('/') + '/'

        if 'path' not in df.columns:
            logging.error("'path' column is missing from the data.")
            sys.exit(1)

        def parse_path(path):
            try:
                p = Path(path)
                if not str(p).startswith(mount_point):
                    logging.warning(f'Path does not start with mount point and will be skipped: {path}')
                    return pd.Series({'season': 'Unknown', 'event': 'Unknown', 'department': 'Unknown'})
                relative = p.relative_to(mount_point)
                parts = relative.parts
                season = parts[0] if len(parts) >= 1 else 'Unknown'
                event = parts[1] if len(parts) >= 2 else 'Unknown'
                department = parts[2] if len(parts) >= 3 else 'Unknown'
                # Categorize 'department' as 'chassis' if it matches 'YYYY-MM'
                department_pattern = r'^\d{4}-\d{2}$'
                if re.match(department_pattern, department):
                    department = 'chassis'
                return pd.Series({'season': season, 'event': event, 'department': department})
            except Exception as e:
                logging.warning(f'Error parsing path {path}: {e}')
                return pd.Series({'season': 'Unknown', 'event': 'Unknown', 'department': 'Unknown'})

        extracted = df['path'].apply(parse_path)
        df = pd.concat([df, extracted], axis=1)

        df['file_extension'] = df['path'].str.extract(r'\.([^.\\/:*?"<>|\r\n]+)$', expand=False).str.lower().fillna('unknown')

        # Convert to categorical dtype
        for col in ['season', 'event', 'department', 'file_extension']:
            df[col] = df[col].astype('category')

        logging.info('Sample extracted fields:')
        logging.info(df[['path', 'season', 'event', 'department']].head(10).to_string(index=False))

        logging.info('Extraction of season, event, and department completed successfully.')
        return df
    except Exception as e:
        logging.exception(f'Failed to extract fields: {e}')
        sys.exit(1)

# Age Bucketing
def bucket_age(df, current_date):
    try:
        logging.info('Calculating age of files and bucketing into monthly intervals.')

        df['access_time'] = pd.to_datetime(df['access_time'], errors='coerce')
        initial_count = len(df)
        df = df.dropna(subset=['access_time'])
        dropped_count = initial_count - len(df)
        if dropped_count > 0:
            logging.warning(f'Dropped {dropped_count} rows due to invalid access_time.')

        df['age_days'] = (current_date - df['access_time']).dt.days
        df['age_months'] = df['age_days'] / 30  # Approximate

        bins = list(range(0, 25))  # 0 to 24
        labels = [f'{i}-{i+1} months' for i in range(0, 24)]
        labels.append('24+ months')

        df['age_bucket'] = pd.cut(
            df['age_months'],
            bins=bins + [float('inf')],
            labels=labels,
            right=False
        )

        df['age_bucket'] = df['age_bucket'].cat.add_categories(['Future'])
        df.loc[df['age_months'] < 0, 'age_bucket'] = 'Future'

        logging.info('Age bucketing completed successfully.')
        return df
    except Exception as e:
        logging.exception(f'Failed to bucket age: {e}')
        sys.exit(1)

# Coldness Analysis
def analyze_coldness(df):
    try:
        logging.info('Analyzing data coldness.')

        coldness_overall = df['age_bucket'].value_counts().sort_index()

        coldness_by_season = df.groupby(['season'])['age_bucket'].value_counts().unstack(fill_value=0).sort_index()
        coldness_by_event = df.groupby(['event'])['age_bucket'].value_counts().unstack(fill_value=0).sort_index()
        coldness_by_department = df.groupby(['department'])['age_bucket'].value_counts().unstack(fill_value=0).sort_index()

        logging.info('Coldness analysis completed successfully.')
        return coldness_overall, coldness_by_season, coldness_by_event, coldness_by_department
    except Exception as e:
        logging.exception(f'Failed to analyze coldness: {e}')
        sys.exit(1)

# Statistical Insights
def statistical_insights(coldness_by_category, category_name):
    try:
        logging.info(f'Generating statistical insights for {category_name}.')

        insights = coldness_by_category.div(coldness_by_category.sum(axis=1), axis=0) * 100
        insights = insights.fillna(0)

        logging.info(f'Statistical insights for {category_name} generated successfully.')
        return insights
    except Exception as e:
        logging.exception(f'Failed to generate statistical insights for {category_name}: {e}')
        sys.exit(1)

# File Extension Analysis
def file_extension_analysis(df):
    try:
        logging.info('Analyzing file extensions by total size.')

        if 'size' not in df.columns:
            logging.error("'size' column is missing from the data.")
            sys.exit(1)

        if not pd.api.types.is_numeric_dtype(df['size']):
            logging.info("'size' column is not numeric. Attempting to convert.")
            df['size'] = pd.to_numeric(df['size'], errors='coerce')
            invalid_sizes = df['size'].isna().sum()
            if invalid_sizes > 0:
                logging.warning(f'{invalid_sizes} rows have invalid size values and will be dropped.')
                df = df.dropna(subset=['size'])

        extension_sizes = df.groupby('file_extension')['size'].sum().sort_values(ascending=False)

        top_25 = extension_sizes.head(25)
        others = extension_sizes.iloc[25:].sum()

        other_series = pd.Series({'other': others})
        top_25 = pd.concat([top_25, other_series])

        top_25 = top_25.apply(lambda x: human_readable_size(x))

        logging.info('File extension analysis completed successfully.')
        return top_25
    except Exception as e:
        logging.exception(f'Failed to analyze file extensions: {e}')
        sys.exit(1)

# Dataset Statistics
def summarize_statistics(df):
    try:
        logging.info('Generating dataset statistics.')

        total_files = len(df)
        total_size = df['size'].sum()
        average_size = df['size'].mean()
        file_types = df['file_extension'].nunique()

        stats = {
            'Total Files': human_readable_number(total_files),
            'Total Size': human_readable_size(total_size),
            'Average File Size': human_readable_size(average_size),
            'Unique File Extensions': human_readable_number(file_types)
        }

        logging.info('Dataset statistics generated successfully.')
        return stats
    except Exception as e:
        logging.exception(f'Failed to summarize statistics: {e}')
        sys.exit(1)

# Output Results
def output_results(
    log_file,
    stats,
    coldness_overall,
    insights_season,
    insights_event,
    insights_department,
    extension_analysis
):
    try:
        logging.info('Outputting results.')

        # Since logging is already set up to write to the log file, we'll use logging instead of writing to the file directly.
        logging.info('\n=== Dataset Statistics ===')
        for key, value in stats.items():
            logging.info(f'{key}: {value}')

        logging.info('\n=== Overall Data Coldness ===')
        formatted_coldness_overall = coldness_overall.apply(human_readable_number)
        logging.info(formatted_coldness_overall.to_string())

        logging.info('\n=== Data Coldness by Season (Percentage) ===')
        formatted_insights_season = insights_season.applymap(human_readable_percentage)
        logging.info(formatted_insights_season.to_string())

        logging.info('\n=== Data Coldness by Event (Percentage) ===')
        formatted_insights_event = insights_event.applymap(human_readable_percentage)
        logging.info(formatted_insights_event.to_string())

        logging.info('\n=== Data Coldness by Department (Percentage) ===')
        formatted_insights_department = insights_department.applymap(human_readable_percentage)
        logging.info(formatted_insights_department.to_string())

        logging.info('\n=== File Extension Analysis (Top 25 + Other) ===')
        logging.info(extension_analysis.to_string())

        logging.info('Results have been successfully outputted to the log file.')
    except Exception as e:
        logging.exception(f'Failed to output results: {e}')
        sys.exit(1)

# Main Function
def main():
    args = parse_arguments()
    setup_logging(args.log_file)

    logging.info('Starting file access and data hot/cold-ness analysis.')

    # Determine current date
    if args.current_date:
        try:
            current_date = pd.to_datetime(args.current_date)
        except Exception as e:
            logging.error(f'Invalid current_date format: {args.current_date}. Use YYYY-MM-DD.')
            sys.exit(1)
    else:
        current_date = pd.to_datetime(datetime.now().date())

    logging.info(f'Using current date for analysis: {current_date.date()}')

    # Load data
    parquet_file = args.parquet_file if args.parquet_file else Path(args.csv_file).with_suffix('.parquet')
    df = load_data(args.csv_file, parquet_file)

    # Extract fields
    df = extract_fields(df, args.mount_point)

    # Drop rows with missing essential fields
    initial_count = len(df)
    df = df.dropna(subset=['season', 'event', 'department'])
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        logging.warning(f'Dropped {dropped_count} rows due to missing season/event/department.')

    # Bucket age
    df = bucket_age(df, current_date)

    # Analyze coldness
    coldness_overall, coldness_by_season, coldness_by_event, coldness_by_department = analyze_coldness(df)

    # Statistical insights
    insights_season = statistical_insights(coldness_by_season, 'Season')
    insights_event = statistical_insights(coldness_by_event, 'Event')
    insights_department = statistical_insights(coldness_by_department, 'Department')

    # File extension analysis
    extension_analysis = file_extension_analysis(df)

    # Dataset statistics
    stats = summarize_statistics(df)

    # Output results
    output_results(
        args.log_file,
        stats,
        coldness_overall,
        insights_season,
        insights_event,
        insights_department,
        extension_analysis
    )

    logging.info('Analysis complete. Results have been logged.')

if __name__ == '__main__':
    main()
