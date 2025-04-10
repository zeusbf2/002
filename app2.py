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
import math

# === CONFIG ===
archivo_excel = "INDICES CACC_IMN.xlsx"
hoja = "Indices Reales Normalizados"
carpeta_kmz = "tus_kmz"

# === FUNCIONES ===

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
        return "#FFFFFF"  # Blanco para sin datos
    if v <= 1.00:
        return "#00FF00"  # Verde
    elif v <= 2.00:
        return "#FFFF00"  # Amarillo
    elif v <= 3.00:
        return "#FFA500"  # Naranja
    elif v <= 4.00:
        return "#FF0000"  # Rojo
    elif v <= 5.00:
        return "#808080"  # Gris
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

def calcular_perpendicular(p1, p2, length=0.00015):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    mag = math.hypot(dx, dy)
    if mag == 0:
        return None
    dx /= mag
    dy /= mag
    px = -dy
    py = dx
    mid = p1
    start = (mid[0] + px * length / 2, mid[1] + py * length / 2)
    end = (mid[0] - px * length / 2, mid[1] - py * length / 2)
    return [start, end]

# === APP ===

st.set_page_config(layout="wide")
st.title("🗺️ Mapa ISV Mejorado")

kmz_files = [f for f in os.listdir(carpeta_kmz) if f.endswith(".kmz")]
rutas_disponibles = sorted(set(os.path.splitext(f)[0].split("_")[-1] for f in kmz_files))
ruta_seleccionada = st.selectbox("Selecciona una ruta:", rutas_disponibles)

if ruta_seleccionada:
    valores = cargar_valores_excel(ruta_seleccionada)
    if valores is None:
        st.warning("No se encontraron datos para esta ruta en el Excel.")
    else:
        kmz_filename = next((f for f in kmz_files if f.endswith(f"{ruta_seleccionada}.kmz")), None)
        if kmz_filename:
            ruta = os.path.join(carpeta_kmz, kmz_filename)
            try:
                linea = cargar_linea_desde_kmz(ruta)
                segmentos = dividir_linea_por_km(linea)

                if len(valores) < len(segmentos):
                    st.warning(f"⚠️ La ruta tiene {len(segmentos)} tramos de 1 km, pero el Excel solo tiene {len(valores)} valores. El resto será blanco (sin datos).")

                bounds = [[linea.bounds[1], linea.bounds[0]], [linea.bounds[3], linea.bounds[2]]]
                m = folium.Map()
                folium.TileLayer(
                    tiles="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                    attr="Google Satellite",
                    name="Satélite",
                    max_zoom=20,
                    subdomains=["mt0", "mt1", "mt2", "mt3"]
                ).add_to(m)
                folium.TileLayer("OpenStreetMap", name="Mapa base").add_to(m)
                m.fit_bounds(bounds)

                for i, seg in enumerate(segmentos):
                    color = valor_a_color(valores[i]) if i < len(valores) else "#FFFFFF"
                    folium.GeoJson(
                        mapping(seg),
                        style_function=(lambda col=color: lambda x: {"color": col, "weight": 5})(color)
                    ).add_to(m)

                    coords = list(seg.coords)
                    if len(coords) >= 2:
                        perp = calcular_perpendicular(coords[0], coords[1], length=0.00015)
                        if perp:
                            folium.PolyLine(
                                locations=[(perp[0][1], perp[0][0]), (perp[1][1], perp[1][0])],
                                color="black", weight=4
                            ).add_to(m)

                        dx = coords[1][0] - coords[0][0]
                        dy = coords[1][1] - coords[0][1]
                        label_x = coords[0][0] + dx * 0.03
                        label_y = coords[0][1] + dy * 0.03 - 0.0020

                        folium.Marker(
                            location=[label_y, label_x],
                            icon=folium.DivIcon(html=f"""
                                <div style='
                                    font-size: 10pt;
                                    color: black;
                                    font-weight: bold;
                                    text-shadow: -1px -1px 0 white, 1px -1px 0 white,
                                                 -1px 1px 0 white, 1px 1px 0 white;
                                '> {i+1}</div>
                            """)
                        ).add_to(m)


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

            except Exception as e:
                st.error(f"Error al procesar la ruta: {e}")
        else:
            st.error("No se encontró el archivo KMZ para esta ruta.")
