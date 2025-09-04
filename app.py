import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
import os


# Load your CSV file
csv_path = "longitudinal_with_bpm.csv"
df = pd.read_csv(csv_path, parse_dates=["Date"])


# Identify genus and species columns (exclude known columns)
known_cols = {"EBM", "Date", "Unit/Pen", "Pre/Post Fish", "Format", "Volume (L)", "Filter weight (g)", "Biomass (g/L)"}
all_taxa_cols = [col for col in df.columns if col not in known_cols]
genus_cols = [col for col in all_taxa_cols if len(col.split()) == 1]
species_cols = [col for col in all_taxa_cols if len(col.split()) > 1]



# Only include EBM samples with BPM or genus/species data
bpm_col = None
for col in df.columns:
    if "bpm" in col.lower():
        bpm_col = col
        break
def ebm_has_data(row):
    genus_data = row[genus_cols].apply(pd.to_numeric, errors='coerce').sum() > 0
    species_data = row[species_cols].apply(pd.to_numeric, errors='coerce').sum() > 0
    bpm_data = False
    if bpm_col:
        try:
            bpm_data = pd.to_numeric(row[bpm_col], errors='coerce') > 0
        except Exception:
            bpm_data = False
    return genus_data or species_data or bpm_data
valid_ebms = df[df.apply(ebm_has_data, axis=1)]["EBM"].dropna().unique()

# Use Google Fonts for Poppins
external_stylesheets = [
    'https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap'
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1(
        "Genus Abundance Over Time (Log Scale)",
        style={"fontFamily": "Poppins, sans-serif", "color": "rgb(14, 144, 122)"}
    ),
    html.Label(
        "Select Genus:",
        style={"fontFamily": "Poppins, sans-serif", "color": "rgb(14, 144, 122)"}
    ),
    dcc.Dropdown(
        id="genus-dropdown",
        options=[{"label": "Select All", "value": "__all__"}] + [{"label": genus, "value": genus} for genus in genus_cols],
        value=genus_cols[:1],
        multi=True,
        style={"fontFamily": "Poppins, sans-serif"}
    ),
    html.Label(
        "Select Species:",
        style={"fontFamily": "Poppins, sans-serif", "color": "rgb(14, 144, 122)"}
    ),
    dcc.Dropdown(
        id="species-dropdown",
        options=[{"label": "Select All", "value": "__all__"}] + [{"label": species, "value": species} for species in species_cols],
        value=[],
        multi=True,
        style={"fontFamily": "Poppins, sans-serif"}
    ),
    html.Label(
        "Filter by EBM:",
        style={"fontFamily": "Poppins, sans-serif", "color": "rgb(14, 144, 122)"}
    ),
    dcc.Dropdown(
        id="ebm-dropdown",
        options=[{"label": "Select All", "value": "__all__"}] + [{"label": ebm, "value": ebm} for ebm in valid_ebms],
        value=[],
        multi=True,
        placeholder="Select EBM(s) or leave empty for all",
        style={"fontFamily": "Poppins, sans-serif"}
    ),
        html.Label(
            "Filter by Unit/Pen:",
            style={"fontFamily": "Poppins, sans-serif", "color": "rgb(14, 144, 122)"}
        ),
        dcc.Dropdown(
            id="unitpen-dropdown",
            options=[{"label": "Select All", "value": "__all__"}] + [{"label": up, "value": up} for up in df["Unit/Pen"].dropna().unique()],
            value=[],
            multi=True,
            placeholder="Select Unit/Pen(s) or leave empty for all",
            style={"fontFamily": "Poppins, sans-serif"}
        ),
        html.Label(
            "Filter by Format:",
            style={"fontFamily": "Poppins, sans-serif", "color": "rgb(14, 144, 122)"}
        ),
        dcc.Dropdown(
            id="format-dropdown",
            options=[{"label": "Select All", "value": "__all__"}] + [{"label": fmt, "value": fmt} for fmt in df["Format"].dropna().unique()],
            value=[],
            multi=True,
            placeholder="Select Format(s) or leave empty for all",
            style={"fontFamily": "Poppins, sans-serif"}
        ),
        html.Label(
            "Filter by Pre/Post Fish:",
            style={"fontFamily": "Poppins, sans-serif", "color": "rgb(14, 144, 122)"}
        ),
        dcc.Dropdown(
            id="prepost-dropdown",
            options=[{"label": "Select All", "value": "__all__"}] + [{"label": pp, "value": pp} for pp in df["Pre/Post Fish"].dropna().unique()],
            value=[],
            multi=True,
            placeholder="Select Pre/Post Fish or leave empty for all",
            style={"fontFamily": "Poppins, sans-serif"}
        ),
    dcc.Graph(id="line-graph", style={"height": "900px"}),
    html.Div(id="pie-container")
],
    style={"fontFamily": "Poppins, sans-serif"}
)


# Updated callback to include all filters


# Multi-output callback for line graph and pie chart


from dash.dependencies import Output

