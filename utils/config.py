import os
from dotenv import load_dotenv
import json


# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Tiempo de espera general
TIMEOUT = int(os.getenv("TIMEOUT", 120))


def get_environment():
    return os.getenv("ENVIRONMENT", "development")

def get_credentials(bank_name: str):
    
    upper = bank_name.upper()
    return {
        "url": os.getenv(f"{upper}_URL"),
        "ruc": os.getenv(f"{upper}_RUC"),
        "user": os.getenv(f"{upper}_USER"),
        "password": os.getenv(f"{upper}_PASS"),
    }


def load_flow(bank_name):
    with open(f"flows/{bank_name}.json", "r", encoding="utf-8") as file:
        return json.load(file)


def load_selectors():

    return {
        "continental": {
            "step_1": {
                "online_banking": '#navbarsDefault > ul > li:nth-child(6) > button',
                "companies_checkbox": 'input[name="Empresas"]',
                "ruc_input": '#docIdentidad',
                "user_input": '#docIdentidad2',
                "password_input": "#clave",
                "login_button": '#ingresar_btn',
            },
            "step_2": {
            },
            "step_3": {
                "menu_button": "a#menu-user:has(span.fa-cog)",
                "logout_button": "a:has(.fa-sign-out)"

            }
        },

        "basa": {
            "step_1": {
                "ruc_input": '#solid-justified-tab1 > form > div:nth-child(1) > div > div.col-md-7 > input',
                "user_input": '#solid-justified-tab1 > form > div:nth-child(2) > div > div.col-md-7 > input',
                "login_button": 'button[type="submit"].btn.btn-primary',
                "password_virtual_selector": "[data-valor]"
            },
            "step_2": {
            },
            "step_3": {
                "menu_button": 'a.dropdown-toggle[data-toggle="dropdown"]',
                "logout_button": 'a.bttn-logout[href="/be/logout"]'
            }
        },

        "sudameris": {
            "step_1": {
                "open_login" : "a[href*='login']",
                "user_input": "#userValue",
                "password_input": "#pass-input",
                "login_button": 'input[type="submit"][value="INGRESAR"]'
            },
            "step_2": {
            },
            "step_3": {
            }
        },
        
        "itau": {
            "step_1": {
                "segment_selector": "#segmento",
                "ruc_input": "#ruc",
                "user_input": "#cuenta_empresa",
                "login_button": "#vprocesar",
                "password_virtual_selector": "#teclado_borrar",
                "access_button": "#rwb_login_Siguiente"

            },
            "step_2": {
            },
            "step_3": {
                "logout_button": "#rwb_header_user_box_salir"
            }
        },
        
        "atlas": {
            "step_1": {
                "user_input": "input#document",
                "password_input": "input#password",
                "login_button": 'button[type="submit"]:has-text("INGRESAR")',
                "daniel_radio_button": 'role=radio[name="DANIEL BERNARDO MEZA GONZALEZ"]',
                "fenix_radio_button": 'role=radio[name="FENIX S.A. DE SEGUROS Y REASEGUROS"]'
            },
            "step_2": {
            },
            "step_3": {
                "logout_button": "div.flex.justify-center.items-center.gap-2 span.cursor-pointer",
                "confirm_logout_button": "button:has-text('Aceptar')",
            }
        }
    }
