import streamlit as st
from paginas.home import mostrar_home
from paginas.isv_mejorado import mostrar_isv

# Configuración general
st.set_page_config(page_title="Visor de Rutas ISV", layout="wide")

# Menú lateral
st.sidebar.title("Navegación")
pagina = st.sidebar.selectbox("Selecciona una página", ["Home", "ISV Mejorado"])  # 👈 Home por defecto

# Carga la página correspondiente
if pagina == "Home":
    mostrar_home()
elif pagina == "ISV Mejorado":
    mostrar_isv()
