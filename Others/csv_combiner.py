import pandas as pd
import glob
import os

folder_path = "D:/777/numbers-tiempos/"
output_file = os.path.join(folder_path, "combined.csv")

# get all csv files
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

# read and concatenate
df_list = [pd.read_csv(file) for file in csv_files]
combined_df = pd.concat(df_list, ignore_index=True)

# save
combined_df.to_csv(output_file, index=False)

print("Done. Combined file saved as:", output_file)