import os
from dotenv import load_dotenv
import json

load_dotenv()

PERIODO_DESCARGA = os.getenv("PERIODO_DESCARGA", "mensual")  # por defecto mensual
QUINCENA = os.getenv("QUINCENA") 
RUTA_EXCEL = os.getenv("RUTA_EXCEL")
BASE_DIR = os.getenv("BASE_DIR")

def get_credentials(bank_name: str):
    upper = bank_name.upper()
    
    credentials = {
        "url": os.getenv(f"{upper}_URL"),
        "ruc": os.getenv(f"{upper}_RUC"),
        "user": os.getenv(f"{upper}_USER"),
        "password": os.getenv(f"{upper}_PASS"),
    }

    if upper == "GNB":
        credentials["user2"] = os.getenv(f"{upper}_USER2")

    return credentials

def load_flow(bank_name):
    with open(f"flows/{bank_name}.json", "r", encoding="utf-8") as file:
        return json.load(file)

def load_selectors():

    return {
        "continental": {
            "step_1": {
                "companies_checkbox": "input[name='Empresas']",
                "ruc_input": '#docIdentidad',
                "user_input": '#docIdentidad2',
                "password_input": "#clave",
                "login_button": '#ingresar_btn',
            },
            "step_2": {
                "button_informes": "a#\\32 77",
                "button_cuentas": "a#\\33 11",
                
                "cuenta_input_selector" : 'input[aria-controls="bs-select-1"]',
                "periodo_input_selector" : 'input[aria-controls="bs-select-2"]',
                "cuenta_dropdown_button": "button[data-id='cuenta']",
                "periodo_dropdown_button": "button[data-id='fecha']",
                

            },
            "step_3": {
                "select_fecha_inicio": "#FechaDesde",
                "select_fecha_fin": "#FechaHasta",
                "excel_export_button": "button#btnVerExtractoExcel"
            },
            "step_4": {
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
                "button_products": "a:has-text('Productos')",
                "list_selector": "body > div.page-container > div > div.content-wrapper",
                "action_button_selector": "button.btn.btn-primary",
                "action_button_text": "Ver extracto",    
                
            },
            
            "step_3": {
                "select_mes"   : "#form-content > div.row > div.form-group.col-md-2 > span > span.selection > span",
                "select_inicio": "#extracto-pdf > div:nth-child(5) > span > span.selection > span",
                "select_fin": "#extracto-pdf > div:nth-child(7) > span > span.selection > span",
                "input_field": "body > span > span > span.select2-search.select2-search--dropdown > input",
                "excel_export_button": "#extracto-pdf > div.col-md-7 > div > div:nth-child(2) > button",
            },
            "step_4": {
                "menu_button": '#navbar-mobile .dropdown-toggle',
                "logout_button": '#navbar-mobile > ul > li > ul > li:nth-child(4) > a'
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
                "list_selector": "div.row.product-list",
                "moneda_selector": "div.currency-code > span",
                "tipo_selector": "div.product-details > div:nth-child(1)",
                "cuenta_selector": "div.font-weight-bold > span",
                "button_cuentas": "div.menu-home[onclick*='/sudamerisweb/home']"
            },
            "step_3": {
                "select_mes" : "select#periodo",
                "select_formato":  "select#fileType",
                "excel_export_button": "span#downloadFile",
            },
            "step_4": {
                "logout_button": 'div.logout'
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
            },
            "step_4": {
                "logout_button": "div#rwb_header_user_box_salir"
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
                "button_cuentas": 'a[href="/atlasdigital/account/list"]',
                
                "list_selector": 'div[class^="_secctionCardClassic_"]',
                "action_button_selector": "div[class^=\"_showMovementsText_\"]",
                "action_button_text": "ver movimientos"

            },
            "step_3": {
                
                "select_mes"   : 'button[role="combobox"].text-principal',
                "button_select_inicio": "button[aria-haspopup='dialog']:nth-of-type(1)",
                "button_select_fin": "button[aria-haspopup='dialog']:nth-of-type(2)",
                "calendar_input": "#radix-\:r19m\: > div",
                "donwload_button": "button.bg-principal.border-2.text-primary-foreground.px-4.py-2.w-full.md\\:w-28.text-xs.h-7",
                "excel_export_button": 'button:has(img[src*="xls_icon.png"])',
                "back_button" : 'button.bg-principal.text-white.w-36:has-text("VOLVER")',

            },
            "step_4": {
                "logout_button": "div.flex.justify-center.items-center.gap-2 span.cursor-pointer",
                "confirm_logout_button": "button:has-text('Aceptar')"
            }
        },
        
        "gnb": {
            "step_1": {
                "client_access_button": '#logCliente',
                "empresa_radio": "label[for='rCompany']",
                "ruc_input": "#ruc",
                "user_input": "#documentNumber",    
                "user2_input": "#access-username",  
                "password_input": "#access-pin",
                "login_button": "#bSubmit",
                "login_button2": "#btnLogin"        
            },
            "step_2": {
                "button_cuentas_ahorros": "span.enlace:has-text('Cuentas y Ahorro')",
                "list_selector": "td.first.product.cardNumTip.yaguareteEvent div:first-child em",
                },
            "step_3": {
               "button_estracto": "#tabs_OperativasConsultasextractos",
               "button_desplegar_fecha": 'h3.dateStatement:has-text("Fecha")',
               "contenedor_fecha": "#slideQueryDate",
               
               "select_inicio": "#fechaDesdeStatement",
               "select_fin": "#fechaHastaStatement",
               "excel_export_button": "#botonDescargaExcel",
                             
               "without_movements": 'section.container-modal.warning',
               "button_aceptar": '#errorModal[style*="display: block"] button#errorAccept',
    
            },
            "step_4": {
                "logout_button": '#btnDesconectar.c-botones-generico[role="button"]',
                "confirm_logout_button": "#logout-disconect.btn-si"
            }
        }

    }
