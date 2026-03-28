import pandas as pd
import dash
from dash import dcc, html, dash_table, Input, Output, State, callback_context
import plotly.express as px
from Scanner import obtener_archivos
from Scanner import registrar_dominio
from Scanner import eliminar_dominio
from Scanner import escaneo_y_registro_dominio


colores_riesgo = {
    "BAJO":    "#2ecc71",
    "MEDIO":   "#f39c12",
    "ALTO":    "#d3721e",
    "CRITICO": "#e74c3c"
}

colores_tabla = {
    "BAJO":    "#a8e6cf",
    "MEDIO":   "#ffd3b6",
    "ALTO":    "#ffaaa5",
    "CRITICO": "#ff8b94"
}

app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Dashboard de Seguridad TLS",
            style={"textAlign": "center", "fontFamily": "Arial",
                   "color": "#2c3e50", "marginBottom": "10px"}),

    html.P("Sistema centralizado de monitoreo de certificados SSL/TLS",
           style={"textAlign": "center", "fontFamily": "Arial",
                  "color": "#7f8c8d", "marginBottom": "30px"}),

    html.Div([
        # div Dominios escaneados
        html.Div([
            html.H2("0", id="dominios_escaneados", style={"margin": "0", "fontSize": "36px"}),
            html.P("Dominios escaneados", style={"margin": "0"})
        ], style={"background": "#3498db", "color": "white", "padding": "20px",
                  "borderRadius": "10px", "textAlign": "center", "flex": "1"}),

        # div Riesgo bajo
        html.Div([
            html.H2("0", id="riesgo_bajo", style={"margin": "0", "fontSize": "36px"}),
            html.P("Riesgo bajo", style={"margin": "0"})
        ], style={"background": "#2ecc71", "color": "white", "padding": "20px",
                  "borderRadius": "10px", "textAlign": "center", "flex": "1"}),

        # div Requieren atención
        html.Div([
            html.H2("0", id="requieren_atencion", style={"margin": "0", "fontSize": "36px"}),
            html.P("Requieren atención", style={"margin": "0"})
        ], style={"background": "#e74c3c", "color": "white", "padding": "20px",
                  "borderRadius": "10px", "textAlign": "center", "flex": "1"}),
    ], style={"display": "flex", "gap": "20px", "marginBottom": "30px",
              "padding": "0 20px"}),
    
    # div Gráficos
    html.Div([
        dcc.Graph(id="fig_torta", style={"flex": "1"}),
        dcc.Graph(id="fig_barras", style={"flex": "2"}),
    ], style={"display": "flex", "gap": "20px", "padding": "0 20px",
              "marginBottom": "30px"}),
    
    # div Información detallada
    html.Div([
        html.H3("Detalle por dominio",
                style={"fontFamily": "Arial", "color": "#2c3e50", "padding-left": "20px"}),
        
        # div BÚSQUEDA y FILTROS
        html.Div([           
            html.Div([ # Búsqueda (izquierda)
                dcc.Input(
                    id="busqueda_texto",
                    type="text",
                    placeholder="buscar por dominio",
                    style={"width": "200px"}
                ),
                dcc.Dropdown(
                    id="busqueda_extension",
                    options=[
                        {"label": ".com", "value": ".com"},
                        {"label": ".org", "value": ".org"},
                        {"label": ".co", "value": ".co"},
                        {"label": ".net", "value": ".net"}
                    ],
                    value=".com",
                    style={"width": "150px"}
                ),
                html.Div(id="rg_resultado")
            ], style={
                "display": "flex",
                "gap": "10px",
                "align-items": "center",
            }),
            
            html.Div([  # Filtros (derecha)
                html.Div([
                    html.Label("Filtrar por columna:"),
                    dcc.Dropdown(
                        id="filtro_columna",
                        options=[
                            {"label": "Riesgo", "value": "Riesgo"},
                            {"label": "Versión TLS", "value": "Version TLS"},
                            {"label": "Protocolo de cifrado", "value": "Protocolo de cifrado"},
                            {"label": "Emisor de certificado TLS", "value": "Emisor de certificado TLS"}
                        ],
                        placeholder="Selecciona una columna",
                        style={"width": "200px"}
                    )
                ], style={"display": "flex", "flex-direction": "column", "gap": "5px"}),

                html.Div([
                    html.Label("Selecciona valor:"),
                    dcc.Dropdown(
                        id="filtro_valor",
                        placeholder="Primero selecciona una columna",
                        style={"width": "200px"}
                    )
                ], style={"display": "flex", "flex-direction": "column", "gap": "5px"}),
            ], style={
                "display": "flex",
                "gap": "20px",
                "align-items": "flex-start",  # para que los labels y dropdowns no se desalineen
            })
        ], style={
            "display": "flex",
            "justify-content": "space-between",  # separación entre izquierda y derecha
            "align-items": "center",
            "padding": "0 20px",
            "margin-bottom": "10px"
        }),
        
        # Tabla con toda la información
        dash_table.DataTable(
            id="tabla_vision_general",
            row_selectable="multi",
            selected_rows=[],
            
            style_cell={"fontFamily": "Arial", "textAlign": "left", "padding": "10px"},
            style_header={"backgroundColor": "#2c3e50", "color": "white", "fontWeight": "bold"},            
            style_table={
                "margin": "0 20px",
                "overflowX": "auto",   # scroll horizontal
                "maxWidth": "98%",    # no se salga de la página
                "overflowY": "auto",    #  scroll vertical
                "maxHeight": "400px",     # límite vertical
            }            
        ),        
        dcc.Store(id="signal_botones_tabla", data={}), # Señal personalizada para controlar los botones de la tabla
        
        # Botones de acciones de la tabla 
        html.Div(
            id="botones_tabla",
            children=[  
            html.Button(
                "Re-escanear dominio(s)",
                id="btn_reescanear",
                n_clicks=0,
                style={
                    "backgroundColor": "#3498db",  # azul
                    "color": "white",
                    "border": "none",
                    "borderRadius": "8px",
                    "padding": "10px 20px",
                    "cursor": "pointer",
                    "fontWeight": "bold",
                    "marginRight": "10px",
                    "transition": "0.2s"
                }
            ),
            html.Button(
                "Eliminar dominio(s)",
                id="btn_eliminar_fila",
                n_clicks=0,
                style={
                    "backgroundColor": "#e74c3c",  # rojo
                    "color": "white",
                    "border": "none",
                    "borderRadius": "8px",
                    "padding": "10px 20px",
                    "cursor": "pointer",
                    "fontWeight": "bold",
                    "transition": "0.2s"
                }
            ),
        ], style={
            "display": "flex",
            "justifyContent": "flex-start",
            "alignItems": "center",
            "margin-top": "15px",
            "margin-left": "14px",
            "gap": "10px"            
        }),
        
        # div Sin resultados de búsqueda / registro de dominios
        html.Div(
            id="sin_resultados_busqueda",
            style={"display": "none"},
            children=[
                html.Br(),
                html.H3(
                    "No se encontraron resultados",
                    style={
                        "textAlign": "center",
                        "color": "#2c3e50",
                        "marginTop": "10px"
                    }
                ),              
                html.Img(
                    src="/assets/sin_resultados.png",
                    style={
                        "display": "block",
                        "margin": "40px auto",
                        "maxWidth": "150px",
                        "width": "100%",
                        "opacity": "0.8"
                    }
                ),
                html.P(
                    "¿Desea registrar y escanear este dominio?",
                    id="mensaje_registro",
                    style={
                        "textAlign": "center",
                        "color": "#627172",
                        "marginTop": "10px"
                    }
                ),
                html.Div(
                    html.Button(
                        "Registrar y escanear",
                        id="btn_registrar_dominio",
                        n_clicks=0,
                        style={
                            "display": "block",
                            "margin": "10px auto",
                            "padding": "10px 20px",
                            "backgroundColor": "#3498db",
                            "color": "white",
                            "border": "none",
                            "borderRadius": "5px",
                            "cursor": "pointer"
                        }
                    )
                )          
            ] 
        )
    ]),
], style={"backgroundColor": "#f8f9fa", "minHeight": "100vh", "paddingBottom": "40px"})


