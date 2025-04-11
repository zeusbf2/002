import streamlit as st
import os
import zipfile
from xml.etree import ElementTree as ET
import pydeck as pdk
import pandas as pd

carpeta_kmz = "tus_kmz"

def extraer_coords_desde_kmz(kmz_path):
    with zipfile.ZipFile(kmz_path, 'r') as z:
        kml_file = next(f for f in z.namelist() if f.endswith('.kml'))
        with z.open(kml_file) as kml:
            tree = ET.parse(kml)
            root = tree.getroot()
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
            coord_text = root.find('.//kml:coordinates', ns).text.strip()
            coords = []
            for line in coord_text.split():
                partes = line.strip().split(",")
                if len(partes) == 3:
                    lon, lat, ele = map(float, partes)
                    coords.append([lon, lat, ele])
            return coords

def mostrar_ruta_3d():
    st.title("🌍 Visualizador 3D de Ruta (Simulado con Pydeck)")

    kmz_files = [f for f in os.listdir(carpeta_kmz) if f.endswith(".kmz")]
    rutas_disponibles = sorted(set(os.path.splitext(f)[0].split("_")[-1] for f in kmz_files))
    ruta_seleccionada = st.selectbox("Selecciona una ruta:", rutas_disponibles)

    if ruta_seleccionada:
        kmz_filename = next((f for f in kmz_files if f.endswith(f"{ruta_seleccionada}.kmz")), None)
        ruta = os.path.join(carpeta_kmz, kmz_filename)

        try:
            coords = extraer_coords_desde_kmz(ruta)
            if not coords:
                st.warning("No se encontraron coordenadas.")
                return

            df = pd.DataFrame(coords, columns=["lon", "lat", "elev"])
            path_data = [{
                'path': coords,
                'name': 'Ruta',
                'color': [0, 102, 204]  # Azul
            }]

            view_state = pdk.ViewState(
                longitude=df["lon"].mean(),
                latitude=df["lat"].mean(),
                zoom=13,
                pitch=60,    # Inclinación
                bearing=30   # Rotación
            )

            layer = pdk.Layer(
                "PathLayer",
                data=path_data,
                get_path="path",
                get_color="color",
                width_scale=10,
                width_min_pixels=2,
                get_width=5,
                pickable=True,
                auto_highlight=True
            )

            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                map_style='mapbox://styles/mapbox/satellite-v9',
                tooltip={"text": "{name}"}
            )

            st.pydeck_chart(deck)

        except Exception as e:
            st.error(f"Error al procesar el archivo KMZ: {e}")
