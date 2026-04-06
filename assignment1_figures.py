"""
Assignment 1 — Interaktive Plotly figurer
Kør: .venv/bin/python assignment1_figures.py
Output: docs/assignment1/  (fig1–fig5 + index.html)
"""

import pandas as pd
import numpy as np
import requests
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

OUT_DIR = "docs/assignment1"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Delte Plotly-indstillinger (samme look som Assignment 2) ─────────────────
CFG  = {"responsive": True, "displayModeBar": False}
FONT = dict(family="Georgia, serif", size=12, color="#1A1A1A")
BG   = "#FAFAF8"
RULE = "#DDDDDD"
RED  = "#E63946"
BLUE = "#457B9D"
PALETTE = [RED, BLUE, "#2A9D8F", "#E9C46A", "#F4A261",
           "#264653", "#6D6875", "#B5838D"]

def base_layout(**kwargs):
    base = dict(
        plot_bgcolor=BG, paper_bgcolor=BG, font=FONT,
        margin=dict(t=70, b=60, l=70, r=40),
        hoverlabel=dict(bgcolor="white", font_size=12,
                        font_family="Georgia, serif"),
    )
    # Only add default axes if caller hasn't specified them
    if "xaxis" not in kwargs:
        base["xaxis"] = dict(showgrid=True, gridcolor=RULE, zeroline=False)
    if "yaxis" not in kwargs:
        base["yaxis"] = dict(showgrid=True, gridcolor=RULE, zeroline=False)
    base.update(kwargs)
    return base

def save(fig, name):
    fig.write_html(f"{OUT_DIR}/{name}", include_plotlyjs="cdn",
                   full_html=True, config=CFG)
    print(f"✓ {name}")

# ── Hent data ────────────────────────────────────────────────────────────────
print("Henter data...")
df_r = pd.DataFrame(requests.get(
    "https://data.sfgov.org/resource/wg3w-h783.json?$limit=100000").json())
df_h = pd.DataFrame(requests.get(
    "https://data.sfgov.org/resource/tmnf-yvry.json?$limit=100000").json())

df_r = df_r.rename(columns={"incident_category": "category",
                              "incident_date": "date", "incident_time": "time",
                              "police_district": "district"})
df_h = df_h.rename(columns={"category": "category", "date": "date",
                              "time": "time", "pddistrict": "district",
                              "x": "longitude", "y": "latitude"})

keep = ["category", "date", "time", "district", "longitude", "latitude"]
for col in keep:
    if col not in df_r.columns: df_r[col] = np.nan
    if col not in df_h.columns: df_h[col] = np.nan

df = pd.concat([df_r[keep], df_h[keep]], ignore_index=True)
df["category"]  = df["category"].str.upper().str.strip()
df["district"]  = df["district"].str.upper().str.strip()
df["date"]      = pd.to_datetime(df["date"], errors="coerce")
df["year"]      = df["date"].dt.year
df["hour"]      = pd.to_datetime(df["time"], format="%H:%M",
                                  errors="coerce").dt.hour
df["latitude"]  = pd.to_numeric(df["latitude"],  errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
print(f"✓ {len(df):,} rækker")

FOCUS = [c for c in ["ASSAULT", "LARCENY THEFT", "BURGLARY", "ROBBERY",
                      "VANDALISM", "DRUG OFFENSE", "MOTOR VEHICLE THEFT",
                      "WARRANT"] if c in df["category"].unique()]
df_f = df[df["category"].isin(FOCUS)]
cmap = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(FOCUS)}


# ── Fig 1: Temporal tidsserie ─────────────────────────────────────────────────
yearly = (df_f[df_f["year"].between(2003, 2025)]
          .groupby(["year", "category"]).size().reset_index(name="n"))

# Shorten legend labels so they fit
LABELS = {c: c.title().replace("Motor Vehicle Theft","MV Theft")
               .replace("Larceny Theft","Larceny")
               .replace("Drug Offense","Drug Off.")
          for c in FOCUS}

fig1 = go.Figure()
for crime in FOCUS:
    sub = yearly[yearly["category"] == crime]
    fig1.add_trace(go.Scatter(
        x=sub["year"], y=sub["n"], mode="lines+markers",
        name=crime.title(),
        line=dict(color=cmap[crime], width=2),
        marker=dict(size=5),
        hovertemplate=f"<b>{crime.title()}</b><br>%{{x}}: <b>%{{y:,}}</b><extra></extra>"
    ))