# **\\---CONTROL DEL REGISTRO---//**
def obtener_info_actualizada():
    # Leer el CSV generado por Bryan
    archivoCSV, _ = obtener_archivos()
    df, _ = archivoCSV
    
    conteo_riesgo = df["Riesgo"].value_counts().reset_index()
    conteo_riesgo.columns = ["Riesgo", "Cantidad"]
    fig_torta = px.pie(
        conteo_riesgo,
        names="Riesgo",
        values="Cantidad",
        title="Distribución de riesgos",
        color="Riesgo",
        color_discrete_map=colores_riesgo
    )

    df_validos = df[df["Días restantes"] > 0].copy()
    fig_barras = px.bar(
        df_validos,
        x="Dominio",
        y="Días restantes",
        title="Días hasta vencimiento del certificado",
        color="Riesgo",
        color_discrete_map=colores_riesgo,
        text="Días restantes"
    )
    fig_barras.update_traces(textposition="outside")
    data = {
        "dominios_escaneados": str(len(df)),
        "cantidad_riesgo_bajo": str(len(df[df["Riesgo"] == "BAJO"])),
        "cantidad_requieren_atencion": str(len(df[df["Riesgo"].isin(["ALTO", "CRITICO"])])),
        "fig_torta": fig_torta, 
        "fig_barras": fig_barras,
        "info_tabla_global": 
            {"data": df.to_dict("records"),
            "columns": [{"name": c, "id": c} for c in df.columns]
            }
        }
    return data
