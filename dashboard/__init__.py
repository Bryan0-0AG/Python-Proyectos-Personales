import dash
from dashboard.layout import crear_layout
from dashboard.callbacks import registrar_callbacks
from dashboard.chatbot import registrar_chatbot_callbacks   # ← NUEVO


def crear_app() -> dash.Dash:
    app = dash.Dash(__name__)
    app.layout = crear_layout()
    registrar_callbacks(app)
    registrar_chatbot_callbacks(app)                        # ← NUEVO
    return app
