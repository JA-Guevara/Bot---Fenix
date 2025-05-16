import os
import pandas as pd
from utils.config import RUTA_EXCEL

def obtener_cuentas_por_banco(nombre_banco: str) -> list[dict]:

    if not os.path.exists(RUTA_EXCEL):
        raise FileNotFoundError(f"❌ El archivo Excel no existe: {RUTA_EXCEL}")

    try:
        df = pd.read_excel(RUTA_EXCEL, sheet_name="CUENTAS")
        df.columns = [col.upper().strip() for col in df.columns]

        if "BANCO" not in df.columns:
            raise ValueError("❌ La hoja 'CUENTAS' debe tener una columna 'BANCO'.")

        filtro = df["BANCO"].str.upper().str.strip() == nombre_banco.upper()
        
        df_filtrado = df[filtro].fillna("").infer_objects(copy=False)
        cuentas = df_filtrado.to_dict("records")


        if not cuentas:
            raise ValueError(f"⚠️ No se encontraron cuentas para el banco: {nombre_banco.upper()}")

        return cuentas

    except Exception as e:
        raise RuntimeError(f"❌ Error al leer cuentas desde Excel: {e}")
