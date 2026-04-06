"""
Assignment 2 – Figur-generering
Henter data direkte fra SF OpenData API (samme metode som all_weeks.ipynb)
Kør: .venv/bin/python assignment2_figures.py
Output: docs/assignment2/
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import folium
from folium.plugins import HeatMap
import requests
import os

OUT_DIR = "docs/assignment2"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Hent data fra API (samme som all_weeks.ipynb) ────────────────────────────
print("Henter data fra SF OpenData API...")
api_nutidig = "https://data.sfgov.org/resource/wg3w-h783.json"
response = requests.get(f"{api_nutidig}?$limit=100000")
df = pd.DataFrame(response.json())
print(f"✓ {len(df):,} rækker hentet")

# ── Rens og forbered ─────────────────────────────────────────────────────────
df["incident_category"] = df["incident_category"].str.upper().str.strip()
df["police_district"]   = df["police_district"].str.upper().str.strip()
df["latitude"]  = pd.to_numeric(df.get("latitude"),  errors="coerce")
df["longitude"] = pd.to_numeric(df.get("longitude"), errors="coerce")

df = df[df["latitude"].between(37.70, 37.84)]
df = df[df["longitude"].between(-122.52, -122.35)]

top6 = df["incident_category"].value_counts().head(6).index.tolist()
print(f"Top 6 kategorier: {top6}")


# ── Figur 1: KDE hotspot-kort (statisk PNG) ──────────────────────────────────
df_geo = df.dropna(subset=["latitude", "longitude"])

fig1, ax = plt.subplots(figsize=(9, 9))
sns.kdeplot(data=df_geo, x="longitude", y="latitude",
            fill=True, cmap="Reds", thresh=0.04, levels=20, ax=ax)

ax.set_title("Crime Hotspots in San Francisco", fontsize=13, fontweight="bold")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.annotate("Tenderloin /\nDowntown", xy=(-122.412, 37.783),
            xytext=(-122.455, 37.800),
            arrowprops=dict(arrowstyle="->", color="#333"), fontsize=9)
ax.annotate("Mission District", xy=(-122.420, 37.760),
            xytext=(-122.460, 37.748),
            arrowprops=dict(arrowstyle="->", color="#333"), fontsize=9)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
fig1.savefig(f"{OUT_DIR}/fig1_hotspot.png", dpi=160, bbox_inches="tight")
plt.close()
print("✓ fig1_hotspot.png")


# ── Figur 2: Folium interaktivt heatmap ──────────────────────────────────────
sample = df_geo[["latitude","longitude"]].sample(min(50_000, len(df_geo)), random_state=42)

m = folium.Map(location=[37.762, -122.435], zoom_start=12, tiles="CartoDB dark_matter")
HeatMap(sample.values.tolist(), radius=10, blur=14, max_zoom=13,
        gradient={"0.3":"#3A86FF","0.6":"#FF006E","1.0":"#FFBE0B"},
        name="All incidents").add_to(m)

for cat, grad in [
    ("LARCENY THEFT",       {"0.4":"#4CC9F0","1.0":"#4361EE"}),
    ("ASSAULT",             {"0.4":"#F72585","1.0":"#7209B7"}),
    ("MOTOR VEHICLE THEFT", {"0.4":"#F8961E","1.0":"#F3722C"}),
]:
    sub = df_geo[df_geo["incident_category"] == cat][["latitude","longitude"]]
    sub = sub.sample(min(15_000, len(sub)), random_state=42)
    HeatMap(sub.values.tolist(), radius=9, blur=12, max_zoom=13,
            gradient=grad, name=cat.title(), show=False).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
m.get_root().html.add_child(folium.Element("""
<div style="position:fixed;top:12px;left:50%;transform:translateX(-50%);
     background:rgba(0,0,0,0.75);color:#fff;padding:8px 20px;border-radius:6px;
     font-family:sans-serif;font-size:13px;z-index:9999;">
  Heatmap — toggle layers using the control in the top right corner
</div>"""))
m.save(f"{OUT_DIR}/fig2_map.html")
print("✓ fig2_map.html")


# ── Figur 3: Plotly heatmap – distrikt × kategori overrepræsentation ─────────
valid = [d for d in df["police_district"].unique()
         if d not in ["NAN","OUT OF SF","UNKNOWN",""]]
df_d  = df[df["police_district"].isin(valid) & df["incident_category"].isin(top6)]

counts = df_d.groupby(["police_district","incident_category"]).size().reset_index(name="n")
counts = counts.merge(df_d.groupby("police_district").size().rename("dist_n"), on="police_district")
counts = counts.merge(df_d.groupby("incident_category").size().rename("cat_n"), on="incident_category")
counts["ratio"] = (counts["n"] / counts["dist_n"]) / (counts["cat_n"] / len(df_d))

pivot = counts.pivot(index="police_district", columns="incident_category", values="ratio").fillna(0)

fig3 = go.Figure(go.Heatmap(
    z=pivot.values,
    x=[c.title() for c in pivot.columns],
    y=pivot.index.tolist(),
    colorscale="RdBu_r", zmid=1.0,
    text=np.round(pivot.values, 2),
    texttemplate="%{text}",
    textfont={"size":10},
    hovertemplate="<b>%{y}</b> · <b>%{x}</b><br>Ratio: %{z:.2f}<extra></extra>",
    colorbar=dict(title="Ratio<br>(1 = avg)")
))
fig3.update_layout(
    title="Which crimes are over-/under-represented per police district?",
    xaxis=dict(title="Crime category", tickangle=-30),
    yaxis=dict(title="Police district"),
    plot_bgcolor="#FAFAF8", paper_bgcolor="#FAFAF8",
    font=dict(family="Georgia, serif", size=11),
    margin=dict(t=70, b=110, l=130, r=60), height=500
)
fig3.write_html(f"{OUT_DIR}/fig3_districts.html",
                include_plotlyjs="cdn", full_html=True,
                config={"responsive":True})
print("✓ fig3_districts.html")
print(f"\nAlt gemt i {OUT_DIR}/")