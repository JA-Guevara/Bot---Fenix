import os
from dotenv import load_dotenv

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


def load_selectors():

    return {
        "continental": {
            "step_1": {
                "start_button": "#inicioSesionBtn",
            },
            "step_2": {
                "user_input": "#usuario",
                "password_input": "#clave",
            },
            "step_3": {
                "submit_button": "#botonEntrar",
            }
        },

        "basa": {
            "step_1": {
                "user_input": "#username",
                "password_input": "#password",
                "login_button": "button[type='submit']",
            }
        },

        "sudameris": {
            "step_1": {
                "open_login": "a[href*='login']"
            },
            "step_2": {
                "user_input": "input[name='usuario']",
                "password_input": "input[name='clave']"
            },
            "step_3": {
                "login_button": "button[type='submit']"
            }
        },
        
        "itau": {
            "step_1": {
                "start_button": "#inicioSesionBtn",
            },
            "step_2": {
                "user_input": "#usuario",
                "password_input": "#clave",
            },
            "step_3": {
                "submit_button": "#botonEntrar",
            }
        },

        "basa": {
            "step_1": {
                "user_input": "#username",
                "password_input": "#password",
                "login_button": "button[type='submit']",
            }
        },
        "atlas": {
            "user_input": "#usuario",
            "password_input": "#password",
            "login_button": "#ingresar",
        }
    }
