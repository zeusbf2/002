import streamlit as st
st.set_page_config(page_title="Visor ISV", layout="wide")


import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from paginas.home import mostrar_home
from paginas.isv_mejorado import mostrar_isv
from paginas.ruta_3d import mostrar_ruta_3d
from paginas.todas_rutas_isv import todas_rutas_isv

# Selector de página en la parte superior
pagina = st.sidebar.selectbox("Selecciona una página", ["Home", "ISV Mejorado", "Ruta 3D"])

# Mostrar el contenido según la página seleccionada
if pagina == "Home":
    mostrar_home()
elif pagina == "ISV Mejorado":
    mostrar_isv()
elif pagina == "Ruta 3D":
    mostrar_ruta_3d()
elif pagina == "Todas las rutas ISV":
    mostrar_todas_rutas_isv()
