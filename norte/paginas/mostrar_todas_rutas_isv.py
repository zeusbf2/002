import streamlit as st
import zipfile
import os
import shutil
import pandas as pd
import math
import folium
from shapely.geometry import LineString, mapping
from xml.etree import ElementTree as ET
from geopy.distance import geodesic
from streamlit_folium import st_folium

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAIZ_PROYECTO = os.path.abspath(os.path.join(BASE_DIR, ".."))
archivo_excel = os.path.join(RAIZ_PROYECTO, "INDICES CACC_IMN.xlsx")
hoja = "Indices Mejorados Normalizados"
carpeta_kmz = os.path.join(RAIZ_PROYECTO, "tus_kmz")
carpeta_salida = os.path.join(RAIZ_PROYECTO, "kmz_pintados")
os.makedirs(carpeta_salida, exist_ok=True)

def kml_color(html_color):
    """Convierte un color HTML (#RRGGBB) a formato KML (aabbggrr) con alfa completa."""
    html_color = html_color.lstrip('#')
    if len(html_color) != 6:
        return "ff000000"
    r = html_color[0:2]
    g = html_color[2:4]
    b = html_color[4:6]
    return f"ff{b}{g}{r}"

def mostrar_todas_rutas_isv():
    st.markdown("<h1 style='font-size: 30px;'>🖍️ Pintar y Exportar KMZs con ISV</h1>", unsafe_allow_html=True)

    if not os.path.exists(archivo_excel):
        st.error(f"No se encontró el archivo Excel: {archivo_excel}")
        return
    if not os.path.exists(carpeta_kmz):
        st.error(f"No se encontró la carpeta de archivos KMZ: {carpeta_kmz}")
        return

    kmz_files = [f for f in os.listdir(carpeta_kmz) if f.endswith(".kmz")]
    rutas_disponibles = sorted(set(os.path.splitext(f)[0].split("_")[-1] for f in kmz_files))
    if not rutas_disponibles:
        st.warning("No se encontraron archivos KMZ en la carpeta.")
        return

    ejecutar = st.button("🖍️ Pintar y exportar KMZs")

    df_excel = pd.read_excel(archivo_excel, sheet_name=hoja, header=None, engine='openpyxl')

    def cargar_valores_excel(nombre_ruta, df):
        fila_nombres = df.iloc[3, 2:].astype(str).str.strip()
        coincidencias = fila_nombres[fila_nombres == nombre_ruta]
        if coincidencias.empty:
            return None
        idx_col = coincidencias.index[0]
        columna = df.loc[18:721, idx_col]
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

    if ejecutar:
        progreso = st.progress(0, text="Procesando rutas...")

        for idx, ruta_sufijo in enumerate(rutas_disponibles):
            progreso.progress((idx + 1) / len(rutas_disponibles), text=f"Procesando {ruta_sufijo}...")

            valores = cargar_valores_excel(ruta_sufijo, df_excel)
            kmz_filename = next((f for f in kmz_files if f.endswith(f"{ruta_sufijo}.kmz")), None)
            if not kmz_filename:
                continue

            try:
                kmz_path = os.path.join(carpeta_kmz, kmz_filename)
                linea = cargar_linea_desde_kmz(kmz_path)
                segmentos = dividir_linea_por_km_real(linea)

                kml_output = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
                doc = ET.SubElement(kml_output, "Document")

                for i, seg in enumerate(segmentos):
                    color = valor_a_color(valores[i]) if valores and i < len(valores) else "#FFFFFF"
                    placemark = ET.SubElement(doc, "Placemark")
                    ET.SubElement(placemark, "name").text = f"Tramo {i+1}"
                    style = ET.SubElement(placemark, "Style")
                    line_style = ET.SubElement(style, "LineStyle")
                    ET.SubElement(line_style, "color").text = kml_color(color)
                    ET.SubElement(line_style, "width").text = "4"

                    linestring = ET.SubElement(placemark, "LineString")
                    ET.SubElement(linestring, "tessellate").text = "1"
                    coords = " ".join([f"{x[0]},{x[1]},0" for x in seg.coords])
                    ET.SubElement(linestring, "coordinates").text = coords

                nombre_base = os.path.splitext(kmz_filename)[0]
                kml_path = os.path.join(carpeta_salida, f"{nombre_base}.kml")
                tree = ET.ElementTree(kml_output)
                tree.write(kml_path, encoding="utf-8", xml_declaration=True)

                kmz_out = os.path.join(carpeta_salida, f"{nombre_base}_pintado.kmz")
                with zipfile.ZipFile(kmz_out, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(kml_path, arcname="doc.kml")
                os.remove(kml_path)

            except Exception as e:
                st.error(f"❌ Error al procesar la ruta {ruta_sufijo}: {e}")

        st.success("✅ ¡Todos los archivos KMZ pintados fueron generados exitosamente!")

        # VISOR FINAL DE KMZ GENERADOS
        st.markdown("### 🗺️ Visualización de KMZs pintados")
        m = folium.Map()
        folium.TileLayer("OpenStreetMap").add_to(m)

        for archivo in os.listdir(carpeta_salida):
            if archivo.endswith("_pintado.kmz"):
                try:
                    with zipfile.ZipFile(os.path.join(carpeta_salida, archivo), 'r') as z:
                        kml_file = next(f for f in z.namelist() if f.endswith('.kml'))
                        with z.open(kml_file) as kml_data:
                            tree = ET.parse(kml_data)
                            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
                            for placemark in tree.findall(".//kml:Placemark", ns):
                                coords_node = placemark.find('.//kml:coordinates', ns)
                                if coords_node is None:
                                    continue
                                coords_text = coords_node.text.strip()
                                coord_pairs = []
                                for line in coords_text.split():
                                    parts = line.split(",")
                                    if len(parts) >= 2:
                                        lon, lat = float(parts[0]), float(parts[1])
                                        coord_pairs.append((lat, lon))
                                if coord_pairs:
                                    folium.PolyLine(coord_pairs, color="blue", weight=3).add_to(m)
                except:
                    continue

        st_folium(m, use_container_width=True, height=600)
