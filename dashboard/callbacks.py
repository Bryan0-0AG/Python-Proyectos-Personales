import pandas as pd
from dash import Input, Output, State, callback_context

from domain.domain_manager import registrar_dominio, eliminar_dominio, escanear_y_registrar
from storage.file_manager import leer_csv
from dashboard.charts import obtener_info_actualizada


def registrar_callbacks(app):
    """Registra todos los callbacks en la instancia de la app Dash."""

    # ── 1. Registro, re-escaneo y eliminación ─────────────────────────────────
    @app.callback(
        Output("rg_resultado",                    "children"),
        Output("busqueda_texto",                  "value"),
        Output("dominios_escaneados",             "children"),
        Output("riesgo_bajo",                     "children"),
        Output("requieren_atencion",              "children"),
        Output("fig_torta",                       "figure"),
        Output("fig_barras",                      "figure"),
        Output("tabla_vision_general",            "data"),
        Output("tabla_vision_general",            "columns"),
        Output("tabla_vision_general",            "style_data_conditional"),
        Output("signal_botones_tabla",            "data"),

        Input("signal_botones_tabla",             "data"),
        Input("btn_registrar_dominio",            "n_clicks"),
        Input("busqueda_texto",                   "n_submit"),
        State("busqueda_texto",                   "value"),
        State("busqueda_extension",               "value"),
    )
    def control_registro(signal, click, enter, nombre, extension):
        mensaje = ""

        if (click or enter) and nombre:
            dominio = f"{nombre}{extension}"
            registrar_dominio(dominio)
            mensaje = f"Registrado: {dominio}"

        for dominio in signal.get("re_scan", []):
            escanear_y_registrar(dominio)

        for dominio in signal.get("delete", []):
            eliminar_dominio(dominio)

        data = obtener_info_actualizada()
        return (
            mensaje, "",
            data["dominios_escaneados"],
            data["cantidad_riesgo_bajo"],
            data["cantidad_requieren_atencion"],
            data["fig_torta"],
            data["fig_barras"],
            data["tabla_data"],
            data["tabla_columns"],
            data["estilo_tabla"],
            {},
        )

    # ── 2. Botones de la tabla ─────────────────────────────────────────────────
    @app.callback(
        Output("signal_botones_tabla",  "data"),
        Output("tabla_vision_general",  "selected_rows"),

        Input("btn_reescanear",         "n_clicks"),
        Input("btn_eliminar_fila",      "n_clicks"),
        State("tabla_vision_general",   "data"),
        State("tabla_vision_general",   "selected_rows"),
    )
    def acciones_tabla(click_scan, click_delete, data, filas_seleccionadas):
        signal = {"re_scan": [], "delete": []}
        if not data:
            return signal, []

        df = pd.DataFrame(data)
        triggered = callback_context.triggered_id

        if triggered == "btn_reescanear" and filas_seleccionadas:
            validas = [i for i in filas_seleccionadas if i < len(df)]
            signal["re_scan"] = df.iloc[validas]["Dominio"].tolist()

        elif triggered == "btn_eliminar_fila" and filas_seleccionadas:
            validas = [i for i in filas_seleccionadas if i < len(df)]
            signal["delete"] = df.iloc[validas]["Dominio"].tolist()
            filas_seleccionadas = []

        return signal, filas_seleccionadas

    # ── 3. Búsqueda en la tabla ────────────────────────────────────────────────
    @app.callback(
        Output("tabla_vision_general",  "data"),
        Output("mensaje_registro",      "children"),
        Output("sin_resultados_busqueda", "style"),
        Output("botones_tabla",         "style"),
        Output("tabla_vision_general",  "selected_rows"),

        Input("busqueda_texto",         "value"),
        State("busqueda_extension",     "value"),
    )
    def filtrar_tabla(texto, extension):
        df = leer_csv()
        estilo_sin = {"display": "none"}
        estilo_btn = {"display": "block"}
        mensaje    = ""

        if texto:
            df = df[df["Dominio"].str.contains(texto, case=False, na=False)]

        if df.empty and texto:
            from dash import html
            estilo_sin = {"display": "block"}
            estilo_btn = {"display": "none"}
            mensaje = html.Span([
                "¿Desea registrar y escanear este dominio: ",
                html.Span(f"{texto}{extension}",
                          style={"fontWeight": "bold",
                                 "textDecoration": "underline"}),
                "? ", html.Br(),
                html.Span("— Presione Enter o use el siguiente botón:",
                          style={"fontStyle": "italic"}),
            ])

        return df.to_dict("records"), mensaje, estilo_sin, estilo_btn, []

    # ── 4. Filtrado por columna ────────────────────────────────────────────────
    @app.callback( # Obtenemos valores de columna
        Output("filtro_valor", "options"),
        Input("filtro_columna", "value"),
    )
    def actualizar_valores_filtro(columna):
        if not columna:
            return []
        df = leer_csv()
        valores = df[columna].dropna().unique()
        return [{"label": str(v), "value": v} for v in sorted(valores)]

    @app.callback( # Filtramos la tabla
        Output("tabla_vision_general", "data"),
        Output("tabla_vision_general", "selected_rows"),

        Input("filtro_columna", "value"),
        Input("filtro_valor",   "value"),
        prevent_initial_call=True,
    )
    def filtrar_por_valor(columna, valor):
        df = leer_csv()
        if columna and valor:
            df = df[df[columna] == valor]
        return df.to_dict("records"), []