# Annotate each line at its last data point (right side)
for crime in FOCUS:
    sub = yearly[yearly["category"] == crime].dropna()
    if len(sub) == 0: continue
    last = sub.iloc[-1]
    label = crime.title().replace("Motor Vehicle Theft","MV Theft").replace("Larceny Theft","Larceny").replace("Drug Offense","Drug Off.")
    fig1.add_annotation(
        x=last["year"], y=last["n"],
        text=f"  {label}",
        showarrow=False,
        xanchor="left", yanchor="middle",
        font=dict(size=10, color=cmap[crime]),
        bgcolor="rgba(250,250,248,0.0)"
    )

fig1.add_vrect(x0=2019.8, x1=2021.2, fillcolor="rgba(180,180,180,0.15)",
               line_width=0, annotation_text="COVID-19",
               annotation_position="top left",
               annotation=dict(font_size=10, font_color="#888"))
fig1.update_layout(**base_layout(
    title=dict(text="Crime Trends in San Francisco, 2003–2025", font=dict(size=15)),
    xaxis=dict(title="Year", dtick=2, showgrid=True, gridcolor=RULE, range=[2002, 2029]),
    yaxis=dict(title="Number of incidents", showgrid=True, gridcolor=RULE),
    showlegend=False, hovermode="x unified", height=460,
    margin=dict(t=70, b=60, l=70, r=110)
))
save(fig1, "fig1_temporal.html")


# ── Fig 2: District heatmap ───────────────────────────────────────────────────
valid = [d for d in df["district"].unique()
         if d not in ["NAN","OUT OF SF","UNKNOWN","","NAN"]]
df_d  = df[df["district"].isin(valid) & df["category"].isin(FOCUS)]
counts = df_d.groupby(["district","category"]).size().reset_index(name="n")
counts = counts.merge(df_d.groupby("district").size().rename("dn"), on="district")
counts = counts.merge(df_d.groupby("category").size().rename("cn"), on="category")
counts["ratio"] = (counts["n"] / counts["dn"]) / (counts["cn"] / len(df_d))
pivot = counts.pivot(index="district", columns="category",
                     values="ratio").fillna(0)
pivot.columns = [c.title() for c in pivot.columns]

fig2 = go.Figure(go.Heatmap(
    z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
    colorscale="RdBu_r", zmid=1.0,
    text=np.round(pivot.values, 2), texttemplate="%{text}",
    textfont={"size": 10},
    hovertemplate="<b>%{y}</b> · <b>%{x}</b><br>Ratio: <b>%{z:.2f}</b><extra></extra>",
    colorbar=dict(title="", tickvals=[0,1,2,3], ticktext=["0","1","2","3"],
                  thickness=15, len=0.85,
                  y=0.5, yanchor="middle")
))
fig2.update_layout(**base_layout(
    title=dict(text="Crime Over-representation per Police District",
               font=dict(size=15)),
    xaxis=dict(title="Crime category", tickangle=-30),
    yaxis=dict(title="Police district"),
    height=520, margin=dict(t=70, b=120, l=130, r=80)
))
save(fig2, "fig2_districts.html")


# ── Fig 3: Violin plots time-of-day ──────────────────────────────────────────
df_v = df_f.dropna(subset=["hour"])
fig3 = go.Figure()
for crime in FOCUS:
    sub = df_v[df_v["category"] == crime]["hour"].values
    fig3.add_trace(go.Violin(
        y=sub, name=crime.title(),
        box_visible=True, meanline_visible=True,
        fillcolor=cmap[crime], opacity=0.75,
        line_color="#333", hoverinfo="name+y"
    ))
fig3.update_layout(**base_layout(
    title=dict(text="Time-of-Day Distribution per Crime Category",
               font=dict(size=15)),
    yaxis=dict(title="Hour of day", tickvals=list(range(0,24,3)),
               ticktext=[f"{h:02d}:00" for h in range(0,24,3)],
               showgrid=True, gridcolor=RULE),
    xaxis=dict(tickangle=-30),
    showlegend=False, height=480
))
save(fig3, "fig3_distributions.html")


# ── Fig 4: Spatial power law ─────────────────────────────────────────────────
df_geo = df.dropna(subset=["latitude","longitude"])
df_geo = df_geo[df_geo["latitude"].between(37.70, 37.84)]
df_geo = df_geo[df_geo["longitude"].between(-122.52, -122.35)]
loc_n  = (df_geo.groupby(["latitude","longitude"]).size()
          .sort_values(ascending=False).values)
ranks  = np.arange(1, len(loc_n)+1)
log_r, log_c = np.log10(ranks), np.log10(loc_n+1)
coef   = np.polyfit(log_r, log_c, 1)
fit_y  = 10**np.polyval(coef, log_r)

