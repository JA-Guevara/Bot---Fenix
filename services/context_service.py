from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

@dataclass
class ContextoEjecucion:
    cuentas: List[Dict[str, Any]]
    fecha_inicio: datetime
    fecha_fin: datetime
    fecha_inicio2: str
    fecha_fin2: str
    mes: str
    banco: str
    base_dir: str
    rutas_por_cuenta: Dict[str, str]
    dia_inicio: str
    dia_fin: str

    def to_dict(self):
        return {
            "cuentas": self.cuentas,
            "fecha_inicio": self.fecha_inicio,
            "fecha_fin": self.fecha_fin,
            "fecha_inicio2": self.fecha_inicio2,
            "fecha_fin2": self.fecha_fin2,
            "mes": self.mes,
            "banco": self.banco,
            "base_dir": self.base_dir,
            "rutas_por_cuenta": self.rutas_por_cuenta,
            "dia_inicio": self.dia_inicio,
            "dia_fin": self.dia_fin
        }
