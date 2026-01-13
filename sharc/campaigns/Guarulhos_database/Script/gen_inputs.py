from pathlib import Path
from ruamel.yaml import YAML
from copy import deepcopy
import math
import random
import os
import numpy as np

def latlon2xy(lat, lon, lat0, lon0):

    # Raio médio da Terra (metros)
    R = 6378100

    # Converter graus para radianos
    lat = math.radians(lat)
    lon = math.radians(lon)
    lat0 = math.radians(lat0)
    lon0 = math.radians(lon0)

    # Conversão equiretangular
    x = R * (lon - lon0) * math.cos(lat0)  # Leste
    y = R * (lat - lat0)                   # Norte

    return x, y

def xy2latlon(x, y, lat0, lon0):
    # Raio médio da Terra (metros)
    R = 6378100

    lat0 = math.radians(lat0)
    lon0 = math.radians(lon0)

    lat = y / R + lat0
    lon = x / (R * math.cos(lat0)) + lon0

    return math.degrees(lat), math.degrees(lon)

# Caminhos
BASE_YAML = Path("./sharc/campaigns/Guarulhos_database/Script/Base.yaml")
OUT_DIR   = Path("./sharc/campaigns/Guarulhos_database/input/")

print(BASE_YAML, OUT_DIR)

# Parâmetros Geometricos -----------------------------------------

# Coordenada central da região de estudo (centro do círculo)
lat_c = -23.6041
lon_c = -46.5919

# Coordenada de inicio [°]
lat_0 = -23.5685
lon_0 = -46.8609
# Coordenadas central [m]
x_0, y_0 = latlon2xy(lat_0, lon_0, lat_c, lon_c)

# Coordenadas de pouso [°]
lat_f = -23.4304
lon_f = -46.4832
# Coordenadas de pouso [m]
x_f, y_f = latlon2xy(lat_f, lon_f, lat_c, lon_c)

# Vetor direção do percurso
dir_v = np.array([x_f-x_0, y_f-y_0]) / np.sqrt( (x_f-x_0)**2 + (y_f-y_0)**2 )

# Ângulo de descida da aeronave
GLIDESLOPE_DEG  = 3.0         # rampa (graus)

# Distâncias no plano até pouso do avião
DISTANCES_M = [
    1000,
    2000,
    6000,
    10000,
    15000,
    20000,
    25000,
    30000,
]

# Leitura do Yaml --------------------------------------------------
yaml = YAML(typ="rt")
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)

# Carrega o template
data = yaml.load(BASE_YAML.read_text(encoding="utf-8"))

# Acessos conforme o Base.yaml
sss   = data["single_space_station"]
geom  = sss["geometry"]
loc   = geom["location"]
fixed = loc["fixed"]

# Mudar a coordenada de referência
geom['es_lat_deg'] = lat_c
geom['es_long_deg'] = lon_c

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Loop nas distâncias ----------------------------------------------
total_files = 0
for s_m in DISTANCES_M:

    # altura na rampa
    h_n  = math.tan(math.radians(GLIDESLOPE_DEG)) * s_m
    # Coordenadas locais em metros
    x_n = x_f - s_m * dir_v[0]
    y_n = y_f - s_m * dir_v[1]
    # Coordenadas locais em graus
    lat_n, lon_n = xy2latlon(x_n, y_n, lat_c, lon_c)

    print(s_m, lat_n, lon_n, lat_c, lon_c)
    # ---- gera cópia e edita ----
    doc = deepcopy(data)

    g   = doc["single_space_station"]["geometry"]
    fx  = g["location"]["fixed"]
    g["altitude"]   = float(f"{h_n:.2f}")
    fx["lat_deg"]   = float(f"{lat_n:.6f}")
    fx["long_deg"]  = float(f"{lon_n:.6f}")
    num = random.randint(0, 1000)
    doc["general"]["seed"] = num

    # muda também o prefixo
    if "general" in doc and isinstance(doc["general"], dict):
        doc["general"]["output_dir_prefix"] = f"database_sim_approach_fixed_gain_{int(s_m)}m_fixed_h"

    # salva com nome pela distância
    out = OUT_DIR / f"database_sim_approach_fixed_gain_{int(s_m)}m_fixed_h.yaml"
    with out.open("w", encoding="utf-8") as f:
        yaml.dump(doc, f)

    total_files += 1

print(f"OK! Gerados {total_files} arquivos em {OUT_DIR}")
