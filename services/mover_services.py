import os
import shutil

def mover_y_renombrar_archivo(origen_descarga: str, nuevo_nombre: str, destino: str) -> str:
    if not os.path.exists(origen_descarga):
        raise FileNotFoundError(f"❌ Ruta de descarga no encontrada: {origen_descarga}")

    os.makedirs(destino, exist_ok=True)
    archivos = sorted(
        [f for f in os.listdir(origen_descarga) if f.endswith((".xls", ".xlsx"))],
        key=lambda x: os.path.getctime(os.path.join(origen_descarga, x)),
        reverse=True
    )

    if not archivos:
        raise FileNotFoundError("❌ No se encontró ningún archivo Excel descargado.")

    origen_completo = os.path.join(origen_descarga, archivos[0])
    destino_final = os.path.join(destino, nuevo_nombre)

    shutil.move(origen_completo, destino_final)
    return destino_final
