from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

@dataclass
class ContextoEjecucion:
    cuentas: List[Dict[str, Any]]
    fecha_inicio: datetime
    fecha_fin: datetime
    mes: str
    banco: str
    base_dir: str
    rutas_por_cuenta: Dict[str, str]
    dia_inicio: str
    dia_fin: str

    def to_dict(self):
        return self.__dict__
