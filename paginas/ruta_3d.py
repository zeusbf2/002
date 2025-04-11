if pagina == "ruta_3d":
    st.title("🛰️ Visor 3D Externo")
    st.markdown("Abre el visor CesiumJS en una nueva pestaña:")
    st.markdown(
        """
        <a href="https://infinityfy.com/visor_3d_multiple/index.html" target="_blank">
            <button style="padding:12px 20px;font-size:16px;background:#2d72d9;color:white;border:none;border-radius:6px;">
                🌍 Abrir visor CesiumJS
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )
