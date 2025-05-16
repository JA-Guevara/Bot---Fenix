# application/actions/strategy_factory.py

from application.actions.basa_actions import BasaActions
from application.actions.sudameris_actions import SudamerisActions
from application.actions.continental_actions import ContinentalActions
from application.actions.atlas_actions import AtlasActions
from application.actions.gnb_actions import GnbActions
from application.actions.itau_actions import ItauActions

def get_strategy(nombre_banco, credentials, selectors, flow, contexto):
    banco = nombre_banco.lower()

    if banco == "basa":
        return BasaActions(credentials, selectors, flow, contexto)
    elif banco == "sudameris":
        return SudamerisActions(credentials, selectors, flow, contexto)
    elif banco == "continental":
        return ContinentalActions(credentials, selectors, flow, contexto)
    elif banco == "atlas":
        return AtlasActions(credentials, selectors, flow, contexto)
    elif banco == "gnb":
        return GnbActions(credentials, selectors, flow, contexto)
    elif banco == "itau":
        return ItauActions(credentials, selectors, flow, contexto)
    else:
        raise ValueError(f"❌ No hay estrategia definida para el banco: {nombre_banco}")

def get_bank_executor(nombre_banco, credentials, selectors, flow, contexto):
    return get_strategy(nombre_banco, credentials, selectors, flow, contexto)
