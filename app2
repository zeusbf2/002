import streamlit as st

# Agrega títulos y configuración
st.set_page_config(page_title="Visualizador de Rutas", layout="wide")

# Menú lateral
st.sidebar.title("Navegación")
pagina = st.sidebar.selectbox("Selecciona una página", ["Home", "ISV Mejorado"])

# Lógica de navegación
if pagina == "Home":
    from paginas.home import mostrar_home
    mostrar_home()
elif pagina == "ISV Mejorado":
    from paginas.isv_mejorado import mostrar_isv
    mostrar_isv()
