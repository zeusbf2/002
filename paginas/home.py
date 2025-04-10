import streamlit as st
import os
import zipfile
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from shapely.geometry import LineString
from geopy.distance import geodesic
from xml.etree import ElementTree as ET
from streamlit.components.v1 import html

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
    st.markdown("""
        <style>
            .main-container {
                padding: 0;
            }
            .map-container {
                height: 70vh;
                margin-bottom: 0.5rem;
            }
            iframe {
                border: none;
            }
            .info-text {
                margin: 0;
                padding: 0 0 0.2rem 0.5rem;
                font-size: 15px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='font-size: 25px; margin-bottom: 0.2rem;'>📍 Visualizador de Rutas</h1>", unsafe_allow_html=True)
    st.markdown("<p class='info-text'>Explora los trazados de rutas disponibles sin mapa de calor.</p>", unsafe_allow_html=True)

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

                m = folium.Map(tiles="OpenStreetMap")
                m.fit_bounds(bounds)
                folium.GeoJson(linea, style_function=lambda x: {"color": "black", "weight": 8}).add_to(m)
                folium.GeoJson(linea, style_function=lambda x: {"color": "#3388ff", "weight": 4}).add_to(m)

                mapa_html = m.get_root().render().replace('"', '&quot;')

                # Mapa con menos separación debajo
                html(f"""
                    <div class="map-container">
                        <iframe srcdoc="{mapa_html}" width="100%" height="100%"></iframe>
                    </div>
                """, height=500)

                elevaciones = [round(z, 2) for _, _, z in coords]
                distancias = calcular_distancia_acumulada(coords)

                elev_min = round(min(elevaciones), 2)
                elev_max = round(max(elevaciones), 2)

                st.markdown(f"<p class='info-text'><b>📈 Elevación:</b> mínima {elev_min} m, máxima {elev_max} m</p>", unsafe_allow_html=True)

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
                    margin=dict(l=10, r=10, t=20, b=20),
                    xaxis_title="Distancia (m)",
                    yaxis_title="Elevación (m)",
                    template="plotly_white",
                    height=260,
                    showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Error al procesar el archivo KMZ: {e}")
        else:
            st.warning("No se encontró el archivo KMZ para esta ruta.")
