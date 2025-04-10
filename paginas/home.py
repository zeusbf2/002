import streamlit as st
import os
import zipfile
import geopandas as gpd
import io
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from shapely.geometry import LineString
from geopy.distance import geodesic

carpeta_kmz = "tus_kmz"

def cargar_linea_desde_kmz(kmz_path):
    with zipfile.ZipFile(kmz_path, 'r') as z:
        kml_file = next(f for f in z.namelist() if f.endswith('.kml'))
        with z.open(kml_file) as kml:
            gdf = gpd.read_file(io.BytesIO(kml.read()))
    return gdf.geometry.iloc[0], gdf

def calcular_distancia_acumulada(coords):
    distancias = [0.0]
    for i in range(1, len(coords)):
        p1 = (coords[i-1][1], coords[i-1][0])  # lat, lon
        p2 = (coords[i][1], coords[i][0])
        d = geodesic(p1, p2).meters
        distancias.append(distancias[-1] + d)
    return distancias

def mostrar_home():
    st.title("📍 Visualizador de Rutas")
    st.write("Aquí puedes explorar los trazados de rutas disponibles sin mapa de calor.")

    kmz_files = [f for f in os.listdir(carpeta_kmz) if f.endswith(".kmz")]
    rutas_disponibles = sorted(set(os.path.splitext(f)[0].split("_")[-1] for f in kmz_files))
    ruta_seleccionada = st.selectbox("Selecciona una ruta:", rutas_disponibles)

    if ruta_seleccionada:
        kmz_filename = next((f for f in kmz_files if f.endswith(f"{ruta_seleccionada}.kmz")), None)
        if kmz_filename:
            ruta = os.path.join(carpeta_kmz, kmz_filename)
            try:
                linea, gdf = cargar_linea_desde_kmz(ruta)
                bounds = [[linea.bounds[1], linea.bounds[0]], [linea.bounds[3], linea.bounds[2]]]
                m = folium.Map()
                folium.TileLayer("OpenStreetMap").add_to(m)
                m.fit_bounds(bounds)

                # Borde negro
                folium.GeoJson(
                    linea,
                    style_function=lambda x: {"color": "black", "weight": 8}
                ).add_to(m)

                # Línea azul encima
                folium.GeoJson(
                    linea,
                    style_function=lambda x: {"color": "#3388ff", "weight": 4}
                ).add_to(m)

                st_folium(m, use_container_width=True, height=600)

                # Elevación (si hay)
                if gdf.geometry.iloc[0].has_z:
                    coords = [c for c in gdf.geometry.iloc[0].coords if len(c) > 2]
                    if coords:
                        elevaciones = [round(c[2], 2) for c in coords]
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

                    else:
                        st.info("No se encontraron valores de elevación.")
                else:
                    st.info("La geometría no contiene datos de altitud (Z).")

            except Exception as e:
                st.error(f"Error al cargar la ruta: {e}")
        else:
            st.warning("No se encontró el archivo KMZ para esta ruta.")
