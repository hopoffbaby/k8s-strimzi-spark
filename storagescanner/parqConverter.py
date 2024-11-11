import pandas as pd
import sys
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq

def process_chunk(chunk, current_date, date_pattern, max_remaining_levels=3):
    # Calculate days since last access, modify, and change
    chunk['days_since_last_access'] = (current_date - chunk['access_time']).dt.days
    chunk['days_since_last_modify'] = (current_date - chunk['modify_time']).dt.days
    chunk['days_since_last_change'] = (current_date - chunk['change_time']).dt.days

    # Remove the file_type column if it exists
    if 'file_type' in chunk.columns:
        chunk = chunk.drop(columns=['file_type'])

    # Extract file extension from path
    chunk['file_extension'] = chunk['path'].str.extract(r'(\.[^./\\]+)$', expand=False).str.lower()

    # Extract filename with and without extension
    chunk['filename_with_extension'] = chunk['path'].str.split(r'[/\\]').str[-1]
    chunk['filename_without_extension'] = chunk['filename_with_extension'].str.replace(r'\.[^./\\]+$', '', regex=True)

    # Split the path into components and remove empty strings
    path_components = chunk['path'].str.split(r'[/\\]+').apply(lambda x: [i for i in x if i])

    # Convert the list of components into a DataFrame
    path_df = pd.DataFrame(path_components.tolist())

    # Assign column names for clarity
    path_df.columns = [f'level_{i}' for i in range(path_df.shape[1])]

    # Ensure path_df has at least 4 columns (mount_point, season, event, department)
    for i in range(4):
        level = f'level_{i}'
        if level not in path_df.columns:
            path_df[level] = pd.NA

    # Extract mount_point, season, event, and department based on directory structure
    chunk['mount_point'] = path_df['level_0'].astype(pd.StringDtype())
    chunk['season'] = path_df['level_1'].astype(pd.StringDtype())
    chunk['event'] = path_df['level_2'].astype(pd.StringDtype())
    chunk['department'] = path_df['level_3'].astype(pd.StringDtype())

    # Identify departments that are dates and replace them with 'chassis'
    matches = chunk['department'].str.match(date_pattern, na=False)
    chunk['department'] = chunk['department'].where(~matches, 'chassis')

    # Extract remaining directories excluding the filename
    # remaining_dirs is a list of directories after mount_point, season, event, department, and before the filename
    remaining_dirs = path_components.str[4:-1]

    # Expand remaining_dirs into separate columns
    remaining_dirs_expanded = pd.DataFrame(remaining_dirs.tolist(), index=chunk.index)

    # Assign remaining_level_1, remaining_level_2, remaining_level_3 with StringDtype
    for i in range(max_remaining_levels):
        column_name = f'remaining_level_{i+1}'
        if i in remaining_dirs_expanded.columns:
            chunk[column_name] = remaining_dirs_expanded[i].astype(pd.StringDtype())
        else:
            chunk[column_name] = pd.Series([pd.NA] * len(chunk), dtype=pd.StringDtype())

    return chunk

def main():
    if len(sys.argv) != 3:
        print("Usage: python parqConverter.py input.csv output.parquet")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # Define the chunk size (e.g., 1 million rows per chunk)
    chunksize = 10 ** 6

    # Current date for calculating days since last access, modify, and change
    current_date = pd.to_datetime(datetime.now())

    # Define the date pattern for department (YYYY-MM)
    date_pattern = r'^\d{4}-\d{2}$'

    # Initialize Parquet writer
    parquet_writer = None

    print("Processing CSV in chunks...")
    for i, chunk in enumerate(pd.read_csv(
        input_file,
        parse_dates=['access_time', 'modify_time', 'change_time'],
        low_memory=False,
        chunksize=chunksize
    ), start=1):
        print(f"Processing chunk {i} with {len(chunk)} rows...")

        # Process the current chunk
        processed_chunk = process_chunk(chunk, current_date, date_pattern)

        # Convert the processed chunk to an Arrow table
        table = pa.Table.from_pandas(processed_chunk, preserve_index=False)

        # Initialize ParquetWriter if it's the first chunk
        if parquet_writer is None:
            parquet_writer = pq.ParquetWriter(output_file, table.schema)
        
        # Write the table to the Parquet file
        parquet_writer.write_table(table)

    # Close the Parquet writer
    if parquet_writer is not None:
        parquet_writer.close()

    print("Processing complete. Parquet file created.")

if __name__ == '__main__':
    main()
