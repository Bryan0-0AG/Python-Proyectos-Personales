from dash import dcc, html, dash_table
from dashboard.chatbot import seccion_chatbot

def crear_layout() -> html.Div:
    return html.Div([
        # ── Encabezado ────────────────────────────────────────────────────────
        html.Div(style={
            "height": "2px",
            "background": "linear-gradient(90deg, transparent, #00ffcc, #ff00aa, transparent)",
            "boxShadow": "0 0 12px #00ffcc66",
            "marginBottom": "30px",
        }),
        html.H1(
            "SCET",
            style={
                "textAlign": "center",
                "fontFamily": "'Orbitron', monospace",
                "color": "#00ffcc",
                "fontSize": "48px",
                "fontWeight": "900",
                "letterSpacing": "12px",
                "marginBottom": "8px",
                "textShadow": "0 0 10px #00ffcc, 0 0 30px #00ffcc44",
            },
        ),
        html.P(
            "SISTEMA CENTRALIZADO DE ESCANEO DE TLS",
            style={
                "textAlign": "center",
                "fontFamily": "'Share Tech Mono', monospace",
                "color": "#4a6a8a",
                "fontSize": "11px",
                "letterSpacing": "4px",
                "marginBottom": "36px",
            },
        ),

        # ── Contadores ────────────────────────────────────────────────────────
        html.Div([
            _tarjeta("0", "dominios_escaneados", "DOMINIOS ESCANEADOS", "#00ffcc"),
            _tarjeta("0", "riesgo_bajo",         "RIESGO BAJO",         "#00ff88"),
            _tarjeta("0", "requieren_atencion",  "REQUIEREN ATENCIÓN",  "#ff2255"),
        ], style={
            "display": "flex", "gap": "16px",
            "marginBottom": "28px", "padding": "0 24px",
        }),

        # ── Gráficas ──────────────────────────────────────────────────────────
        html.Div([
            dcc.Graph(id="fig_torta",  style={"flex": "1"}),
            dcc.Graph(id="fig_barras", style={"flex": "2"}),
        ], style={
            "display": "flex", "gap": "16px",
            "padding": "0 24px", "marginBottom": "28px",
        }),

        # ── Tabla detallada ───────────────────────────────────────────────────
        html.Div([
            html.H3("◈ DETALLE POR DOMINIO",
                    style={
                        "fontFamily": "'Orbitron', monospace",
                        "color": "#00ffcc",
                        "fontSize": "11px",
                        "letterSpacing": "4px",
                        "paddingLeft": "14px",
                        "borderLeft": "3px solid #00ffcc",
                        "marginBottom": "18px",
                    }),

            html.Div([
                _seccion_busqueda(),
                _seccion_filtros(),
            ], style={
                "display": "flex", "justifyContent": "space-between",
                "alignItems": "flex-end", "padding": "0 24px",
                "marginBottom": "14px", "flexWrap": "wrap", "gap": "16px",
            }),

            dash_table.DataTable(
                id="tabla_vision_general",
                row_selectable="multi",
                selected_rows=[],
                style_cell={
                    "fontFamily": "'Share Tech Mono', monospace",
                    "textAlign": "left",
                    "padding": "10px 14px",
                    "whiteSpace": "pre-line",
                    "backgroundColor": "#080818",
                    "color": "#000000",
                    "border": "1px solid #00ffcc11",
                    "fontSize": "12px",
                },
                style_header={
                    "backgroundColor": "#0a0a1f",
                    "color": "#00ffcc",
                    "fontWeight": "bold",
                    "fontFamily": "'Orbitron', monospace",
                    "fontSize": "10px",
                    "letterSpacing": "2px",
                    "border": "1px solid #00ffcc33",
                },
                style_table={
                    "margin": "0 24px",
                    "overflowX": "auto",
                    "overflowY": "auto",
                    "maxHeight": "400px",
                    "maxWidth": "calc(100% - 48px)",
                    "border": "1px solid #00ffcc22",
                },
            ),

            dcc.Store(id="signal_botones_tabla", data={}),

            html.Div(id="botones_tabla", children=[
                _boton("⟳ RE-ESCANEAR", "btn_reescanear",   "#00ffcc"),
                _boton("✕ ELIMINAR",    "btn_eliminar_fila", "#ff2255"),
            ], style={
                "display": "flex", "justifyContent": "flex-start",
                "alignItems": "center", "marginTop": "16px",
                "marginLeft": "24px", "gap": "12px",
            }),

            _seccion_sin_resultados(),

        ], style={
            "background": "linear-gradient(145deg, #0a0a1f, #060618)",
            "border": "1px solid #00ffcc33",
            "borderRadius": "4px",
            "padding": "24px 0",
            "margin": "0 24px 28px",
            "position": "relative",
        }),

        # ── Chatbot ───────────────────────────────────────────────────────────
        seccion_chatbot(),

        # ── Footer ────────────────────────────────────────────────────────────
        html.Div([
            html.Span("◈ SCET v2.0 // SECURE CHANNEL ACTIVE ",
                      style={"color": "#00ffcc", "fontSize": "10px",
                             "fontFamily": "'Share Tech Mono', monospace",
                             "letterSpacing": "2px"}),
            html.Span("█", style={"color": "#00ff88", "fontSize": "10px",
                                  "animation": "blink 1s step-end infinite"}),
        ], style={
            "textAlign": "center", "padding": "20px 0 10px",
            "borderTop": "1px solid #00ffcc22",
            "margin": "0 24px",
        }),

    ], style={
        "backgroundColor": "#050510",
        "minHeight": "100vh",
        "paddingBottom": "40px",
        "backgroundImage": "linear-gradient(rgba(0,255,204,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,204,0.03) 1px, transparent 1px)",
        "backgroundSize": "40px 40px",
    })


