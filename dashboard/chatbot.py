"""
dashboard/chatbot.py
Asistente RADAR — sin API externa.
Responde preguntas sobre TLS usando lógica de reglas local.
"""
from dash import html, dcc, Input, Output, State, callback_context
import re


# ── Motor de respuestas local ──────────────────────────────────────────────────

_BASE = [
    # Saludos
    (r"hola|buenos|buenas|saludos|hey",
     "🛰️ ¡Hola! Soy RADAR, tu asistente TLS. Puedes preguntarme sobre versiones TLS, "
     "cifrados, certificados, niveles de riesgo o cómo remediar un problema específico."),

    # TLS 1.0
    (r"tls\s*1\.0|tls10",
     "🔴 CRÍTICO — TLS 1.0 está obsoleto desde 2020.\n"
     "Vulnerable a POODLE y BEAST. Acción: deshabilítalo de inmediato en la "
     "configuración del servidor (Nginx/Apache/IIS) y fuerza mínimo TLS 1.2."),

    # TLS 1.1
    (r"tls\s*1\.1|tls11",
     "🔴 CRÍTICO — TLS 1.1 también está deprecado.\n"
     "Comparte vulnerabilidades con TLS 1.0. Migra a TLS 1.2 o 1.3 cuanto antes. "
     "Los navegadores modernos ya lo rechazan por defecto."),

    # TLS 1.2
    (r"tls\s*1\.2|tls12",
     "🟡 MEDIO — TLS 1.2 es aceptable pero no ideal.\n"
     "Solo es seguro con cifrados AES-GCM y SHA-256. Evita RC4, 3DES y SHA-1. "
     "Planifica migración a TLS 1.3 a mediano plazo."),

    # TLS 1.3
    (r"tls\s*1\.3|tls13",
     "🟢 OK — TLS 1.3 es la versión recomendada actualmente.\n"
     "Elimina cifrados inseguros por diseño, soporta Perfect Forward Secrecy "
     "y reduce la latencia del handshake. Mantén esta versión habilitada."),

    # Riesgo CRÍTICO
    (r"riesgo cr[ií]tico|cr[ií]tico",
     "🔴 CRÍTICO — Requiere acción inmediata.\n"
     "Causas comunes: certificado vencido, TLS 1.0/1.1 activo, "
     "cifrados NULL o EXPORT habilitados. Prioriza estos dominios sobre cualquier otro."),

    # Riesgo ALTO
    (r"riesgo alto|nivel alto",
     "🟠 ALTO — Atención urgente recomendada.\n"
     "Suele indicar: certificado próximo a vencer (<30 días), "
     "uso de SHA-1, cifrados débiles como 3DES o RC4. "
     "Programa la remediación esta semana."),

    # Riesgo MEDIO
    (r"riesgo medio|nivel medio",
     "🟡 MEDIO — Planifica corrección a corto plazo.\n"
     "Típicamente: TLS 1.2 con cifrados AES-128, certificado con 30-60 días restantes. "
     "No es urgente pero debe resolverse antes de convertirse en ALTO."),

    # Riesgo BAJO
    (r"riesgo bajo|nivel bajo",
     "🟢 BAJO — Configuración aceptable.\n"
     "El dominio usa TLS 1.2 o 1.3 con cifrados fuertes y certificado vigente. "
     "Revísalo en el próximo ciclo de auditoría."),

    # Certificado vencido
    (r"certificado venc|expirado|caducado|vence en 0|vence en -",
     "🔴 CRÍTICO — Certificado vencido.\n"
     "El sitio mostrará error de seguridad a todos los usuarios. "
     "Renueva el certificado de inmediato. "),

    # Certificado por vencer
    (r"(vence en|vencimiento|expira).{0,20}(d[ií]as|días)|pr[oó]ximo a vencer|renovar certificado",
     "🟠 ALTO — Certificado próximo a vencer.\n"
     "Renueva con al menos 14 días de anticipación para evitar interrupciones. "
     "Configura renovación automática con certbot o tu proveedor de certificados."),

    # Cifrados inseguros
    (r"rc4|des\b|3des|null cipher|export cipher|cifrado.{0,15}inseguro",
     "🔴 CRÍTICO — Cifrado inseguro detectado.\n"
     "RC4, DES, 3DES, NULL y EXPORT están completamente rotos criptográficamente. "
     "Deshabílitalos en la configuración SSL del servidor y usa "
     "solo AES-256-GCM o CHACHA20-POLY1305."),

    # Cifrados seguros
    (r"aes.?256|chacha20|cifrado.{0,15}seguro|cifrado fuerte",
     "🟢 OK — Cifrado fuerte.\n"
     "AES-256-GCM y CHACHA20-POLY1305 son los estándares recomendados. "
     "Asegúrate de combinarlos con TLS 1.3 para máxima seguridad."),

    # HTTPS
    (r"https|http\b",
     "⚠️ Aclaración importante:\n"
     "HTTPS NO garantiza seguridad por sí solo. Un sitio puede usar HTTPS "
     "con TLS 1.0 o cifrados rotos. Siempre verifica la versión TLS "
     "y los cifrados habilitados, no solo el candado del navegador."),

    # Nginx
    (r"nginx",
     "🛠️ Configuración recomendada para Nginx:\n"
     "ssl_protocols TLSv1.2 TLSv1.3;\n"
     "ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;\n"
     "ssl_prefer_server_ciphers off;\n"
     "add_header Strict-Transport-Security 'max-age=31536000';"),

    # Remediación general
    (r"qu[eé] hago|c[oó]mo (remediar|arreglar|solucionar|corregir)|remediaci[oó]n|pasos",
     "📋 Pasos generales de remediación TLS:\n"
     "1. Deshabilita TLS 1.0 y 1.1 en el servidor.\n"
     "2. Elimina cifrados inseguros (RC4, 3DES, NULL, EXPORT).\n"
     "3. Renueva certificados próximos a vencer.\n"
     "4. Habilita HSTS y OCSP Stapling.\n"
     "5. Re-escanea el dominio para verificar correcciones."),

    # Prioridad
    (r"prioridad|primero|qu[eé] atender|orden",
     "📊 Orden de prioridad recomendado:\n"
     "1. 🔴 Certificados vencidos — afectan disponibilidad inmediata.\n"
     "2. 🔴 TLS 1.0/1.1 activo — riesgo de explotación activa.\n"
     "3. 🔴 Cifrados NULL/EXPORT/RC4 — completamente comprometidos.\n"
     "4. 🟠 Certificados por vencer (<30 días).\n"
     "5. 🟡 TLS 1.2 sin cifrados fuertes."),

    # Estadísticas
    (r"cu[aá]ntos|estad[ií]sticas|resumen|total",
     "📈 Consulta las tarjetas superiores del dashboard: dominios escaneados, "
     "riesgo bajo y dominios que requieren atención. "
     "También puedes usar el filtro por columna en la tabla para ver por nivel de riesgo."),
]


