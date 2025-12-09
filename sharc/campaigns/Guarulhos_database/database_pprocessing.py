import pandas as pd
import numpy as np
from pathlib import Path
import math

# Function to adjust the decimal places of the coordinates
def round_dec_places(x):
    if math.isnan(x):
        return math.nan
    factor = 10 ** (int(math.log10(abs(x))) - 1)
    return round(x / factor, 6)

# File path
file_path = "./sharc/campaigns/Guarulhos_database/Base SP 3.5 GHz Rev2.xlsx"

# Load table
db_df = pd.read_excel(file_path)

# Nome da entidade (lower case)
db_df["NomeEntidade_norm"] = db_df["NomeEntidade"].str.strip().str.lower()

# Adicionar coluna de potência (se não houver)
if "tx_power" not in db_df.columns:
    db_df["tx_power"] = 10.0 * np.log10( db_df["PotenciaTransmissorWatts"] ) + 30.0  # ou qualquer valor padrão
# Adicionar coluna de downtilt (se não houver)
if "downtilt" not in db_df.columns:
    db_df["downtilt"] = 6.0

db_df["Latitude"] = db_df["Latitude"].apply(round_dec_places)
db_df["Longitude"] = db_df["Longitude"].apply(round_dec_places)

# Remove NaN rows
db_df = db_df.dropna(subset=["Latitude"])
db_df = db_df.dropna(subset=["Longitude"])

# Save dataframe to files
db_df.to_excel("Database_Anatel_FULL.xlsx", index=False)
db_df.to_csv("Database_Anatel_FULL.csv", sep="\t", index=False)


# Segmentar pelo valor da coluna "NomeEntidade_norm"
group = {k: v.copy() for k, v in db_df.groupby("NomeEntidade_norm")}

for nome, grupo in db_df.groupby("NomeEntidade_norm"):
    grupo.to_csv(f"./sharc/campaigns/Guarulhos_database/Database_Anatel_{nome}.csv", sep="\t", index=False)