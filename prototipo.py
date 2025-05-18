import folium
import json
import os
import webbrowser
import pandas as pd
from shapely.geometry import LineString
from tqdm import tqdm  

# === 1. Leer el GeoJSON ===
with open('C:/Users/pelay/Downloads/SREETS_NAV_4815096.geojson', encoding='utf-8') as f:
    data = json.load(f)

# === 2. Crear mapa base ===
primer_objeto = data['features'][0]
p = primer_objeto['geometry']['coordinates'][0]
m = folium.Map(location=[p[1], p[0]], zoom_start=16)

# === 3. Dibujar las líneas y guardar centroides por LINK_ID ===
centroides = {}

for feat in tqdm(data['features'], desc="Dibujando calles"):
    if feat['geometry']['type'] != 'LineString':
        continue

    coords = feat['geometry']['coordinates']
    if len(coords) < 2:
        continue

    
    coords_latlon = [[lat, lon] for lon, lat in coords]
    nombre = feat['properties'].get('ST_NAME', 'Sin nombre')
    dir_travel = feat['properties'].get('dir_travel', 'B').upper()

    # Dibujar la línea
    folium.PolyLine(coords_latlon, color='blue', weight=3, tooltip=f"{nombre} ({dir_travel})").add_to(m)

    # Agregar flechas con íconos en los extremos
    start = coords_latlon[0]
    end = coords_latlon[-1]

    if dir_travel == 'F':
        folium.Marker(
            location=start,
            icon=folium.Icon(icon='arrow-right', color='green'),
            tooltip="From Ref Node"
        ).add_to(m)

    elif dir_travel == 'T':
        folium.Marker(
            location=end,
            icon=folium.Icon(icon='arrow-left', color='orange'),
            tooltip="To Ref Node"
        ).add_to(m)

    elif dir_travel == 'B':
        folium.Marker(
            location=start,
            icon=folium.Icon(icon='arrow-right', color='blue'),
            tooltip="Bidirectional →"
        ).add_to(m)
        folium.Marker(
            location=end,
            icon=folium.Icon(icon='arrow-left', color='blue'),
            tooltip="Bidirectional ←"
        ).add_to(m)

   

    # Guardar centroide para usar con los POI
    line = LineString(coords)
    centroide = line.centroid
    link_id = feat['properties'].get('link_id') or feat['properties'].get('LINK_ID')
    if link_id is not None:
        centroides[link_id] = (centroide.y, centroide.x)


df = pd.read_csv('C:/Users/pelay/Downloads/POI_4815096.csv')

# === 4. AñadiMOS marcadores en los centroides correspondientes ===
for _, row in tqdm(df.iterrows(), total=len(df), desc="Colocando POIs"): 
    link_id = row['LINK_ID']
    poi_name = row.get('POI_NAME', 'POI')
    if link_id in centroides:
        lat, lon = centroides[link_id]
        folium.Marker(
            location=[lat, lon],
            popup=poi_name,
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)


output_file = 'mapacondirecciones.html'
m.save(output_file)
webbrowser.open('file://' + os.path.realpath(output_file))