def _responder(texto: str) -> str:
    texto_lower = texto.lower().strip()
    for patron, respuesta in _BASE:
        if re.search(patron, texto_lower):
            return respuesta
    return (
        "🤔 No tengo una respuesta específica para eso.\n"
        "Puedes preguntarme sobre: versiones TLS (1.0, 1.1, 1.2, 1.3), "
        "niveles de riesgo (crítico, alto, medio, bajo), cifrados (RC4, AES, CHACHA20), "
        "certificados vencidos, HSTS, POODLE, BEAST, Nginx, Apache o remediación general."
    )


# ── Layout ─────────────────────────────────────────────────────────────────────

def seccion_chatbot() -> html.Div:
    return html.Div([
        html.Div([
            html.Div(className="cy-corner tl"),
            html.Div(className="cy-corner tr"),
            html.Div(className="cy-corner bl"),
            html.Div(className="cy-corner br"),

            html.Div([
                html.Div([
                    html.Span("🛰️", style={"fontSize": "20px"}),
                    html.Span(" RADAR AI ", style={
                        "fontFamily": "'Orbitron', monospace",
                        "fontSize": "13px", "fontWeight": "700",
                        "letterSpacing": "4px", "color": "#00ffcc",
                        "textShadow": "0 0 8px #00ffcc",
                    }),
                    html.Span("// ASISTENTE DE SEGURIDAD TLS", style={
                        "fontFamily": "'Share Tech Mono', monospace",
                        "fontSize": "10px", "color": "#4a6a8a",
                        "letterSpacing": "2px",
                    }),
                ], style={"display": "flex", "alignItems": "center",
                          "gap": "6px", "marginBottom": "4px"}),

                html.P(
                    "> Consulta sobre riesgos, versiones TLS, cifrados, certificados o remediación.",
                    style={
                        "fontFamily": "'Share Tech Mono', monospace",
                        "fontSize": "11px", "color": "#4a6a8a",
                        "marginBottom": "16px",
                    }
                ),

                html.Div(
                    id="chat_historial",
                    children=[_burbuja_radar(
                        "Sistema en línea. Pregúntame sobre versiones TLS, "
                        "cifrados, certificados o qué hacer con un riesgo específico."
                    )],
                    style={
                        "height": "300px", "overflowY": "auto",
                        "background": "#030310", "borderRadius": "2px",
                        "padding": "14px", "marginBottom": "14px",
                        "border": "1px solid #00ffcc22",
                    },
                ),

                html.Div([
                    dcc.Input(
                        id="chat_input", type="text",
                        placeholder="> introduce consulta...",
                        n_submit=0, className="cy-input",
                        style={"flex": "1"},
                    ),
                    html.Button("↗ ENVIAR", id="chat_btn_enviar", n_clicks=0,
                                className="cy-btn", style={"whiteSpace": "nowrap"}),
                    html.Button("✕ LIMPIAR", id="chat_btn_limpiar", n_clicks=0,
                                className="cy-btn danger", style={"whiteSpace": "nowrap"}),
                ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),

                dcc.Store(id="chat_store", data=[]),

            ], style={"padding": "24px"}),
        ], className="cy-panel", style={"marginBottom": "28px"}),
    ])


# ── Callbacks ──────────────────────────────────────────────────────────────────

def registrar_chatbot_callbacks(app) -> None:

    @app.callback(
        Output("chat_historial", "children"),
        Output("chat_store",     "data"),
        Output("chat_input",     "value"),

        Input("chat_btn_enviar",  "n_clicks"),
        Input("chat_input",       "n_submit"),
        Input("chat_btn_limpiar", "n_clicks"),

        State("chat_input",     "value"),
        State("chat_historial", "children"),
        State("chat_store",     "data"),
        prevent_initial_call=True,
    )
    def manejar_chat(_, __, ___, texto, historial_ui, historial_api):
        triggered = callback_context.triggered_id

        if triggered == "chat_btn_limpiar":
            return [_burbuja_radar("Chat reiniciado. ¿En qué te puedo ayudar?")], [], ""

        if not texto or not texto.strip():
            return historial_ui, historial_api, ""

        texto = texto.strip()
        respuesta = _responder(texto)
        nuevas_burbujas = [_burbuja_usuario(texto), _burbuja_radar(respuesta)]
        return (historial_ui or []) + nuevas_burbujas, historial_api or [], ""


# ── Helpers visuales ───────────────────────────────────────────────────────────

def _burbuja_radar(texto: str) -> html.Div:
    partes = []
    for i, linea in enumerate(texto.split("\n")):
        if i > 0:
            partes.append(html.Br())
        partes.append(linea)
    return html.Div([
        html.Span("🛰️ RADAR: ", style={
            "fontWeight": "bold", "color": "#00ffcc",
            "textShadow": "0 0 6px #00ffcc",
        }),
        html.Span(partes),
    ], style={
        "background": "linear-gradient(135deg, #001a2a, #000d18)",
        "border": "1px solid #00ffcc33", "borderLeft": "3px solid #00ffcc",
        "borderRadius": "2px", "padding": "12px 16px", "marginBottom": "10px",
        "fontFamily": "'Share Tech Mono', monospace", "fontSize": "12px",
        "color": "#c8f0ff", "lineHeight": "1.8",
    })


def _burbuja_usuario(texto: str) -> html.Div:
    return html.Div([
        html.Span("👤 TÚ: ", style={
            "fontWeight": "bold", "color": "#ff00aa",
            "textShadow": "0 0 6px #ff00aa",
        }),
        html.Span(texto),
    ], style={
        "background": "linear-gradient(135deg, #1a0020, #0d0012)",
        "border": "1px solid #ff00aa33", "borderLeft": "3px solid #ff00aa",
        "borderRadius": "2px", "padding": "12px 16px", "marginBottom": "10px",
        "fontFamily": "'Share Tech Mono', monospace", "fontSize": "12px",
        "color": "#c8f0ff", "lineHeight": "1.6",
    })