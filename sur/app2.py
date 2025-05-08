import streamlit as st
st.set_page_config(page_title="Visor ISV", layout="wide")


import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from paginas.home import mostrar_home
from paginas.isv_mejorado import mostrar_isv
from paginas.isv_real import mostrar_isvr
from paginas.ruta_3d import mostrar_ruta_3d
from paginas.mostrar_todas_rutas_isv import mostrar_todas_rutas_isv
from paginas.mostrar_todas_rutas_isvr import mostrar_todas_rutas_isvr

# Selector de página en la parte superior
pagina = st.sidebar.selectbox("Selecciona una página", ["Home", "ISV Mejorado", "ISV Real", "Ruta 3D", "Global ISV Mejorado", "Global ISV Real"])

# Mostrar el contenido según la página seleccionada
if pagina == "Home":
    mostrar_home()
elif pagina == "ISV Mejorado":
    mostrar_isv()
elif pagina == "ISV Real":
    mostrar_isvr()    
elif pagina == "Ruta 3D":
    mostrar_ruta_3d()
elif pagina == "Global ISV Mejorado":
    mostrar_todas_rutas_isv()
elif pagina == "Global ISV Real":
    mostrar_todas_rutas_isvr()