@app.callback(
    [Output("line-graph", "figure"), Output("pie-container", "children")],
    [Input("genus-dropdown", "value"),
     Input("species-dropdown", "value"),
     Input("ebm-dropdown", "value"),
     Input("unitpen-dropdown", "value"),
     Input("format-dropdown", "value"),
     Input("prepost-dropdown", "value")]
)
def update_graph_and_pie(selected_genera, selected_species, selected_ebms, selected_unitpen, selected_format, selected_prepost):
    filtered = df.copy()
    # Handle 'Select All' for each filter
    if selected_ebms:
        if "__all__" in selected_ebms:
            pass  # No filter
        else:
            filtered = filtered[filtered["EBM"].isin(selected_ebms)]
    if selected_unitpen:
        if "__all__" in selected_unitpen:
            pass
        else:
            filtered = filtered[filtered["Unit/Pen"].isin(selected_unitpen)]
    if selected_format:
        if "__all__" in selected_format:
            pass
        else:
            filtered = filtered[filtered["Format"].isin(selected_format)]
    if selected_prepost:
        if "__all__" in selected_prepost:
            pass
        else:
            filtered = filtered[filtered["Pre/Post Fish"].isin(selected_prepost)]
    # Genus select all
    if selected_genera:
        if "__all__" in selected_genera:
            selected_genera = genus_cols
    # Species select all
    if selected_species:
        if "__all__" in selected_species:
            selected_species = species_cols
    fig = go.Figure()
    group_cols = ["Unit/Pen", "Format", "Pre/Post Fish"]
    for genus in selected_genera:
        for keys, group in filtered.groupby(group_cols):
            y_vals = pd.to_numeric(group[genus], errors="coerce").replace(0, np.nan)
            if y_vals.notna().sum() == 0:
                continue
            hover_text = group.apply(lambda row: '<br>'.join([
                f"EBM: {row['EBM']}",
                f"Date: {row['Date'].strftime('%Y-%m-%d') if not pd.isnull(row['Date']) else ''}",
                f"Unit/Pen: {row.get('Unit/Pen','')}",
                f"Pre/Post Fish: {row.get('Pre/Post Fish','')}",
                f"Format: {row.get('Format','')}",
                f"{genus}: {row[genus]}"
            ]), axis=1)
            fig.add_trace(go.Scatter(
                x=group["Date"],
                y=y_vals,
                mode="lines+markers",
                name=f"{genus} | Pen: {keys[0]} | Format: {keys[1]} | {keys[2]}",
                text=hover_text,
                hoverinfo="text"
            ))
    for species in selected_species:
        for keys, group in filtered.groupby(group_cols):
            y_vals = pd.to_numeric(group[species], errors="coerce").replace(0, np.nan)
            if y_vals.notna().sum() == 0:
                continue
            hover_text = group.apply(lambda row: '<br>'.join([
                f"EBM: {row['EBM']}",
                f"Date: {row['Date'].strftime('%Y-%m-%d') if not pd.isnull(row['Date']) else ''}",
                f"Unit/Pen: {row.get('Unit/Pen','')}",
                f"Pre/Post Fish: {row.get('Pre/Post Fish','')}",
                f"Format: {row.get('Format','')}",
                f"{species}: {row[species]}"
            ]), axis=1)
            fig.add_trace(go.Scatter(
                x=group["Date"],
                y=y_vals,
                mode="lines+markers",
                name=f"{species} | Pen: {keys[0]} | Format: {keys[1]} | {keys[2]}",
                text=hover_text,
                hoverinfo="text"
            ))
    # Dynamically set x-axis range to only include filtered dates, with padding
    if not filtered.empty:
        min_date = filtered["Date"].min()
        max_date = filtered["Date"].max()
        date_span = (max_date - min_date)
        pad = pd.Timedelta(days=max(1, int(date_span.days * 0.05))) if date_span.days > 0 else pd.Timedelta(days=1)
        padded_min = min_date - pad
        padded_max = max_date + pad
        xaxis_range = [padded_min, padded_max]
    else:
        xaxis_range = None
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Abundance (log scale)",
        legend_title="Genus/Species",
        yaxis=dict(type="log", autorange=True),
        xaxis=dict(autorange=False, range=xaxis_range) if xaxis_range else dict(autorange=True),
        height=900,
        font=dict(family="Poppins, sans-serif", color="rgb(14, 144, 122)")
    )
    # PIE CHART LOGIC
    pie_div = html.Div()
    # Only show pie chart if exactly one EBM is selected
    if selected_ebms and len(selected_ebms) == 1 and selected_ebms[0] != "__all__":
        ebm_sample = filtered[filtered["EBM"] == selected_ebms[0]]
        if not ebm_sample.empty:
            genus_numeric = ebm_sample[genus_cols].apply(pd.to_numeric, errors='coerce')
            genus_values = genus_numeric.sum()
            genus_values = genus_values[genus_values > 0]
            if not genus_values.empty:
                pie_fig = go.Figure(data=[go.Pie(labels=genus_values.index, values=genus_values.values)])
                pie_fig.update_layout(
                    title=f"Genus Population Percentages for EBM {selected_ebms[0]}",
                    font=dict(family="Poppins, sans-serif", color="rgb(14, 144, 122)")
                )
                pie_div = dcc.Graph(figure=pie_fig, style={"height": "500px"})
    return fig, pie_div

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8050)))