# ── Helpers ───────────────────────────────────────────────────────────────────
def _tarjeta(valor, id_elem, etiqueta, color):
    return html.Div([
        html.H2(valor, id=id_elem, style={
            "margin": "0",
            "fontSize": "42px",
            "fontFamily": "'Orbitron', monospace",
            "fontWeight": "900",
            "color": color,
            "textShadow": f"0 0 12px {color}",
            "lineHeight": "1",
        }),
        html.P(etiqueta, style={
            "margin": "8px 0 0",
            "fontFamily": "'Share Tech Mono', monospace",
            "fontSize": "10px",
            "letterSpacing": "2px",
            "color": "#4a6a8a",
        }),
    ], style={
        "background": "#0a0a1f",
        "border": f"1px solid {color}33",
        "borderBottom": f"2px solid {color}",
        "boxShadow": f"0 0 12px {color}11",
        "borderRadius": "4px",
        "padding": "22px 20px",
        "textAlign": "center",
        "flex": "1",
        "position": "relative",
    })


def _boton(texto, id_elem, color):
    return html.Button(
        texto, id=id_elem, n_clicks=0,
        style={
            "backgroundColor": "transparent",
            "color": color,
            "border": f"1px solid {color}",
            "borderRadius": "2px",
            "padding": "9px 22px",
            "cursor": "pointer",
            "fontFamily": "'Share Tech Mono', monospace",
            "fontSize": "12px",
            "letterSpacing": "2px",
            "textTransform": "uppercase",
            "transition": "background 0.2s",
            "clipPath": "polygon(8px 0%, 100% 0%, calc(100% - 8px) 100%, 0% 100%)",
        },
    )


def _seccion_busqueda():
    return html.Div([
        dcc.Input(id="busqueda_texto", type="text",
                  placeholder="buscar dominio...",
                  style={
                      "width": "200px",
                      "background": "#060618",
                      "border": "1px solid #00ffcc44",
                      "borderRadius": "2px",
                      "color": "#00ffcc",
                      "fontFamily": "'Share Tech Mono', monospace",
                      "fontSize": "12px",
                      "padding": "8px 12px",
                      "outline": "none",
                  }),
        dcc.Dropdown(
            id="busqueda_extension",
            options=[
                {"label": ".com", "value": ".com"},
                {"label": ".org", "value": ".org"},
                {"label": ".co",  "value": ".co"},
                {"label": ".net", "value": ".net"},
                {"label": "---",  "value": ""},
            ],
            value=".com",
            style={"width": "120px", "backgroundColor": "#060618"},
        ),
        html.Div(id="rg_resultado", style={
            "fontFamily": "'Share Tech Mono', monospace",
            "fontSize": "11px",
            "color": "#00ff88",
        }),
    ], style={"display": "flex", "gap": "10px", "alignItems": "center"})


def _seccion_filtros():
    return html.Div([
        html.Div([
            html.Label("FILTRAR POR COLUMNA", style={
                "fontFamily": "'Orbitron', monospace",
                "fontSize": "9px",
                "letterSpacing": "2px",
                "color": "#4a6a8a",
                "display": "block",
                "marginBottom": "6px",
            }),
            dcc.Dropdown(
                id="filtro_columna",
                options=[
                    {"label": "Riesgo",                      "value": "Riesgo"},
                    {"label": "Versión TLS",                 "value": "Version TLS"},
                    {"label": "Protocolo de cifrado",        "value": "Protocolo de cifrado"},
                    {"label": "Emisor de certificado TLS",   "value": "Emisor de certificado TLS"},
                ],
                placeholder="Selecciona columna",
                style={"width": "200px", "backgroundColor": "#060618"},
            ),
        ], style={"display": "flex", "flexDirection": "column", "gap": "5px"}),

        html.Div([
            html.Label("VALOR", style={
                "fontFamily": "'Orbitron', monospace",
                "fontSize": "9px",
                "letterSpacing": "2px",
                "color": "#4a6a8a",
                "display": "block",
                "marginBottom": "6px",
            }),
            dcc.Dropdown(
                id="filtro_valor",
                placeholder="Selecciona valor",
                style={"width": "200px", "backgroundColor": "#060618"},
            ),
        ], style={"display": "flex", "flexDirection": "column", "gap": "5px"}),

    ], style={"display": "flex", "gap": "20px", "alignItems": "flex-start"})


def _seccion_sin_resultados():
    return html.Div(
        id="sin_resultados_busqueda",
        style={"display": "none"},
        children=[
            html.Br(),
            html.H3("⚠ SIN RESULTADOS",
                    style={
                        "textAlign": "center",
                        "fontFamily": "'Orbitron', monospace",
                        "color": "#ffe000",
                        "fontSize": "13px",
                        "letterSpacing": "3px",
                        "marginTop": "10px",
                        "textShadow": "0 0 8px #ffe000",
                    }),
            html.Img(src="/assets/sin_resultados.png",
                     style={
                         "display": "block", "margin": "30px auto",
                         "maxWidth": "120px", "width": "100%",
                         "opacity": "0.4",
                         "filter": "sepia(1) hue-rotate(120deg)",
                     }),
            html.P("¿Desea registrar y escanear este dominio?",
                   id="mensaje_registro",
                   style={
                       "textAlign": "center",
                       "fontFamily": "'Share Tech Mono', monospace",
                       "color": "#4a8aaa",
                       "fontSize": "12px",
                       "marginTop": "10px",
                   }),
            html.Div(html.Button(
                "↗ REGISTRAR Y ESCANEAR", id="btn_registrar_dominio", n_clicks=0,
                style={
                    "display": "block", "margin": "12px auto",
                    "padding": "10px 24px",
                    "backgroundColor": "transparent",
                    "color": "#00ffcc",
                    "border": "1px solid #00ffcc",
                    "borderRadius": "2px",
                    "cursor": "pointer",
                    "fontFamily": "'Share Tech Mono', monospace",
                    "fontSize": "12px",
                    "letterSpacing": "2px",
                    "clipPath": "polygon(8px 0%, 100% 0%, calc(100% - 8px) 100%, 0% 100%)",
                },
            )),
        ],
    )