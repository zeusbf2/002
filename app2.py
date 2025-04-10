import streamlit as st
st.set_page_config(page_title="Visor ISV", layout="wide")

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from paginas.home import mostrar_home
from paginas.isv_mejorado import mostrar_isv

# Selector de página en la parte superior
st.title("🧭 Visor ISV")
pagina = st.selectbox("Selecciona una página", ["Home", "ISV Mejorado"])

# Mostrar el contenido según la página seleccionada
if pagina == "Home":
    mostrar_home()
elif pagina == "ISV Mejorado":
    mostrar_isv()
