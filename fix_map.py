import folium
from folium.plugins import HeatMap
import pandas as pd
import requests

print('Henter data...')
df = pd.DataFrame(requests.get(
    'https://data.sfgov.org/resource/wg3w-h783.json?$limit=100000').json())
df['latitude']  = pd.to_numeric(df['latitude'],  errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
df['incident_category'] = df['incident_category'].str.upper().str.strip()
df = df.dropna(subset=['latitude','longitude'])
df = df[df['latitude'].between(37.70, 37.84)]
df = df[df['longitude'].between(-122.52, -122.35)]

m = folium.Map(location=[37.762, -122.435], zoom_start=12, tiles='CartoDB dark_matter')

all_pts = df[['latitude','longitude']].sample(5000, random_state=42).values.tolist()
HeatMap(all_pts, radius=12, blur=15, name='All incidents', show=True).add_to(m)

for cat, grad, name in [
    ('LARCENY THEFT',       {"0.4":"#4CC9F0","1.0":"#4361EE"}, 'Larceny/Theft'),
    ('ASSAULT',             {"0.4":"#F72585","1.0":"#7209B7"}, 'Assault'),
    ('MOTOR VEHICLE THEFT', {"0.4":"#F8961E","1.0":"#F3722C"}, 'Motor Vehicle Theft'),
]:
    sub = df[df['incident_category'] == cat][['latitude','longitude']]
    if len(sub) > 2000:
        sub = sub.sample(2000, random_state=42)
    HeatMap(sub.values.tolist(), radius=10, blur=14,
            gradient=grad, name=name, show=False).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
m.save('docs/assignment2/fig2_map.html')
print('Done')