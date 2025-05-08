import os
from datetime import datetime, timedelta

def generar_clave_cuenta(cuenta: dict) -> str:
    nro = str(cuenta.get("NROCUENTA", "")).strip().upper()
    tipo = str(cuenta.get("TIPOCUENTA", "")).strip().upper()
    moneda = str(cuenta.get("MONEDA", "")).strip().upper()
    return f"{nro}-{tipo}-{moneda}".replace(" ", "")

def generar_ruta_archivo(

    base_dir: str,
    banco: str,
    tipo_archivo: str,
    tipo_cuenta: str,
    nro_cuenta: str,
    tipo_moneda: str,
    fecha: datetime = None  # ✅ Volver a incluir este argumento
) -> str:
    """
    Genera la ruta en base al mes anterior al actual si no se pasa fecha.
    """
    if fecha is None:
        fecha = (datetime.today().replace(day=1) - timedelta(days=1))

    anio = fecha.strftime("%Y")
    mes = fecha.strftime("%m")

    ruta_banco = os.path.join(base_dir, anio, mes, str(banco).strip().upper())
    os.makedirs(ruta_banco, exist_ok=True)

    tipo_archivo = str(tipo_archivo).strip().upper()
    tipo_cuenta = str(tipo_cuenta).strip().upper()
    nro_cuenta = str(nro_cuenta).strip().upper()
    tipo_moneda = str(tipo_moneda).strip().upper()

    nombre_archivo = f"{tipo_archivo}_{tipo_cuenta}_{nro_cuenta}_{tipo_moneda}.xlsx"
    ruta_completa = os.path.join(ruta_banco, nombre_archivo)

    return ruta_completa
