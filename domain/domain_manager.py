from scanner.tls_scanner import escanear_tls
from storage.file_manager import (
    agregar_dominio_json,
    eliminar_dominio_json,
    eliminar_dominio_csv,
    upsert_dominio_csv,
)

def _build_row(dominio: str, scan: dict) -> dict:
    """Convierte el resultado del scanner al formato de fila del CSV."""
    return {
        "Dominio":                   dominio,
        "Fecha scan":              scan["scan_date"],
        "TLS":               scan["version"],
        "Vence en":            scan["days_left"],
        "Emisor": scan["emisor"],
        "Cifrado":      scan["cipher_name"],
        "Riesgo":                    scan["risk"],
        "Observaciones":             scan["observaciones"],
    }


def escanear_y_registrar(dominio: str) -> dict:
    """
    Escanea el dominio y actualiza (o inserta) su fila en el CSV.
    Devuelve el resultado del scan.
    """
    scan = escanear_tls(dominio)
    upsert_dominio_csv(dominio, _build_row(dominio, scan))
    return scan


def registrar_dominio(dominio: str) -> bool:
    """
    Añade el dominio al JSON y lanza el primer escaneo.
    Devuelve False si el dominio ya existía.
    """
    es_nuevo = agregar_dominio_json(dominio)
    if es_nuevo:
        escanear_y_registrar(dominio)
    return es_nuevo


def eliminar_dominio(dominio: str) -> None:
    """Elimina el dominio del JSON y del CSV."""
    eliminar_dominio_json(dominio)
    eliminar_dominio_csv(dominio)
