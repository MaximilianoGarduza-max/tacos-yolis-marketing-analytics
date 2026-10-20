"""Exploración descriptiva para conectar señales de interés con compras observadas."""

import pandas as pd
import streamlit as st


OBJETIVO = "compro_ultima_campana_sintetica"
VARIABLES = {
    "producto_interes_principal_sintetico": "Producto de mayor interés",
    "producto_interes_secundario_sintetico": "Segundo producto de interés",
    "menciona_varios_antojitos_sintetico": "Menciona varios antojitos",
    "interes_salsa_molcajete_sintetico": "Interés en salsa molcajete",
    "segmento_marketing_sintetico": "Grupo de interés definido en el archivo",
}


def mostrar(df):
    st.header("3. Describir lo que observamos")
    st.markdown(
        "### ¿Qué señales de interés aparecen entre quienes compraron?\n\n"
        "Primero veremos el panorama general y después compararemos grupos de clientes. "
        "La meta es encontrar una pista para investigar, no asumir todavía que una campaña causará más compras."
    )
    if OBJETIVO not in df.columns:
        st.error(f"No se encontró la columna `{OBJETIVO}`.")
        return

    datos = df.copy()
    datos[OBJETIVO] = pd.to_numeric(datos[OBJETIVO], errors="coerce")
    datos = datos[datos[OBJETIVO].isin([0, 1])].copy()
    if datos.empty:
        st.warning("No hay resultados de campaña válidos para resumir.")
        return

    compras = int(datos[OBJETIVO].sum())
    total = len(datos)
    tasa_general = compras / total
    st.subheader("Paso 1 · El panorama de la campaña")
    a, b, c = st.columns(3)
    a.metric("Casos analizados", f"{total:,}")
    b.metric("Compraron", f"{compras:,}")
    c.metric("Compras observadas", f"{tasa_general:.1%}")
    st.caption("La tasa es compras observadas ÷ casos con resultado conocido.")

    disponibles = {col: nombre for col, nombre in VARIABLES.items() if col in datos.columns}
    if not disponibles:
        st.warning("No se encontraron variables de interés compatibles con esta vista.")
        return

    st.subheader("Paso 2 · Comparar grupos de clientes")
    seleccion = st.selectbox(
        "¿Qué característica quieres comparar?",
        options=list(disponibles),
        format_func=lambda col: disponibles[col],
        key="variable_grupo_descriptiva",
    )
    minimo = st.slider(
        "Mostrar grupos con al menos este número de casos",
        min_value=3, max_value=30, value=8, step=1,
        help="Los grupos pequeños pueden tener porcentajes muy inestables.",
        key="minimo_grupo_descriptiva",
    )

    nombre_grupo = "_grupo_descriptiva"
    datos[nombre_grupo] = datos[seleccion]
    if seleccion == "menciona_varios_antojitos_sintetico":
        datos[nombre_grupo] = datos[nombre_grupo].map({0: "Menciona un antojito", 1: "Menciona varios antojitos"})
    elif seleccion == "interes_salsa_molcajete_sintetico":
        datos[nombre_grupo] = datos[nombre_grupo].map({0: "Sin interés declarado", 1: "Con interés"})

    tabla = (
        datos.groupby(nombre_grupo, dropna=False)[OBJETIVO]
        .agg(Casos="size", Compras="sum", Tasa_de_compra="mean")
        .reset_index()
    )
    tabla["Grupo"] = tabla[nombre_grupo].fillna("Sin dato").astype(str)
    tabla["% que compró"] = (tabla["Tasa_de_compra"] * 100).round(1)
    tabla_visible = tabla[tabla["Casos"] >= minimo].sort_values(
        ["Tasa_de_compra", "Casos"], ascending=[False, False]
    )

    if tabla_visible.empty:
        st.info("Ningún grupo alcanza el mínimo elegido. Reduce el mínimo para explorar estos datos.")
        return

    st.write("**Compras observadas por grupo**")
    st.dataframe(
        tabla_visible[["Grupo", "Casos", "Compras", "% que compró"]],
        hide_index=True,
        use_container_width=True,
    )
    st.bar_chart(tabla_visible.set_index("Grupo")[["% que compró"]], y="% que compró")

    mejor = tabla_visible.iloc[0]
    st.subheader("Paso 3 · Convertir el hallazgo en una pregunta de marketing")
    if mejor["Tasa_de_compra"] > tasa_general:
        st.success(
            f"En estos datos, **{mejor['Grupo']}** tuvo la mayor proporción observada de compra entre los grupos mostrados: "
            f"{mejor['% que compró']:.1f}% ({int(mejor['Compras'])} de {int(mejor['Casos'])} casos). "
            f"El promedio general fue {tasa_general:.1%}."
        )
        st.write(
            "**Hipótesis para probar:** ¿un mensaje que destaque el interés de este grupo ayudaría a generar más visitas o compras? "
            "Para saberlo, habría que comparar una campaña con un grupo de control."
        )
    else:
        st.info(
            f"El grupo con mayor tasa entre los mostrados fue **{mejor['Grupo']}** ({mejor['% que compró']:.1f}%), "
            f"pero no superó el promedio general de {tasa_general:.1%}. Los datos todavía no señalan un grupo claramente destacado."
        )
    st.warning(
        "Estos porcentajes describen lo que pasó en el archivo sintético. Una diferencia entre grupos no demuestra "
        "que la característica haya causado la compra ni garantiza que se repita en una campaña real."
    )
    st.markdown(
        "**Conexión con la pregunta inicial:** ya podemos señalar qué grupos mostraron más compras en estos datos. "
        "La pestaña 4 explora si un modelo puede reconocer patrones similares en casos que no usó para aprender."
    )
