from datetime import datetime, timedelta
import os

MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

def generar_periodo():
    hoy = datetime.today()
    periodo = os.getenv("PERIODO_DESCARGA", "MENSUAL").upper()
    quincena = os.getenv("QUINCENA", "1")

    # 🟡 Ajustamos al primer día del mes anterior
    primer_dia_mes_actual = hoy.replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
    fecha_base = ultimo_dia_mes_anterior.replace(day=1)

    if periodo == "QUINCENAL":
        if quincena == "1":
            fecha_inicio = fecha_base
            fecha_fin = fecha_base.replace(day=15)
        else:
            fecha_inicio = fecha_base.replace(day=16)
            siguiente_mes = fecha_base.replace(day=28) + timedelta(days=4)
            ultimo_dia = (siguiente_mes - timedelta(days=siguiente_mes.day)).day
            fecha_fin = fecha_base.replace(day=ultimo_dia)
    else:
        fecha_inicio = fecha_base
        siguiente_mes = fecha_base.replace(day=28) + timedelta(days=4)
        fecha_fin = siguiente_mes - timedelta(days=siguiente_mes.day)

    # Aseguramos que fecha_fin sea el último día del mes anterior
    fecha_fin = fecha_fin.replace(day=ultimo_dia_mes_anterior.day)

    nombre_mes = f"{MESES_ES[fecha_fin.month - 1]} {fecha_fin.year}"

    return fecha_inicio, fecha_fin, nombre_mes
