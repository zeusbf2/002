import streamlit as st
import os
import zipfile
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from shapely.geometry import LineString
from geopy.distance import geodesic
from xml.etree import ElementTree as ET

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

def calcular_distancia_acumulada(coords):
    distancias = [0.0]
    for i in range(1, len(coords)):
        p1 = (coords[i-1][1], coords[i-1][0])  # lat, lon
        p2 = (coords[i][1], coords[i][0])
        d = geodesic(p1, p2).meters
        distancias.append(distancias[-1] + d)
    return distancias

def mostrar_home():
    st.markdown("<h1 style='font-size: 15px;'>📍 Visualizador de Rutas</h1>", unsafe_allow_html=True)
    


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
                    st.warning("No se encontraron coordenadas con elevación.")
                    return

                linea = LineString([(lon, lat) for lon, lat, _ in coords])
                bounds = [[linea.bounds[1], linea.bounds[0]], [linea.bounds[3], linea.bounds[2]]]

                m = folium.Map()
                folium.TileLayer("OpenStreetMap").add_to(m)
                m.fit_bounds(bounds)

                folium.GeoJson(
                    linea,
                    style_function=lambda x: {"color": "black", "weight": 8}
                ).add_to(m)

                folium.GeoJson(
                    linea,
                    style_function=lambda x: {"color": "#3388ff", "weight": 4}
                ).add_to(m)

                st_folium(m, use_container_width=True, height=600)

                elevaciones = [round(z, 2) for _, _, z in coords]
                distancias = calcular_distancia_acumulada(coords)

                elev_min = round(min(elevaciones), 2)
                elev_max = round(max(elevaciones), 2)

                st.markdown(f"**📈 Elevación:** mínima {elev_min} m, máxima {elev_max} m")

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=distancias,
                    y=elevaciones,
                    mode="lines",
                    line=dict(color="mediumslateblue", width=3),
                    fill="tozeroy",
                    name="Altura (m)"
                ))

                fig.update_layout(
                    margin=dict(l=20, r=20, t=30, b=20),
                    xaxis_title="Distancia (m)",
                    yaxis_title="Elevación (m)",
                    template="plotly_white",
                    height=300,
                    showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Error al procesar el archivo KMZ: {e}")
        else:
            st.warning("No se encontró el archivo KMZ para esta ruta.")
