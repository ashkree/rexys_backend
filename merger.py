import pandas as pd

# File paths (update these paths if needed)
steam_file = 'data/steam.csv'
description_file = 'data/steam_description_data.csv'
requirements_file = 'data/steam_requirements_data.csv'

# Load the datasets
steam_df = pd.read_csv(steam_file)
description_df = pd.read_csv(description_file)
requirements_df = pd.read_csv(requirements_file)

description_df.rename(columns={'steam_appid': 'appid'}, inplace=True)
requirements_df.rename(columns={'steam_appid': 'appid'}, inplace=True)


# Merge the datasets on 'appid'
merged_df = steam_df.merge(description_df, on='appid', how='left') \
                    .merge(requirements_df, on='appid', how='left')

# Assuming merged_df is your merged DataFrame
merged_df = merged_df.sample(n=5000, random_state=42)

# Display the first few rows of the merged DataFrame
print(merged_df.head())

# Optionally save the merged DataFrame to a CSV
merged_df.to_csv('merged_steam_data.csv', index=False)
