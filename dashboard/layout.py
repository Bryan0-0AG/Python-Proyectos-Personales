from dash import dcc, html, dash_table
from dashboard.chatbot import seccion_chatbot          # ← NUEVO


def crear_layout() -> html.Div:
    """Devuelve el layout completo del dashboard."""
    return html.Div([
        # ── Encabezado ────────────────────────────────────────────────────────
        html.H1(
            "Dashboard de Seguridad TLS",
            style={"textAlign": "center", "fontFamily": "Arial",
                   "color": "#2c3e50", "marginBottom": "10px"},
        ),
        html.P(
            "Sistema centralizado de monitoreo de certificados SSL/TLS",
            style={"textAlign": "center", "fontFamily": "Arial",
                   "color": "#7f8c8d", "marginBottom": "30px"},
        ),

        # ── Contadores ────────────────────────────────────────────────────────
        html.Div([
            _tarjeta("0", "dominios_escaneados", "Dominios escaneados", "#3498db"),
            _tarjeta("0", "riesgo_bajo",         "Riesgo bajo",         "#2ecc71"),
            _tarjeta("0", "requieren_atencion",  "Requieren atención",  "#e74c3c"),
        ], style={"display": "flex", "gap": "20px",
                  "marginBottom": "30px", "padding": "0 20px"}),

        # ── Gráficas ──────────────────────────────────────────────────────────
        html.Div([
            dcc.Graph(id="fig_torta",  style={"flex": "1"}),
            dcc.Graph(id="fig_barras", style={"flex": "2"}),
        ], style={"display": "flex", "gap": "20px",
                  "padding": "0 20px", "marginBottom": "30px"}),

        # ── Tabla detallada ───────────────────────────────────────────────────
        html.Div([
            html.H3("Detalle por dominio",
                    style={"fontFamily": "Arial", "color": "#2c3e50",
                           "paddingLeft": "20px"}),

            html.Div([
                _seccion_busqueda(),
                _seccion_filtros(),
            ], style={"display": "flex", "justifyContent": "space-between",
                      "alignItems": "center", "padding": "0 20px",
                      "marginBottom": "10px"}),

            dash_table.DataTable(
                id="tabla_vision_general",
                row_selectable="multi",
                selected_rows=[],
                style_cell={"fontFamily": "Arial", "textAlign": "left",
                            "padding": "10px"},
                style_header={"backgroundColor": "#2c3e50", "color": "white",
                               "fontWeight": "bold"},
                style_table={
                    "margin": "0 20px", "overflowX": "auto",
                    "maxWidth": "98%",  "overflowY": "auto",
                    "maxHeight": "400px",
                },
            ),

            dcc.Store(id="signal_botones_tabla", data={}),

            html.Div(id="botones_tabla", children=[
                _boton("Re-escanear dominio(s)", "btn_reescanear",   "#3498db"),
                _boton("Eliminar dominio(s)",    "btn_eliminar_fila","#e74c3c"),
            ], style={"display": "flex", "justifyContent": "flex-start",
                      "alignItems": "center", "marginTop": "15px",
                      "marginLeft": "20px", "gap": "10px"}),

            _seccion_sin_resultados(),
        ]),

        # ── Chatbot RADAR AI ──────────────────────────────────────────────────
        seccion_chatbot(),                             # ← NUEVO

    ], style={"backgroundColor": "#f8f9fa", "minHeight": "100vh",
              "paddingBottom": "40px"})


# ── Helpers ────────────────────────────────────────────────────────────────────

def _tarjeta(valor, id_elem, etiqueta, color):
    return html.Div([
        html.H2(valor, id=id_elem, style={"margin": "0", "fontSize": "36px"}),
        html.P(etiqueta, style={"margin": "0"}),
    ], style={"background": color, "color": "white", "padding": "20px",
              "borderRadius": "10px", "textAlign": "center", "flex": "1"})


def _boton(texto, id_elem, color):
    return html.Button(
        texto, id=id_elem, n_clicks=0,
        style={"backgroundColor": color, "color": "white", "border": "none",
               "borderRadius": "8px", "padding": "10px 20px",
               "cursor": "pointer", "fontWeight": "bold", "transition": "0.2s"},
    )


def _seccion_busqueda():
    return html.Div([
        dcc.Input(id="busqueda_texto", type="text",
                  placeholder="buscar por dominio",
                  style={"width": "200px"}),
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
            style={"width": "150px"},
        ),
        html.Div(id="rg_resultado"),
    ], style={"display": "flex", "gap": "10px", "alignItems": "center"})


def _seccion_filtros():
    return html.Div([
        html.Div([
            html.Label("Filtrar por columna:"),
            dcc.Dropdown(
                id="filtro_columna",
                options=[
                    {"label": "Riesgo",                    "value": "Riesgo"},
                    {"label": "Versión TLS",               "value": "Version TLS"},
                    {"label": "Protocolo de cifrado",      "value": "Protocolo de cifrado"},
                    {"label": "Emisor de certificado TLS", "value": "Emisor de certificado TLS"},
                ],
                placeholder="Selecciona una columna",
                style={"width": "200px"},
            ),
        ], style={"display": "flex", "flexDirection": "column", "gap": "5px"}),

        html.Div([
            html.Label("Selecciona valor:"),
            dcc.Dropdown(
                id="filtro_valor",
                placeholder="Primero selecciona una columna",
                style={"width": "200px"},
            ),
        ], style={"display": "flex", "flexDirection": "column", "gap": "5px"}),
    ], style={"display": "flex", "gap": "20px", "alignItems": "flex-start"})


def _seccion_sin_resultados():
    return html.Div(
        id="sin_resultados_busqueda",
        style={"display": "none"},
        children=[
            html.Br(),
            html.H3("No se encontraron resultados",
                    style={"textAlign": "center", "color": "#2c3e50",
                           "marginTop": "10px"}),
            html.Img(src="/assets/sin_resultados.png",
                     style={"display": "block", "margin": "40px auto",
                            "maxWidth": "150px", "width": "100%",
                            "opacity": "0.8"}),
            html.P("¿Desea registrar y escanear este dominio?",
                   id="mensaje_registro",
                   style={"textAlign": "center", "color": "#627172",
                          "marginTop": "10px"}),
            html.Div(html.Button(
                "Registrar y escanear", id="btn_registrar_dominio", n_clicks=0,
                style={"display": "block", "margin": "10px auto",
                       "padding": "10px 20px", "backgroundColor": "#3498db",
                       "color": "white", "border": "none",
                       "borderRadius": "5px", "cursor": "pointer"},
            )),
        ],
    )