# ------------------------------------
@app.callback(
    # ------ registro
    Output("rg_resultado", "children"),
    Output("busqueda_texto", "value"),  # ← limpiamos aquí
    
    # ------ actualizar UI
    Output("dominios_escaneados", "children"),
    Output("riesgo_bajo", "children"),
    Output("requieren_atencion", "children"),
    Output("fig_torta", "figure"),
    Output("fig_barras", "figure"),
    Output("tabla_vision_general", "data"),
    Output("tabla_vision_general", "columns"),
    Output("tabla_vision_general", "style_data_conditional"),
    
    # ------ Botones de la tabla
    Output("signal_botones_tabla", "data"),
    Input("signal_botones_tabla", "data"),
    
    # ------ registro
    Input("btn_registrar_dominio", "n_clicks"), # ← Click
    Input("busqueda_texto", "n_submit"),  # ← Tecla enter
    State("busqueda_texto", "value"),
    State("busqueda_extension", "value"),
)
# ------------------------------------
def control_de_registro(signal_botones_tabla, click, enter, nombre, extension):
    mensaje = ""
    # Registro
    if (click or enter) and nombre:
        dominio = f"{nombre}{extension}"
        registrar_dominio(dominio)
        mensaje = f"Registrado: {dominio}"        
    
    # Re-scaneo
    for dominio in signal_botones_tabla.get("re_scan", []):
        escaneo_y_registro_dominio(dominio)
        
    # Eliminación   
    for dominio in signal_botones_tabla.get("delete", []):
        eliminar_dominio(dominio) 
        
    # Actualización de la tabla    
    data = obtener_info_actualizada()
    return (
        mensaje,
        "",
        data["dominios_escaneados"],
        data["cantidad_riesgo_bajo"],
        data["cantidad_requieren_atencion"],
        data["fig_torta"],
        data["fig_barras"],
        data["info_tabla_global"]["data"],
        data["info_tabla_global"]["columns"],
        [{
            "if": {"filter_query": f'{{Riesgo}} = "{r}"'},
            "backgroundColor": c,
        }for r, c in colores_tabla.items()],
        {}
    )


