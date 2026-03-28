"""
dashboard/chatbot.py
Módulo del asistente RADAR AI — integrado con Claude API.
"""
import os
import requests
from dash import html, dcc, Input, Output, State, callback_context

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """Eres RADAR, un asistente experto en ciberseguridad TLS integrado en un dashboard de auditoría.
Ayudas a equipos técnicos a interpretar resultados de escaneos TLS y tomar decisiones de remediación.

Reglas de respuesta:
- Responde SIEMPRE en español, de forma clara y concisa (máximo 4 líneas).
- Usa emojis de semáforo para criticidad: 🔴 CRÍTICO, 🟠 ALTO, 🟡 MEDIO, 🟢 BAJO/OK.
- Si te pegan datos de un escaneo, analízalos y da recomendaciones concretas.

Conocimiento base:
- TLS 1.0 y 1.1: obsoletos, vulnerables a POODLE y BEAST → deshabilitar de inmediato.
- TLS 1.2: aceptable solo con cifrados fuertes (AES-GCM) → migrar a 1.3 a largo plazo.
- TLS 1.3: versión recomendada, máxima seguridad → mantener habilitada.
- HTTPS NO es sinónimo de seguridad: el protocolo puede estar desactualizado.
- Certificados vencidos o por vencer son riesgos críticos operativos.
- Cifrados inseguros: RC4, DES, 3DES, MD5, NULL, EXPORT.
- Cifrados moderados: AES128, SHA1.
- Cifrados seguros: AES256, CHACHA20, SHA256.
"""


def _llamar_claude(historial: list) -> str:
    if not ANTHROPIC_API_KEY:
        return "⚠️ Configura la variable ANTHROPIC_API_KEY para activar el asistente."
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 512,
                "system": SYSTEM_PROMPT,
                "messages": historial,
            },
            timeout=15,
        )
        return r.json()["content"][0]["text"]
    except requests.Timeout:
        return "⏱️ La consulta tardó demasiado. Intenta de nuevo."
    except Exception as e:
        return f"❌ Error: {e}"


# ── Layout ─────────────────────────────────────────────────────────────────────

def seccion_chatbot() -> html.Div:
    """Bloque del chatbot listo para insertar en el layout principal."""
    return html.Div([
        html.Hr(style={"margin": "40px 20px 20px"}),
        html.Div([
            # Encabezado
            html.Div([
                html.Span("🛰️", style={"fontSize": "24px"}),
                html.H3("RADAR AI — Asistente de Seguridad TLS",
                        style={"margin": "0 0 0 10px", "color": "#2c3e50",
                               "fontFamily": "Arial", "fontSize": "18px"}),
            ], style={"display": "flex", "alignItems": "center",
                      "marginBottom": "6px"}),

            html.P("Pregunta sobre los resultados, qué significa un riesgo o cómo remediarlo.",
                   style={"fontFamily": "Arial", "color": "#7f8c8d",
                          "fontSize": "13px", "margin": "0 0 14px"}),

            # Historial visual
            html.Div(
                id="chat_historial",
                children=[_burbuja_radar(
                    "¡Hola! Soy tu asistente TLS. Pregúntame qué significa "
                    "un riesgo CRÍTICO, cómo deshabilitar TLS 1.0, o pégame "
                    "los datos de un escaneo para analizarlos."
                )],
                style={
                    "height": "280px", "overflowY": "auto",
                    "background": "#f8f9fa", "borderRadius": "10px",
                    "padding": "12px", "marginBottom": "12px",
                    "border": "1px solid #dee2e6",
                },
            ),

            # Input + botones
            html.Div([
                dcc.Input(
                    id="chat_input", type="text",
                    placeholder="Escribe tu pregunta sobre TLS...",
                    n_submit=0,
                    style={"flex": "1", "padding": "10px 14px",
                           "borderRadius": "8px", "border": "1px solid #ced4da",
                           "fontFamily": "Arial", "fontSize": "14px"},
                ),
                html.Button("Enviar ↗", id="chat_btn_enviar", n_clicks=0,
                            style=_estilo_btn("#2980b9")),
                html.Button("🗑 Limpiar", id="chat_btn_limpiar", n_clicks=0,
                            style=_estilo_btn("#95a5a6")),
            ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),

            # Store con historial de la API (formato messages)
            dcc.Store(id="chat_store", data=[]),

        ], style={
            "background": "white", "borderRadius": "12px",
            "padding": "24px", "margin": "0 20px 40px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
        }),
    ])


# ── Callbacks ──────────────────────────────────────────────────────────────────

def registrar_chatbot_callbacks(app) -> None:
    """Registra los callbacks del chatbot en la app Dash."""

    @app.callback(
        Output("chat_historial", "children"),
        Output("chat_store",     "data"),
        Output("chat_input",     "value"),

        Input("chat_btn_enviar",  "n_clicks"),
        Input("chat_input",       "n_submit"),
        Input("chat_btn_limpiar", "n_clicks"),

        State("chat_input",    "value"),
        State("chat_historial","children"),
        State("chat_store",    "data"),
        prevent_initial_call=True,
    )
    def manejar_chat(_, __, ___, texto, historial_ui, historial_api):
        triggered = callback_context.triggered_id

        # Limpiar
        if triggered == "chat_btn_limpiar":
            return [_burbuja_radar("Chat reiniciado. ¿En qué te puedo ayudar?")], [], ""

        # Enviar mensaje vacío → no hacer nada
        if not texto or not texto.strip():
            return historial_ui, historial_api, ""

        texto = texto.strip()
        historial_api = historial_api or []
        historial_api.append({"role": "user", "content": texto})

        respuesta = _llamar_claude(historial_api)
        historial_api.append({"role": "assistant", "content": respuesta})

        nuevas_burbujas = [
            _burbuja_usuario(texto),
            _burbuja_radar(respuesta),
        ]
        return (historial_ui or []) + nuevas_burbujas, historial_api, ""


# ── Helpers visuales ───────────────────────────────────────────────────────────

def _burbuja_radar(texto: str) -> html.Div:
    return html.Div([
        html.Span("🛰️ RADAR: ",
                  style={"fontWeight": "bold", "color": "#2980b9"}),
        html.Span(texto),
    ], style={"background": "#eaf4fb", "borderRadius": "8px",
              "padding": "10px 14px", "marginBottom": "8px",
              "fontFamily": "Arial", "fontSize": "13px"})


def _burbuja_usuario(texto: str) -> html.Div:
    return html.Div([
        html.Span("👤 Tú: ",
                  style={"fontWeight": "bold", "color": "#27ae60"}),
        html.Span(texto),
    ], style={"background": "#eafaf1", "borderRadius": "8px",
              "padding": "10px 14px", "marginBottom": "8px",
              "fontFamily": "Arial", "fontSize": "13px"})


def _estilo_btn(color: str) -> dict:
    return {
        "backgroundColor": color, "color": "white",
        "border": "none", "borderRadius": "8px",
        "padding": "10px 18px", "cursor": "pointer",
        "fontFamily": "Arial", "fontWeight": "bold",
    }
