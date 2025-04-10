import streamlit as st
import os
import zipfile
import geopandas as gpd
import io
import folium
from streamlit_folium import st_folium
import plotly.express as px
from geopy.distance import geodesic

carpeta_kmz = "tus_kmz"

def cargar_linea_desde_kmz(kmz_path):
    with zipfile.ZipFile(kmz_path, 'r') as z:
        kml_file = next(f for f in z.namelist() if f.endswith('.kml'))
        with z.open(kml_file) as kml:
            gdf = gpd.read_file(io.BytesIO(kml.read()))
    return gdf.geometry.iloc[0], gdf

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

                # Borde negro grueso
                folium.GeoJson(
                    linea,
                    style_function=lambda x: {"color": "black", "weight": 8}
                ).add_to(m)

                # Línea principal
                folium.GeoJson(
                    linea,
                    style_function=lambda x: {"color": "#3388ff", "weight": 4}
                ).add_to(m)

                st_folium(m, use_container_width=True, height=600)

                # Mostrar gráfico de elevación si hay Z
                if linea.has_z:
                    coords = list(linea.coords)
                    elevaciones = []
                    distancias = []
                    dist_acum = 0.0

                    for i in range(len(coords)):
                        if len(coords[i]) < 3:
                            continue
                        z = coords[i][2]
                        if i == 0:
                            distancias.append(0)
                        else:
                            prev = (coords[i-1][1], coords[i-1][0])
                            curr = (coords[i][1], coords[i][0])
                            dist_acum += geodesic(prev, curr).meters
                            distancias.append(round(dist_acum, 2))
                        elevaciones.append(z)

                    df = {"Distancia (m)": distancias, "Altura (m)": elevaciones}
                    fig = px.line(df, x="Distancia (m)", y="Altura (m)",
                                  title="📈 Perfil de Elevación",
                                  markers=True,
                                  height=400)
                    fig.update_layout(margin=dict(l=30, r=30, t=40, b=30),
                                      template="plotly_white",
                                      xaxis_title="Distancia acumulada (m)",
                                      yaxis_title="Altura (m)")
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.info("La geometría no tiene valores de elevación (Z).")

            except Exception as e:
                st.error(f"Error al cargar la ruta: {e}")
        else:
            st.warning("No se encontró el archivo KMZ para esta ruta.")
