#!/usr/bin/env python3
import os
import csv
import argparse
import multiprocessing
from multiprocessing import Pool, cpu_count
from functools import partial
from tqdm import tqdm
import psutil
import sys
import time
import logging
import functools
from datetime import datetime, timezone

# Configure Logging
logging.basicConfig(
    filename='metadata_collection.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Parallel File Metadata Collector for CIFS-mounted Shares',
        epilog='Example usage: megacollector.py /mnt/share /tmp/metadata.csv --processes 100 --batch_size 1000 --log_errors --monitor'
    )
    parser.add_argument(
        'mount_point',
        help='Path to the directory to scan (e.g., /mnt/share or a subdirectory)'
    )
    parser.add_argument(
        'output_csv',
        help='Path to the output CSV file (e.g., /tmp/metadata.csv)'
    )
    parser.add_argument(
        '--processes',
        type=int,
        default=cpu_count(),
        help='Number of parallel processes (default: number of CPU cores)'
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=1000,
        help='Number of files per batch (default: 1000)'
    )
    parser.add_argument(
        '--fields',
        nargs='+',
        default=['path', 'access_time', 'modify_time', 'change_time', 'size', 'file_type'],
        help='List of metadata fields to collect'
    )
    parser.add_argument(
        '--log_errors',
        action='store_true',
        help='Enable error logging'
    )
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Enable system resource monitoring'
    )
    return parser.parse_args()

def retry(ExceptionToCheck, tries=3, delay=2, backoff=2):
    """Retry decorator with exponential backoff."""
    def deco_retry(f):
        @functools.wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    logging.warning(f"{f.__name__} failed with {e}, retrying in {mdelay} seconds...")
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry
    return deco_retry

@retry(Exception, tries=3, delay=2, backoff=2)
def get_file_metadata(file_path, log_errors):
    """
    Retrieve metadata for a single file.
    Returns a dictionary with requested fields in Excel-compatible date format.
    """
    metadata = {}
    try:
        stat_info = os.stat(file_path, follow_symlinks=False)
        metadata['path'] = file_path
        
        # Convert epoch times to 'YYYY-MM-DD HH:MM:SS' format in local timezone
        # If you prefer UTC, replace datetime.fromtimestamp with datetime.utcfromtimestamp
        metadata['access_time'] = datetime.fromtimestamp(stat_info.st_atime).strftime('%Y-%m-%d %H:%M:%S')
        metadata['modify_time'] = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        metadata['change_time'] = datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        
        metadata['size'] = stat_info.st_size
        # Since we are iterating over files, 'file_type' will always be 'file'
        metadata['file_type'] = 'file'
    except Exception as e:
        metadata['path'] = file_path
        metadata['access_time'] = ''
        metadata['modify_time'] = ''
        metadata['change_time'] = ''
        metadata['size'] = ''
        metadata['file_type'] = ''
        metadata['error'] = str(e)
        if log_errors:
            logging.error(f"Error accessing {file_path}: {e}")
    return metadata

def traverse_files(mount_point, follow_symlinks=False):
    """
    Generator that yields file paths from the specified directory.
    """
    for root, dirs, files in os.walk(mount_point, followlinks=follow_symlinks):
        for file in files:
            yield os.path.join(root, file)

def write_metadata_to_csv(csv_writer, metadata_batch, fields):
    """
    Write a batch of metadata dictionaries to the CSV file without quoting fields.
    """
    for metadata in metadata_batch:
        row = [metadata.get(field, '') for field in fields]
        csv_writer.writerow(row)

def monitor_system(stop_event):
    """
    Optional: Monitor system resources and log if necessary.
    """
    while not stop_event.is_set():
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        logging.info(f"CPU Usage: {cpu}%, Memory Usage: {mem}%")
        time.sleep(10)  # Log every 10 seconds

def main():
    args = parse_arguments()

    # Removed Mount Point Validation
    # If you wish to add any other validation, you can do so here.

    # Prepare CSV File
    try:
        # Check if output file exists to prevent accidental overwrites
        if os.path.exists(args.output_csv):
            response = input(f"The file {args.output_csv} already exists. Overwrite? (y/n): ")
            if response.lower() != 'y':
                sys.exit("Operation cancelled by user.")
        csv_file = open(args.output_csv, 'w', newline='', encoding='utf-8')
    except Exception as e:
        logging.error(f"Failed to open CSV file {args.output_csv}: {e}")
        sys.exit(f"Error: Failed to open CSV file {args.output_csv}: {e}")

    # Initialize CSV Writer without quoting fields unnecessarily
    csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(args.fields)  # Write CSV Header

    # Prepare Multiprocessing Pool
    pool = Pool(processes=args.processes)

    # Initialize Progress Bar
    pbar = tqdm(desc="Collecting Metadata", unit="files")

    # Optional: Start System Resource Monitoring
    stop_event = multiprocessing.Event()
    if args.monitor:
        monitor = multiprocessing.Process(target=monitor_system, args=(stop_event,))
        monitor.start()

    # Prepare partial function with fixed arguments
    partial_get_file_metadata = partial(get_file_metadata, log_errors=args.log_errors)

    # Batch Processing
    metadata_batch = []
    batch_size = args.batch_size
    try:
        # Using imap_unordered for better performance
        for metadata in pool.imap_unordered(partial_get_file_metadata, traverse_files(args.mount_point), chunksize=100):
            metadata_batch.append(metadata)
            pbar.update(1)

            if len(metadata_batch) >= batch_size:
                write_metadata_to_csv(csv_writer, metadata_batch, args.fields)
                metadata_batch = []

        # Write remaining metadata
        if metadata_batch:
            write_metadata_to_csv(csv_writer, metadata_batch, args.fields)

    except KeyboardInterrupt:
        logging.warning("Metadata collection interrupted by user.")
        pool.terminate()
        pool.join()
        csv_file.close()
        sys.exit("Metadata collection interrupted by user.")
    except Exception as e:
        logging.error(f"An error occurred during metadata collection: {e}")
        pool.terminate()
        pool.join()
        csv_file.close()
        sys.exit(f"Error: {e}")
    finally:
        pool.close()
        pool.join()
        csv_file.close()
        pbar.close()
        if args.monitor:
            stop_event.set()
            monitor.join()

    logging.info("Metadata collection completed successfully.")
    print("Metadata collection completed successfully.")

if __name__ == '__main__':
    main()
