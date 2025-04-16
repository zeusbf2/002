import streamlit as st
import os
import pandas as pd
import math
import folium
from shapely.geometry import LineString, mapping
from xml.etree import ElementTree as ET
from geopy.distance import geodesic
from streamlit_folium import st_folium

def mostrar_isvr():
    archivo_excel = "INDICES CACC_IRN.xlsx"
    hoja = "Indices Reales Normalizados"
    carpeta_kml = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tus_kmz"))

    @st.cache_data
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

    @st.cache_data
    def cargar_linea_desde_kml(kml_path):
        tree = ET.parse(kml_path)
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

    def construir_mapa(segmentos, valores, bounds, capa_base):
        with st.status("🧱 Inicializando construcción del mapa...", expanded=True) as status:
            status.write("🗺️ Generando mapa base...")
            m = folium.Map()
            if capa_base == "Satélite + Nombres":
                status.write("🛰️ Agregando capa satelital...")
                folium.TileLayer(
                    tiles="https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
                    attr="Google Hybrid",
                    name="Satélite + Nombres",
                    max_zoom=20,
                    subdomains=["mt0", "mt1", "mt2", "mt3"]
                ).add_to(m)
            else:
                status.write("🗺️ Agregando capa base (OpenStreetMap)...")
                folium.TileLayer("OpenStreetMap", name="Mapa base").add_to(m)

            status.write("📍 Ajustando vista al área de la ruta...")
            m.fit_bounds(bounds)

            barra = st.progress(0, text="🎨 Procesando segmentos...")
            total = len(segmentos)

            for i, seg in enumerate(segmentos):
                color = valor_a_color(valores[i]) if i < len(valores) else "#FFFFFF"
                status.write(f"🎨 Añadiendo segmento {i+1} de {total} con color {color}")
                folium.GeoJson(mapping(seg), style_function=lambda x: {"color": "black", "weight": 9}).add_to(m)
                folium.GeoJson(mapping(seg), style_function=(lambda col=color: lambda x: {"color": col, "weight": 5})(color)).add_to(m)

                coords = list(seg.coords)
                if len(coords) >= 2:
                    dx = coords[1][0] - coords[0][0]
                    dy = coords[1][1] - coords[0][1]
                    label_x = coords[0][0] + dx * 0.03
                    label_y = coords[0][1] + dy * 0.03 - 0.0020

                    status.write(f"📌 Colocando marcador en segmento {i+1}")
                    icon_html = f"""
                    <div style="background-color: {color}; color: black;
                                border-radius: 50%; width: 32px; height: 32px;
                                display: flex; align-items: center; justify-content: center;
                                font-weight: bold; font-size: 13px;
                                border: 2px solid #00000088;
                                box-shadow: 1px 1px 6px rgba(0,0,0,0.5);">
                        {i+1}
                    </div>
                    """
                    folium.Marker(location=[label_y, label_x], icon=folium.DivIcon(html=icon_html)).add_to(m)

                barra.progress((i + 1) / total, text=f"Segmento {i+1} de {total} listo")

            status.write("✅ Añadiendo control de capas...")
            folium.LayerControl().add_to(m)
            status.update(label="✅ Mapa completo con segmentos y marcadores.", state="complete")
            return m

        st.markdown("<h1 style='font-size: 30px;'>🗺️ Mapa ISV Real</h1>", unsafe_allow_html=True)

    kml_files = [f for f in os.listdir(carpeta_kml) if f.endswith(".kml")]
    rutas_disponibles = sorted(set(os.path.splitext(f)[0].split("_")[-1] for f in kml_files))
    ruta_seleccionada = st.selectbox("Selecciona una ruta:", rutas_disponibles, key="select_ruta_isvr")

    capa_base = st.radio("Capa base:", ["Satélite + Nombres", "Mapa base"], horizontal=True)

    if ruta_seleccionada:
        clave_segmentos = f"segmentos_{ruta_seleccionada}"
        clave_valores = f"valores_{ruta_seleccionada}"
        clave_long = f"long_{ruta_seleccionada}"
        clave_bounds = f"bounds_{ruta_seleccionada}"

        if clave_segmentos not in st.session_state:
            st.status("📂 Cargando datos desde Excel y KML...")
            valores = cargar_valores_excel(ruta_seleccionada)
            if valores is None:
                st.warning("No se encontraron datos para esta ruta en el Excel.")
                st.info("Revisa que el nombre en el Excel coincida exactamente con el sufijo del nombre del KML.")
                return

            kml_filename = next((f for f in kml_files if f.endswith(f"{ruta_seleccionada}.kml")), None)
            if not kml_filename:
                st.error("No se encontró el archivo KML para esta ruta.")
                return

            ruta = os.path.join(carpeta_kml, kml_filename)

            try:
                linea = cargar_linea_desde_kml(ruta)

                def longitud_geodesica_total(linea):
                    coords = list(linea.coords)
                    total = 0
                    for i in range(1, len(coords)):
                        p1 = (coords[i - 1][1], coords[i - 1][0])
                        p2 = (coords[i][1], coords[i][0])
                        total += geodesic(p1, p2).meters
                    return total / 1000

                long_km = longitud_geodesica_total(linea)
                segmentos = dividir_linea_por_km_real(linea)
                bounds = [[linea.bounds[1], linea.bounds[0]], [linea.bounds[3], linea.bounds[2]]]

                st.session_state[clave_segmentos] = segmentos
                st.session_state[clave_valores] = valores
                st.session_state[clave_long] = long_km
                st.session_state[clave_bounds] = bounds

            except Exception as e:
                st.error(f"Error al procesar la ruta: {e}")
                return

        segmentos = st.session_state[clave_segmentos]
        valores = st.session_state[clave_valores]
        long_km = st.session_state[clave_long]
        bounds = st.session_state[clave_bounds]
        m = construir_mapa(segmentos, valores, bounds, capa_base)

        st.info(f"📍 Longitud total del KML: {long_km:.2f} km")
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
            st_folium(m, use_container_width=True, height=650, key="mapa")
