import plotly.express as px
import pandas as pd

from config import COLORES_RIESGO, COLORES_TABLA
from storage.file_manager import leer_csv

_LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#030310",
    font=dict(family="'Share Tech Mono', monospace", color="#c8f0ff", size=11),
    title_font=dict(family="'Orbitron', monospace", color="#00ffcc", size=11),
    margin=dict(l=16, r=16, t=44, b=16),
    legend=dict(
        bgcolor="rgba(5,5,16,0.8)",
        font=dict(family="'Share Tech Mono', monospace", color="#c8f0ff", size=10),
    ),
    xaxis=dict(
        tickfont=dict(color="#4a6a8a", size=10),
        title_font=dict(color="#4a6a8a"),
    ),
    yaxis=dict(
        tickfont=dict(color="#4a6a8a", size=10),
        title_font=dict(color="#4a6a8a"),
    ),
)


def obtener_info_actualizada() -> dict:
    df = leer_csv()

    # ── Gráfica de torta ──────────────────────────────────────────────────────
    conteo = df["Riesgo"].value_counts().reset_index()
    conteo.columns = ["Riesgo", "Cantidad"]
    fig_torta = px.pie(
        conteo,
        names="Riesgo",
        values="Cantidad",
        title="◈ DISTRIBUCIÓN DE RIESGOS",
        color="Riesgo",
        color_discrete_map=COLORES_RIESGO,
        hole=0.45,
    )
    fig_torta.update_traces(
        textfont=dict(family="'Share Tech Mono', monospace", size=11, color="#c8f0ff"),
        marker=dict(line=dict(color="#050510", width=2)),
    )
    fig_torta.update_layout(
        **_LAYOUT_BASE,
        annotations=[dict(
            text="RIESGO", x=0.5, y=0.5, showarrow=False,
            font=dict(family="'Orbitron', monospace", size=10, color="#00ffcc"),
        )],
    )

    # ── Gráfica de barras ─────────────────────────────────────────────────────
    df_validos = df[df["Vence en"] > 0].copy()
    fig_barras = px.bar(
        df_validos,
        x="Dominio",
        y="Vence en",
        title="◈ DÍAS HASTA VENCIMIENTO DEL CERTIFICADO",
        color="Riesgo",
        color_discrete_map=COLORES_RIESGO,
        text="Vence en",
    )
    fig_barras.update_traces(
        textposition="outside",
        textfont=dict(family="'Share Tech Mono', monospace", size=10, color="#c8f0ff"),
        marker_line_color="rgba(0,0,0,0)",
    )
    fig_barras.update_layout(**_LAYOUT_BASE, bargap=0.25)

    # ── Estilo condicional de la tabla ────────────────────────────────────────
    estilo_tabla = [
        {"if": {"filter_query": f'{{Riesgo}} = "{r}"'}, "backgroundColor": c}
        for r, c in COLORES_TABLA.items()
    ]

    return {
        "dominios_escaneados":         str(len(df)),
        "cantidad_riesgo_bajo":        str(len(df[df["Riesgo"] == "BAJO"])),
        "cantidad_requieren_atencion": str(len(df[df["Riesgo"].isin(["ALTO", "CRITICO"])])),
        "fig_torta":                   fig_torta,
        "fig_barras":                  fig_barras,
        "tabla_data":                  df.to_dict("records"),
        "tabla_columns":               [{"name": c, "id": c} for c in df.columns],
        "estilo_tabla":                estilo_tabla,
    }