import streamlit as st

# === Menú lateral ===
st.sidebar.title("Navegación")
pagina = st.sidebar.selectbox("Selecciona una página", ["Home", "ISV Mejorado"])  # 👈 Home es el valor por defecto

# === Importación de páginas ===
from paginas.home import mostrar_home
from paginas.isv_mejorado import mostrar_isv

# === Cargar la página correspondiente ===
if pagina == "Home":
    mostrar_home()
elif pagina == "ISV Mejorado":
    mostrar_isv()
