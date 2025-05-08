import streamlit as st
import zipfile
import os
import pandas as pd
import math
import folium
from shapely.geometry import LineString, mapping
from xml.etree import ElementTree as ET
from geopy.distance import geodesic
from streamlit_folium import st_folium

def mostrar_todas_rutas_isv():
    archivo_excel = "INDICES CACC_IMN.xlsx"
    hoja = "Indices Mejorados Normalizados"
    carpeta_kmz = "tus_kmz"



    # Cargar Excel una sola vez
    df_excel = pd.read_excel(archivo_excel, sheet_name=hoja, header=None, engine='openpyxl')

    def cargar_valores_excel(nombre_ruta, df):
        fila_nombres = df.iloc[3, 2:].astype(str).str.strip()
        coincidencias = fila_nombres[fila_nombres == nombre_ruta]
        if coincidencias.empty:
            return None
        idx_col = coincidencias.index[0]
        columna = df.loc[18:97, idx_col]
        valores = []
        for v in columna:
            try:
                valores.append(float(v))
            except:
                valores.append(None)
        return valores

    def valor_a_color(valor):
        try:
            v = float(valor)
        except:
            return "#FFFFFF"
        if v <= 1.00:
            return "#00FF00"
        elif v <= 2.00:
            return "#FFFF00"
        elif v <= 3.00:
            return "#FFA500"
        elif v <= 4.00:
            return "#FF0000"
        elif v <= 5.00:
            return "#808080"
        else:
            return "#FFFFFF"

    def cargar_linea_desde_kmz(kmz_path):
        with zipfile.ZipFile(kmz_path, 'r') as z:
            kml_file = next(f for f in z.namelist() if f.endswith('.kml'))
            with z.open(kml_file) as kml_data:
                tree = ET.parse(kml_data)
                root = tree.getroot()
                ns = {'kml': 'http://www.opengis.net/kml/2.2'}
                coords_text = root.find('.//kml:coordinates', ns).text.strip()
                coord_pairs = []
                for line in coords_text.split():
                    parts = line.split(",")
                    if len(parts) >= 2:
                        lon, lat = float(parts[0]), float(parts[1])
                        coord_pairs.append((lon, lat))
                return LineString(coord_pairs)

    def dividir_linea_por_km_real(linea):
        coords = list(linea.coords)
        segmentos = []
        segmento = [coords[0]]
        dist_acum = 0.0
        for i in range(1, len(coords)):
            p1 = (coords[i - 1][1], coords[i - 1][0])
            p2 = (coords[i][1], coords[i][0])
            d = geodesic(p1, p2).meters
            dist_acum += d
            segmento.append(coords[i])
            if dist_acum >= 1000:
                segmentos.append(LineString(segmento))
                segmento = [coords[i]]
                dist_acum = 0.0
        if len(segmento) > 1:
            segmentos.append(LineString(segmento))
        return segmentos

    st.markdown("<h1 style='font-size: 30px;'>🗺️ Mapa ISV Global Mejorado</h1>", unsafe_allow_html=True)

    kmz_files = [f for f in os.listdir(carpeta_kmz) if f.endswith(".kmz")]
    rutas_disponibles = sorted(set(os.path.splitext(f)[0].split("_")[-1] for f in kmz_files))

    if not rutas_disponibles:
        st.warning("No se encontraron archivos KMZ en la carpeta.")
        return

    m = folium.Map()
    folium.TileLayer(
        tiles="https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google Hybrid",
        name="Satélite + Nombres",
        max_zoom=20,
        subdomains=["mt0", "mt1", "mt2", "mt3"]
    ).add_to(m)
    folium.TileLayer("OpenStreetMap", name="Mapa base").add_to(m)

    progreso = st.progress(0, text="Procesando rutas...")

    for idx, ruta_sufijo in enumerate(rutas_disponibles):
        progreso.progress((idx + 1) / len(rutas_disponibles), text=f"Procesando {ruta_sufijo}...")

        valores = cargar_valores_excel(ruta_sufijo, df_excel)
        kmz_filename = next((f for f in kmz_files if f.endswith(f"{ruta_sufijo}.kmz")), None)
        if not kmz_filename:
            continue

        try:
            linea = cargar_linea_desde_kmz(os.path.join(carpeta_kmz, kmz_filename))
            segmentos = dividir_linea_por_km_real(linea)

            for i, seg in enumerate(segmentos):
                color = valor_a_color(valores[i]) if valores and i < len(valores) else "#FFFFFF"
                folium.GeoJson(mapping(seg), style_function=(lambda col=color: lambda x: {"color": col, "weight": 5})(color)).add_to(m)

        except Exception as e:
            st.error(f"❌ Error al procesar la ruta {ruta_sufijo}: {e}")

    folium.LayerControl().add_to(m)

    st.markdown("### 🗺️ Leyenda")
    st.markdown("""
    <div style='line-height: 2'>
    <span style='background-color:#00FF00;padding:5px 10px;margin-right:5px;'></span> CAT 1 - Muy baja (≤ 1.00)<br>
    <span style='background-color:#FFFF00;padding:5px 10px;margin-right:5px;'></span> CAT 2 - Baja (≤ 2.00)<br>
    <span style='background-color:#FFA500;padding:5px 10px;margin-right:5px;'></span> CAT 3 - Media (≤ 3.00)<br>
    <span style='background-color:#FF0000;padding:5px 10px;margin-right:5px;'></span> CAT 4 - Alta (≤ 4.00)<br>
    <span style='background-color:#808080;padding:5px 10px;margin-right:5px;'></span> CAT 5 - Muy alta (≤ 5.00)<br>
    <span style='background-color:#FFFFFF;padding:5px 10px;margin-right:5px;border:1px solid #ccc;'></span> Sin datos
    </div>
    """, unsafe_allow_html=True)

    st_folium(m, use_container_width=True, height=650)
