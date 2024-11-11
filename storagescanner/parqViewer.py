import pandas as pd

# Set display options to prevent truncation
pd.set_option('display.max_columns', None)      # Display all columns
pd.set_option('display.max_rows', 100)          # Limit display to 100 rows for convenience
pd.set_option('display.max_colwidth', 50)       # Do not truncate column content
pd.set_option('display.width', None)            # Auto-detect the display width

# Read the Parquet file
df = pd.read_parquet('race2024.parquet')

# Display basic information
print(df.info())

# Sample 100 random rows and display them
random_sample = df.sample(n=100, random_state=1)  # Use random_state for reproducibility
print(random_sample)
