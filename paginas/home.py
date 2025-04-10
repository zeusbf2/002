import streamlit as st
import os
import zipfile
import geopandas as gpd
import io
import folium
from streamlit_folium import st_folium

carpeta_kmz = "tus_kmz"

def cargar_linea_desde_kmz(kmz_path):
    with zipfile.ZipFile(kmz_path, 'r') as z:
        kml_file = next(f for f in z.namelist() if f.endswith('.kml'))
        with z.open(kml_file) as kml:
            gdf = gpd.read_file(io.BytesIO(kml.read()))
    return gdf.geometry.iloc[0], gdf  # Devolvemos también el GeoDataFrame completo

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

                # 1️⃣ Capa de borde (más gruesa y negra)
                folium.GeoJson(
                    linea,
                    style_function=lambda x: {"color": "black", "weight": 8}
                ).add_to(m)

                # 2️⃣ Capa superior (color azul claro sobre el borde)
                folium.GeoJson(
                    linea,
                    style_function=lambda x: {"color": "#3388ff", "weight": 4}
                ).add_to(m)

                st_folium(m, use_container_width=True, height=600)

                # 3️⃣ Elevación (Z) desde los valores de altitud
                if gdf.geometry.iloc[0].has_z:
                    elevaciones = [coord[2] for coord in gdf.geometry.iloc[0].coords if len(coord) > 2]
                    if elevaciones:
                        elev_min = round(min(elevaciones), 2)
                        elev_max = round(max(elevaciones), 2)
                        st.markdown(f"**📈 Elevación:** mínima {elev_min} m, máxima {elev_max} m")
                    else:
                        st.info("No se encontraron valores de elevación en la geometría.")
                else:
                    st.info("La geometría no tiene valores de elevación (Z).")

            except Exception as e:
                st.error(f"Error al cargar la ruta: {e}")
        else:
            st.warning("No se encontró el archivo KMZ para esta ruta.")
