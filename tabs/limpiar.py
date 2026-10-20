"""Diagnóstico y tratamiento reversible de calidad de datos."""

import pandas as pd
import streamlit as st


def _resumen_faltantes(df):
    faltantes = df.isna().sum()
    tabla = pd.DataFrame({
        "Variable": faltantes.index,
        "Valores faltantes": faltantes.values,
        "% faltante": (faltantes / max(len(df), 1) * 100).round(1).values,
    })
    return tabla[tabla["Valores faltantes"] > 0].sort_values(
        "Valores faltantes", ascending=False
    )


def mostrar(df):
    st.header("2. Limpiar los datos")
    st.markdown(
        "Revisa los problemas antes de tratar los datos. Cada cambio se aplica "
        "a una copia y queda descrito; el archivo original permanece intacto."
    )

    st.subheader("Diagnóstico de calidad")
    faltantes = _resumen_faltantes(df)
    duplicados = int(df.duplicated().sum())
    col1, col2, col3 = st.columns(3)
    col1.metric("Registros originales", f"{len(df):,}")
    col2.metric("Filas duplicadas exactas", f"{duplicados:,}")
    col3.metric("Variables con faltantes", f"{len(faltantes):,}")

    if faltantes.empty:
        st.success("No se encontraron valores faltantes.")
    else:
        st.write("Los faltantes no se consideran errores automáticamente. Revisa su significado:")
        st.dataframe(faltantes, hide_index=True, use_container_width=True)

    numericas = df.select_dtypes(include="number").columns.tolist()
    if numericas:
        with st.expander("Revisar valores numéricos negativos"):
            st.caption(
                "Un valor negativo puede ser inválido en conteos o visitas, "
                "pero confirma el significado de cada variable antes de decidir."
            )
            candidatas = [
                c for c in numericas
                if any(p in c.lower() for p in ("numero", "visita", "interaccion", "antojito"))
            ]
            seleccion = st.multiselect(
                "Variables que quieres revisar", numericas, default=candidatas,
                key="variables_conteo_limpiar",
            )
            filas_negativas = pd.Series(False, index=df.index)
            for columna in seleccion:
                filas_negativas |= df[columna].lt(0).fillna(False)
            st.metric("Filas con valores negativos seleccionados", int(filas_negativas.sum()))

    st.subheader("Decidir tratamientos")
    st.caption("Los cambios son optativos. No se imputan valores automáticamente.")
    quitar_duplicados = st.checkbox(
        "Quitar filas duplicadas exactas", value=False, disabled=(duplicados == 0),
        help="Conserva la primera aparición. Actívalo solo si confirmas que las repeticiones no son eventos legítimos.",
        key="quitar_duplicados_limpiar",
    )

    tratamientos = {}
    if not faltantes.empty:
        st.write("Tratamiento de faltantes")
        for columna in faltantes["Variable"]:
            tratamientos[columna] = st.selectbox(
                f"{columna} ({int(df[columna].isna().sum())} faltantes)",
                ["Conservar faltantes", "Excluir filas con faltante en esta variable"],
                key=f"tratamiento_{columna}",
            )

    df_limpio = df.copy()
    cambios = []
    if quitar_duplicados:
        antes = len(df_limpio)
        df_limpio = df_limpio.drop_duplicates(keep="first").copy()
        cambios.append(f"Se quitaron {antes - len(df_limpio)} filas duplicadas exactas.")
    for columna, opcion in tratamientos.items():
        if opcion.startswith("Excluir"):
            antes = len(df_limpio)
            df_limpio = df_limpio.dropna(subset=[columna]).copy()
            cambios.append(f"Se excluyeron {antes - len(df_limpio)} filas con faltante en {columna}.")

    st.subheader("Resultado de la revisión")
    if cambios:
        for cambio in cambios:
            st.write(f"- {cambio}")
    else:
        st.info("No se aplicaron cambios. Los faltantes y duplicados se conservan.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Filas en copia de trabajo", f"{len(df_limpio):,}")
    m2.metric("Faltantes restantes", f"{int(df_limpio.isna().sum().sum()):,}")
    m3.metric("Duplicados restantes", f"{int(df_limpio.duplicated().sum()):,}")
    st.session_state["df_limpio"] = df_limpio
    st.dataframe(df_limpio.head(10), hide_index=True, use_container_width=True)
    st.caption("La copia queda disponible como st.session_state['df_limpio']; df conserva los datos de entrada.")
