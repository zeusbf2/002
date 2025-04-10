import streamlit as st
st.set_page_config(page_title="Visor ISV", layout="wide")
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from paginas.home import mostrar_home
from paginas.isv_mejorado import mostrar_isv

# Menú lateral
st.sidebar.title("Navegación")
pagina = st.sidebar.selectbox("Selecciona una página", ["Home", "ISV Mejorado"])

if pagina == "Home":
    mostrar_home()
elif pagina == "ISV Mejorado":
    mostrar_isv()
