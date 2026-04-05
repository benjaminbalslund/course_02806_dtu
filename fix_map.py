import folium
from folium.plugins import HeatMap
import pandas as pd
import requests

print('Henter data...')
response = requests.get('https://data.sfgov.org/resource/wg3w-h783.json?$limit=100000')
df = pd.DataFrame(response.json())
df['latitude']  = pd.to_numeric(df['latitude'],  errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
df = df.dropna(subset=['latitude','longitude'])
df = df[df['latitude'].between(37.70, 37.84)]
df = df[df['longitude'].between(-122.52, -122.35)]

sample = df[['latitude','longitude']].sample(5000, random_state=42)

m = folium.Map(location=[37.762, -122.435], zoom_start=12, tiles='CartoDB dark_matter')
HeatMap(sample.values.tolist(), radius=12, blur=15).add_to(m)
m.save('docs/assignment2/fig2_map.html')
print('Done')

