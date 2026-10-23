import json
import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="Catastro de Fusagasugá", layout="wide")

@st.cache_data
def cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        gj = json.load(f)
    df = pd.DataFrame([ft["properties"] for ft in gj["features"]])
    return gj, df

CAPAS = {
    "Urbano (manzanas)": {
        "archivo": "datos/manzanas_resumen.geojson",
        "centro": [4.34, -74.36], "zoom": 14,   # ajusta el centro si hace falta
        "metricas": {
            "% lotes urbanizados sin construir": "pct_sin_construir",
            "% uso habitacional": "pct_habitacional",
            "% uso comercial": "pct_comercial",
            "Unidades prediales": "n_predios",
        },
    },
    "Rural (veredas)": {
        "archivo": "datos/veredas_resumen.geojson",
        "centro": [4.30, -74.38], "zoom": 11,
        "metricas": {
            "% predios agropecuarios": "pct_agropecuario",
            "Unidades prediales": "n_predios",
            "Mediana del área de terreno (unidad por verificar)": "area_terreno_mediana",
        },
    },
}

tab_mapa, tab_calc = st.tabs(["Mapa", "Calculadora del predial"])

with tab_mapa:
    st.title("Catastro de Fusagasugá")
    capa = st.radio("Zona", list(CAPAS), horizontal=True)
    cfg = CAPAS[capa]
    etiqueta = st.selectbox("Indicador", list(cfg["metricas"]))
    col = cfg["metricas"][etiqueta]

    gj, df = cargar(cfg["archivo"])
    m = folium.Map(location=cfg["centro"], zoom_start=cfg["zoom"],
                   tiles="cartodbpositron")
    folium.Choropleth(
        geo_data=gj, data=df[["codigo", col]].dropna(),
        columns=["codigo", col], key_on="feature.properties.codigo",
        fill_color="YlOrRd", fill_opacity=0.8, line_opacity=0.3,
        nan_fill_color="lightgray", legend_name=etiqueta,
    ).add_to(m)
    campos = [c for c in dict.fromkeys(["nombre", "codigo", "n_predios", col])
              if c in df.columns]
    folium.GeoJson(
        gj, style_function=lambda x: {"fillOpacity": 0, "weight": 0},
        tooltip=folium.GeoJsonTooltip(fields=campos),
    ).add_to(m)
    st_folium(m, height=600, use_container_width=True)

    st.caption(
        "Fuente: datos abiertos de catastro (registros catastrales y cartografía), "
        "vigencia 01/01/2025. Las unidades prediales son filas del registro, no "
        "necesariamente terrenos. En gris: sin datos o menos de 5 unidades "
        "(se oculta por privacidad). Áreas de referencia, no oficiales."
    )

with tab_calc:
    st.title("Calculadora educativa del impuesto predial")
    st.write("Impuesto estimado = avalúo catastral × tarifa ÷ 1.000")
    avaluo = st.number_input("Avalúo catastral (COP)", min_value=0,
                             step=1_000_000, value=0)
    tarifa = st.number_input("Tarifa por mil", min_value=0.0, max_value=33.0,
                             step=0.5, value=0.0)
    st.metric("Impuesto estimado al año", f"${avaluo * tarifa / 1000:,.0f}")
    st.info("La tarifa depende del tipo de predio y la define el Acuerdo "
            "municipal. Consúltala en el estatuto tributario de Fusagasugá. "
            "Es solo un estimado con fines educativos.")