fig4 = go.Figure()
fig4.add_trace(go.Scatter(
    x=ranks, y=loc_n, mode="markers",
    marker=dict(size=3, color=BLUE, opacity=0.45),
    name="Observed",
    showlegend=False,
    hovertemplate="Rank %{x}: <b>%{y}</b> incidents<extra></extra>"
))
fig4.add_trace(go.Scatter(
    x=ranks, y=fit_y, mode="lines",
    line=dict(color=RED, width=2),
    name=f"Fit (α={-coef[0]:.2f})",
    showlegend=False
))
# Annotate directly on the plot
fig4.add_annotation(x=ranks[5], y=loc_n[5],
    text="Observed", showarrow=False, xanchor="left",
    font=dict(size=11, color=BLUE), bgcolor="rgba(250,250,248,0.8)")
fig4.add_annotation(x=ranks[100], y=fit_y[100],
    text=f"Power-law fit (α={-coef[0]:.2f})", showarrow=False, xanchor="left",
    yshift=14, font=dict(size=11, color=RED), bgcolor="rgba(250,250,248,0.8)")
fig4.update_layout(**base_layout(
    title=dict(text="Spatial Power Law: Crime Concentration in SF",
               font=dict(size=15)),
    xaxis=dict(title="Location rank", type="log",
               showgrid=True, gridcolor=RULE),
    yaxis=dict(title="Number of incidents", type="log",
               showgrid=True, gridcolor=RULE),
    showlegend=False,
    height=430, margin=dict(t=70, b=60, l=70, r=40)
))
save(fig4, "fig4_powerlaw.html")


# ── Fig 5: Regression scatterplot matrix ─────────────────────────────────────
df["dayofweek"] = df["date"].dt.dayofweek
df["week_hour"] = df["dayofweek"] * 24 + df["hour"]
crimes4 = [c for c in ["ASSAULT","BURGLARY","ROBBERY","LARCENY THEFT"]
           if c in df["category"].unique()]
profiles = {c: df[df["category"] == c].groupby("week_hour").size()
              .reindex(range(168), fill_value=0).values.astype(float)
            for c in crimes4}

n    = len(crimes4)
fig5 = make_subplots(rows=n, cols=n,
                     horizontal_spacing=0.06, vertical_spacing=0.09)
for i, c1 in enumerate(crimes4):
    for j, c2 in enumerate(crimes4):
        x, y  = profiles[c2], profiles[c1]
        xm, ym = x.mean(), y.mean()
        b1 = np.sum((x-xm)*(y-ym)) / (np.sum((x-xm)**2)+1e-9)
        b0 = ym - b1*xm
        r2 = np.corrcoef(x, y)[0,1]**2
        fig5.add_trace(go.Scatter(
            x=x, y=y, mode="markers",
            marker=dict(size=4, color=BLUE, opacity=0.4),
            showlegend=False,
            hovertemplate=f"{c2.title()} vs {c1.title()}"
                          f"<br>R²={r2:.2f}<extra></extra>"
        ), row=i+1, col=j+1)
        fig5.add_trace(go.Scatter(
            x=[x.min(), x.max()],
            y=[b0+b1*x.min(), b0+b1*x.max()],
            mode="lines", line=dict(color=RED, width=1.5),
            showlegend=False
        ), row=i+1, col=j+1)
        # R² label: top-right corner of each panel using data coords
        fig5.add_annotation(
            text=f"R²={r2:.2f}",
            xref=f"x{i*n+j+1}", yref=f"y{i*n+j+1}",
            x=x.max(), y=y.max(),
            xanchor="right", yanchor="top",
            showarrow=False, font=dict(size=9, color="#333"),
            bgcolor="rgba(255,255,255,0.85)", borderpad=2
        )
        if i == n-1:
            fig5.update_xaxes(title_text=c2.title(),
                               title_font=dict(size=9), row=i+1, col=j+1)
        if j == 0:
            fig5.update_yaxes(title_text=c1.title(),
                               title_font=dict(size=9), row=i+1, col=j+1)

fig5.update_layout(
    title=dict(text="Weekly Rhythm Correlations — Scatterplot Matrix",
               font=dict(size=15, family="Georgia, serif", color="#1A1A1A")),
    plot_bgcolor=BG, paper_bgcolor=BG, font=FONT,
    margin=dict(t=70, b=60, l=90, r=30), height=640
)
save(fig5, "fig5_regression.html")
print(f"\nAlt klar i {OUT_DIR}/")