"""Ayuda a convertir una señal de interés en una acción de marketing comprobable."""

import pandas as pd
import streamlit as st


OBJETIVO = "compro_ultima_campana_sintetica"
GRUPOS = {
    "producto_interes_principal_sintetico": "Producto de mayor interés",
    "producto_interes_secundario_sintetico": "Segundo producto de interés",
    "menciona_varios_antojitos_sintetico": "Menciona varios antojitos",
    "interes_salsa_molcajete_sintetico": "Interés en salsa molcajete",
    "segmento_marketing_sintetico": "Grupo descrito en el archivo",
}


def _preparar_grupos(df, columna):
    grupos = df[columna].copy()
    if columna == "menciona_varios_antojitos_sintetico":
        return grupos.map({0: "Menciona un antojito", 1: "Menciona varios antojitos"}).fillna("Sin dato")
    if columna == "interes_salsa_molcajete_sintetico":
        return grupos.map({0: "Sin interés declarado", 1: "Con interés"}).fillna("Sin dato")
    return grupos.fillna("Sin dato").astype(str)


def _acciones_posibles(columna, valor):
    if columna == "producto_interes_principal_sintetico":
        return [
            f"Probar un mensaje que hable de {valor}, el producto de mayor interés del grupo.",
            "Preguntar qué otros antojitos también les gustaría conocer.",
        ]
    if columna == "producto_interes_secundario_sintetico":
        if valor.lower() in {"ninguno", "sin dato"}:
            return [
                "Preguntar qué antojito les interesa conocer.",
                "Usar el producto de mayor interés de cada persona en un mensaje personalizado.",
            ]
        return [
            f"Probar contenido que conecte {valor} con el producto de mayor interés de cada persona.",
            "Preguntar cuál de los dos productos les interesa más.",
        ]
    if columna == "menciona_varios_antojitos_sintetico":
        if valor == "Menciona varios antojitos":
            return [
                "Crear un mensaje personalizado con los antojitos que cada persona mencionó.",
                "Preguntar cuál de los antojitos mencionados le interesa más a cada persona.",
            ]
        return [
            "Enfocar el mensaje en el producto de mayor interés de cada persona.",
            "Preguntar qué otro antojito le gustaría conocer.",
        ]
    if columna == "interes_salsa_molcajete_sintetico":
        if valor == "Con interés":
            return [
                "Probar contenido informativo sobre salsa molcajete y preguntar qué le gustaría saber al grupo.",
                "Preguntar qué antojito acompañaría con salsa molcajete.",
            ]
        return [
            "No centrar el mensaje en salsa; hablar del producto de mayor interés de cada persona.",
            "Preguntar qué tipo de antojito le interesa al grupo.",
        ]
    if "Explora" in valor:
        return [
            "Crear un mensaje personalizado con los dos antojitos que cada persona mencionó.",
            "Preguntar cuál de los antojitos mencionados le interesa más a cada persona.",
        ]
    producto = valor.replace("Afinidad por ", "")
    return [
        f"Probar un mensaje sobre {producto}, el producto de afinidad descrito para este grupo.",
        "Invitar al grupo a compartir qué antojito le interesa.",
    ]


def mostrar(df):
    st.header("5. Elegir una acción para probar")
    st.markdown(
        "### ¿Qué podríamos hacer con lo que aprendimos?\n\n"
        "Usa un interés observado para proponer una acción concreta. La recomendación es una idea para poner a prueba, "
        "no una promesa de que el grupo comprará."
    )
    if OBJETIVO not in df.columns:
        st.error("No se encontró el resultado de compra de la campaña en el archivo.")
        return

    columnas = {c: nombre for c, nombre in GRUPOS.items() if c in df.columns}
    if not columnas:
        st.warning("No hay características de interés para comparar en este archivo.")
        return

    datos = df.copy()
    datos[OBJETIVO] = pd.to_numeric(datos[OBJETIVO], errors="coerce")
    datos = datos[datos[OBJETIVO].isin([0, 1])].copy()
    if datos.empty:
        st.warning("No hay resultados válidos de campaña para elaborar una propuesta.")
        return

    st.subheader("Paso 1 · Escoger a quién queremos atender")
    columna = st.selectbox(
        "Elige una característica que tenga sentido para tu idea",
        options=list(columnas),
        format_func=lambda opcion: columnas[opcion],
        key="caracteristica_prescriptiva",
    )
    datos["_grupo_accion"] = _preparar_grupos(datos, columna)
    opciones_grupo = sorted(datos["_grupo_accion"].unique().tolist())
    grupo = st.selectbox("Elige el grupo", opciones_grupo, key=f"grupo_prescriptivo_{columna}")
    seleccion = datos[datos["_grupo_accion"] == grupo]

    cantidad = len(seleccion)
    compradores = int(seleccion[OBJETIVO].sum())
    tasa_grupo = compradores / cantidad if cantidad else 0
    total = len(datos)
    tasa_general = float(datos[OBJETIVO].mean()) if total else 0

    st.subheader("Paso 2 · Revisar qué evidencia tenemos")
    c1, c2, c3 = st.columns(3)
    c1.metric("Personas en el grupo", f"{cantidad:,}")
    c2.metric("Compraron en la campaña anterior", f"{compradores:,}")
    c3.metric("Proporción que compró", f"{tasa_grupo:.1%}")
    st.write(
        f"En todo el archivo, compró el {tasa_general:.1%} de los casos. "
        f"En el grupo **{grupo}**, compró el {tasa_grupo:.1%} ({compradores} de {cantidad})."
    )
    if cantidad < 8:
        st.warning("El grupo es pequeño. Toma este resultado como una pista inicial y reúne más información antes de invertir mucho en la acción.")
    elif tasa_grupo > tasa_general:
        st.info("Este grupo tuvo una proporción de compra mayor que el promedio del archivo. Vale la pena pensar en una prueba sencilla.")
    else:
        st.info("Este grupo no superó el promedio general. Aun así, puedes probar una acción si hay una razón de marca o aprendizaje para hacerlo.")

    st.subheader("Paso 3 · Elegir una acción sencilla")
    acciones = _acciones_posibles(columna, grupo)
    accion = st.selectbox(
        "¿Qué te gustaría probar con este grupo?",
        options=acciones,
        key=f"accion_prescriptiva_{columna}_{grupo.replace(' ', '_')}",
    )
    st.success(f"**Propuesta:** {accion}")
    st.caption("La propuesta se basa en intereses que ya aparecen en los datos. No agrega descuentos, urgencia ni beneficios que el archivo no menciona.")

    st.session_state["propuesta_marketing"] = {
        "columna": columna,
        "caracteristica": columnas[columna],
        "grupo": grupo,
        "personas": cantidad,
        "compradores": compradores,
        "tasa_grupo": tasa_grupo,
        "total": total,
        "tasa_general": tasa_general,
        "accion": accion,
    }
    st.markdown(
        "**Siguiente paso:** lleva esta propuesta a la pestaña 6 para redactar un mensaje y acordar cómo medir si funcionó."
    )