# **\\---CONTROL DE BOTONES (TABLA)---//**
@app.callback(
    Output("signal_botones_tabla", "data"),
    Output("tabla_vision_general", "selected_rows"),
    Input("btn_reescanear", "n_clicks"),
    Input("btn_eliminar_fila", "n_clicks"),
    State("tabla_vision_general", "data"),
    State("tabla_vision_general", "selected_rows")
)
def acciones_tabla(click_scan, click_delete, data, filas_seleccionadas):
    signal_data = {"re_scan": [], "delete": []}
    if data is None:
        return signal_data, []

    df = pd.DataFrame(data)
    triggered_id = callback_context.triggered_id  # cuál input disparó

    if triggered_id == "btn_reescanear" and filas_seleccionadas:
        filas_validas = [i for i in filas_seleccionadas if i < len(df)]
        signal_data["re_scan"].extend(df.iloc[filas_validas]["Dominio"].tolist())

    elif triggered_id == "btn_eliminar_fila" and filas_seleccionadas:
        filas_validas = [i for i in filas_seleccionadas if i < len(df)]
        signal_data["delete"].extend(df.iloc[filas_validas]["Dominio"].tolist())
        filas_seleccionadas = []  # deseleccionar todo

    # Si cambian las filas seleccionadas sin botón, no hacemos nada
    return signal_data, filas_seleccionadas 
        

# **\\---CONTROL DE BÚSQUEDA---//**
@app.callback(
    Output("tabla_vision_general", "data"),
    Output("mensaje_registro", "children"),
    Output("sin_resultados_busqueda", "style"),
    Output("botones_tabla", "style"),
    Output("tabla_vision_general", "selected_rows"),
    
    Input("busqueda_texto", "value"),
    State("busqueda_extension", "value"),    
)
def filtrar_tabla(texto_buscado, extension):
    archivoCSV, _ = obtener_archivos()
    df, _ = archivoCSV

    estilo_div_noresults = {"display": "none"}
    estilo_div_btntabla = {"display": "block"}

    if texto_buscado: # Si hay resultados
        df = df[df["Dominio"].str.contains(texto_buscado, case=False, na=False)]

    if df.empty and texto_buscado: # No hay resultados
        estilo_div_noresults = {"display": "block"} # Mostramos el div de "sin resultados"
        estilo_div_btntabla = {"display": "none"}
        mensaje = html.Span([
            "¿Desea registrar y escanear este dominio: ",
            html.Span(f"{texto_buscado}{extension}", style={"fontWeight": "bold", "textDecoration": "underline"}),
            "? ", html.Br(),
            html.Span("— Presione Enter o use el siguiente botón:", style={"fontStyle": "italic"})
        ])
    else:
        estilo_div_noresults = {"display": "none"}
        estilo_div_btntabla = {"display": "block"}
        mensaje = ""
    return df.to_dict("records"), mensaje, estilo_div_noresults, estilo_div_btntabla, []


# **\\---FILTRADO---//**
# Obtener valores por columna
@app.callback(
    Output("filtro_valor", "options"),
    Input("filtro_columna", "value")
)
def actualizar_valores(columna_seleccionada):
    if not columna_seleccionada:
        return []
    
    archivoCSV, _ = obtener_archivos()
    df, _ = archivoCSV

    # Obtenemos los valores únicos de la columna
    valores_unicos = df[columna_seleccionada].dropna().unique()
    opciones = [{"label": str(v), "value": v} for v in sorted(valores_unicos)]
    return opciones

# Control de filtrado de tabla
@app.callback(
    Output("tabla_vision_general", "data"),
    Output("tabla_vision_general", "selected_rows"),
    Input("filtro_columna", "value"),
    Input("filtro_valor", "value"),
    prevent_initial_call=True
)
def filtrar_tabla_por_valor(columna, valor):
    archivoCSV, _ = obtener_archivos()
    df, _ = archivoCSV

    if columna and valor:
        df = df[df[columna] == valor]

    return df.to_dict("records"), []


if __name__ == "__main__":
    print("\nAbriendo dashboard en el navegador...")
    print("Ve a: http://127.0.0.1:8050\n")
    app.run(debug=False)