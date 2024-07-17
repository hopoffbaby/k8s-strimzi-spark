#pip install pyarrow

import pyarrow.parquet as pq

# Specify the path to your Parquet file
parquet_file = r'.\parquet\Flights-1m.parquet'

# Open the Parquet file
file = pq.ParquetFile(parquet_file)

# Get the metadata (stored in the file footer)
metadata = file.metadata

# Print basic file metadata
print(f"Number of row groups: {metadata.num_row_groups}")
print(f"Number of rows: {metadata.num_rows}")
print(f"Number of columns: {metadata.num_columns}")

# Print schema
print("\nSchema:")
print(metadata.schema)

# Print column details
print("\nColumn Details:")
schema = metadata.schema
for i in range(metadata.num_columns):
    column_schema = schema.column(i)
    print(f"Column {i}:")
    print(f"  Name: {column_schema.name}")
    print(f"  Physical Type: {column_schema.physical_type}")
    print(f"  Logical Type: {column_schema.logical_type}")
    print(f"  Max Definition Level: {column_schema.max_definition_level}")
    print(f"  Max Repetition Level: {column_schema.max_repetition_level}")

# Print row group information
print("\nRow Group Information:")
for i in range(metadata.num_row_groups):
    row_group = metadata.row_group(i)
    print(f"Row Group {i}:")
    print(f"  Number of rows: {row_group.num_rows}")
    print(f"  Total byte size: {row_group.total_byte_size}")
    print(f"  Compression: {row_group.column(0).compression}")

# Print key-value metadata (if any)
if metadata.metadata:
    print("\nKey-Value Metadata:")
    for key, value in metadata.metadata.items():
        print(f"  {key}: {value}")


# Calculate byte range for row group 5
target_row_group = 5
start_pos = 0
for i in range(target_row_group):
    start_pos += metadata.row_group(i).total_byte_size

end_pos = start_pos + metadata.row_group(target_row_group).total_byte_size - 1

print(f"\nByte range for Row Group {target_row_group}:")
print(f"Start position: {start_pos}")
print(f"End position: {end_pos}")
print(f"Range header: bytes={start_pos}-{end_pos}")


def extract_byte_range(file_path, start_pos, end_pos):
    with open(file_path, 'rb') as file:
        file.seek(start_pos)
        return file.read(end_pos - start_pos + 1)
    

# Extract the byte range
extracted_data = extract_byte_range(parquet_file, start_pos, end_pos)

# Save the extracted data to a new file
output_file = f'./parquet/row_group_{target_row_group}.parquet'
with open(output_file, 'wb') as file:
    file.write(extracted_data)

print(f"\nExtracted data saved to {output_file}")

