import pandas as pd
import streamlit as st

from tabs import decisiones, descriptiva, entender, limpiar, predictiva, prescriptiva


st.set_page_config(
    page_title="Tacos Yolis - Marketing Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Tacos Yolis - Marketing Analytics")
st.markdown(
    "Aplicación para analizar información de clientes "
    "y convertir los datos en decisiones de marketing."
)

df = pd.read_csv("data/dataset_tacos_yolis_sintetico.csv")

tab_entender, tab_limpiar, tab_descriptiva, tab_predictiva, tab_prescriptiva, tab_decisiones = st.tabs([
    "1. Entender",
    "2. Limpiar",
    "3. Descriptiva",
    "4. Predictiva",
    "5. Prescriptiva",
    "6. Decisiones",
])

with tab_entender:
    entender.mostrar(df)

with tab_limpiar:
    limpiar.mostrar(df)

with tab_descriptiva:
    descriptiva.mostrar(df)

with tab_predictiva:
    predictiva.mostrar(df)

with tab_prescriptiva:
    prescriptiva.mostrar(df)

with tab_decisiones:
    decisiones.mostrar()
