import streamlit as st
import zipfile
import geopandas as gpd
import pandas as pd
import os
import io
from shapely.geometry import LineString, mapping
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

def mostrar_todas_rutas_isv():
    archivo_excel = "INDICES CACC_IMN.xlsx"
    hoja = "Indices Mejorados Normalizados"
    carpeta_kmz = "tus_kmz"

    def cargar_valores_excel(nombre_ruta):
        df = pd.read_excel(archivo_excel, sheet_name=hoja, header=None, engine='openpyxl')
        fila_nombres = df.iloc[3, 2:].astype(str).str.strip()
        coincidencias = fila_nombres[fila_nombres == nombre_ruta]
        if coincidencias.empty:
            return None
        idx_col = coincidencias.index[0]
        columna = df.loc[18:97, idx_col]
        valores = []
        for v in columna:
            try:
                num = float(v)
                valores.append(num)
            except:
                valores.append(None)
        return valores

    def cargar_linea_desde_kmz(kmz_path):
        with zipfile.ZipFile(kmz_path, 'r') as z:
            kml_file = next(f for f in z.namelist() if f.endswith('.kml'))
            with z.open(kml_file) as kml:
                gdf = gpd.read_file(io.BytesIO(kml.read()))
        return gdf.geometry.iloc[0]

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

    def dividir_linea_por_km(linea):
        coords = list(linea.coords)
        segmentos = []
        segmento = [coords[0]]
        dist_acum = 0.0
        for i in range(1, len(coords)):
            p1 = (coords[i-1][1], coords[i-1][0])
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

    st.title("🗺️ Todas las rutas ISV sin Números")

    kmz_files = [f for f in os.listdir(carpeta_kmz) if f.endswith(".kmz")]
    rutas_disponibles = sorted(set(os.path.splitext(f)[0].split("_")[-1] for f in kmz_files))

    if not rutas_disponibles:
        st.warning("No se encontraron archivos KMZ en la carpeta.")
        return

    m = folium.Map(zoom_start=6)
    folium.TileLayer(
        tiles="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google Satellite",
        name="Satélite",
        max_zoom=20,
        subdomains=["mt0", "mt1", "mt2", "mt3"]
    ).add_to(m)
    folium.TileLayer("OpenStreetMap", name="Mapa base").add_to(m)

    for ruta_seleccionada in rutas_disponibles:
        valores = cargar_valores_excel(ruta_seleccionada)
        kmz_filename = next((f for f in kmz_files if f.endswith(f"{ruta_seleccionada}.kmz")), None)
        if not kmz_filename:
            continue
        ruta = os.path.join(carpeta_kmz, kmz_filename)
        try:
            linea = cargar_linea_desde_kmz(ruta)
            linea = linea.simplify(0.00005, preserve_topology=True)
            segmentos = dividir_linea_por_km(linea)

            for i, seg in enumerate(segmentos):
                color = valor_a_color(valores[i]) if valores and i < len(valores) else "#FFFFFF"
                folium.GeoJson(
                    mapping(seg),
                    style_function=(lambda col=color: lambda x: {"color": col, "weight": 5})(color)
                ).add_to(m)
        except Exception as e:
            st.warning(f"❌ Error en ruta {ruta_seleccionada}: {e}")

    folium.LayerControl().add_to(m)

    col1, col2 = st.columns([1, 4])
    with col1:
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
    with col2:
        st_folium(m, use_container_width=True, height=650)
