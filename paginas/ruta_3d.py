# paginas/ruta_3d.py
import streamlit as st
import os
import zipfile
from xml.etree import ElementTree as ET
import plotly.graph_objects as go

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
                    coords.append((lon, lat, ele))
            return coords

def mostrar_ruta_3d():
    st.markdown("## 🌐 Visualizador 3D de Rutas")

    kmz_files = [f for f in os.listdir(carpeta_kmz) if f.endswith(".kmz")]
    rutas_disponibles = sorted(set(os.path.splitext(f)[0].split("_")[-1] for f in kmz_files))
    ruta_seleccionada = st.selectbox("Selecciona una ruta:", rutas_disponibles)

    if ruta_seleccionada:
        kmz_filename = next((f for f in kmz_files if f.endswith(f"{ruta_seleccionada}.kmz")), None)
        if kmz_filename:
            ruta = os.path.join(carpeta_kmz, kmz_filename)
            try:
                coords = extraer_coords_desde_kmz(ruta)
                if not coords:
                    st.warning("No se encontraron coordenadas.")
                    return

                lons = [p[0] for p in coords]
                lats = [p[1] for p in coords]
                elev = [p[2] for p in coords]

                fig = go.Figure(data=[go.Scatter3d(
                    x=lons,
                    y=lats,
                    z=elev,
                    mode='lines',
                    line=dict(color='blue', width=5),
                )])

                fig.update_layout(
                    margin=dict(l=0, r=0, b=0, t=30),
                    scene=dict(
                        xaxis_title='Longitud',
                        yaxis_title='Latitud',
                        zaxis_title='Altura (m)',
                        aspectmode='data'
                    ),
                    title="Vista 3D de la Ruta"
                )

                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Error al procesar el archivo KMZ: {e}")
