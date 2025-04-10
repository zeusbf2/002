import streamlit as st
import sys
import os

# Agrega el path del directorio actual (necesario en Streamlit Cloud)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from paginas.home import mostrar_home
from paginas.isv_mejorado import mostrar_isv

# Configuración de la app
st.set_page_config(page_title="Visor ISV", layout="wide")

# Menú lateral
st.sidebar.title("Navegación")
pagina = st.sidebar.selectbox("Selecciona una página", ["Home", "ISV Mejorado"])

# Mostrar página correspondiente
if pagina == "Home":
    mostrar_home()
elif pagina == "ISV Mejorado":
    mostrar_isv()
