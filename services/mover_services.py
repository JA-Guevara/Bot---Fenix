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

    archivo_original = archivos[0]
    origen_completo = os.path.join(origen_descarga, archivo_original)

    # Obtener la extensión real del archivo descargado
    _, extension_real = os.path.splitext(archivo_original)

    # Usar esa extensión para el nuevo nombre
    nuevo_nombre_con_ext = f"{os.path.splitext(nuevo_nombre)[0]}{extension_real}"
    destino_final = os.path.join(destino, nuevo_nombre_con_ext)

    shutil.move(origen_completo, destino_final)
    return destino_final
