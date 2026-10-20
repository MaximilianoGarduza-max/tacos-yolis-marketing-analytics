"""Modelo de aprendizaje para conversar sobre intención de compra."""

import sys

import pandas as pd
import streamlit as st


OBJETIVO = "compro_ultima_campana_sintetica"
EXCLUIR = {
    "id_caso_sintetico",
    "es_sintetico",
    "segmento_marketing_sintetico",
    OBJETIVO,
}
NOMBRES = {
    "producto_interes_principal_sintetico": "Producto de mayor interés",
    "producto_interes_secundario_sintetico": "Segundo producto de interés",
    "numero_antojitos_mencionados_sintetico": "Cantidad de antojitos mencionados",
    "menciona_varios_antojitos_sintetico": "Menciona varios antojitos",
    "interes_salsa_molcajete_sintetico": "Interés en salsa molcajete",
    "interacciones_facebook_30d_sinteticas": "Interacciones en Facebook (últimos 30 días)",
    "visitas_local_estimadas_mes_sinteticas": "Visitas estimadas al local (mes)",
}


def _aprender_y_revisar(df, variables, umbral):
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import confusion_matrix
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    datos = df[variables + [OBJETIVO]].copy()
    datos[OBJETIVO] = pd.to_numeric(datos[OBJETIVO], errors="coerce")
    datos = datos.dropna(subset=[OBJETIVO])
    datos = datos[datos[OBJETIVO].isin([0, 1])]
    if datos[OBJETIVO].nunique() != 2:
        raise ValueError("Se necesitan casos de compra y de no compra para hacer esta comparación.")

    x = datos[variables]
    y = datos[OBJETIVO].astype(int)
    if y.value_counts().min() < 2:
        raise ValueError("Hay muy pocos casos de una de las respuestas para hacer una evaluación útil.")

    indices_aprendizaje, indices_revision = train_test_split(
        datos.index,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )
    x_aprendizaje = x.loc[indices_aprendizaje]
    x_revision = x.loc[indices_revision]
    y_aprendizaje = y.loc[indices_aprendizaje]
    y_revision = y.loc[indices_revision]

    numericas = x.select_dtypes(include="number").columns.tolist()
    categoricas = [col for col in variables if col not in numericas]
    preparaciones = []
    if numericas:
        preparaciones.append(("numeros", Pipeline([
            ("faltantes", SimpleImputer(strategy="median")),
            ("escala", StandardScaler()),
        ]), numericas))
    if categoricas:
        preparaciones.append(("categorias", Pipeline([
            ("faltantes", SimpleImputer(strategy="most_frequent")),
            ("opciones", OneHotEncoder(handle_unknown="ignore")),
        ]), categoricas))

    modelo = Pipeline([
        ("preparacion", ColumnTransformer(preparaciones)),
        ("aprendizaje", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    modelo.fit(x_aprendizaje, y_aprendizaje)

    probabilidades = modelo.predict_proba(x_revision)[:, 1]
    recomendaciones = (probabilidades >= umbral).astype(int)
    matriz = confusion_matrix(y_revision, recomendaciones, labels=[0, 1])
    total_recomendados = int(recomendaciones.sum())
    compradores_en_revision = int(y_revision.sum())
    compradores_encontrados = int(matriz[1, 1])

    casos = df.loc[indices_revision, "id_caso_sintetico"] if "id_caso_sintetico" in df.columns else indices_revision
    resultados = pd.DataFrame({
        "Caso": casos,
        "Compró en la campaña": y_revision.map({0: "No", 1: "Sí"}),
        "Posibilidad estimada de compra (%)": probabilidades * 100,
        "¿El modelo lo habría señalado?": ["Sí" if r else "No" for r in recomendaciones],
    }, index=indices_revision).sort_values(
        "Posibilidad estimada de compra (%)", ascending=False,
    )
    resultados["Posibilidad estimada de compra"] = resultados[
        "Posibilidad estimada de compra (%)"
    ].map(lambda valor: f"{valor:.0f}%")
    resultados = resultados.drop(columns="Posibilidad estimada de compra (%)")

    return {
        "matriz": matriz,
        "casos_revisados": len(y_revision),
        "recomendados": total_recomendados,
        "compradores_en_revision": compradores_en_revision,
        "compradores_encontrados": compradores_encontrados,
        "porcentaje_recomendados_que_compraron": compradores_encontrados / total_recomendados if total_recomendados else 0,
        "porcentaje_compradores_encontrados": compradores_encontrados / compradores_en_revision if compradores_en_revision else 0,
        "resultados": resultados,
    }


def mostrar(df):
    st.header("4. Aprender de campañas anteriores")
    st.markdown(
        "### ¿Podemos reconocer señales de interés antes de una campaña?\n\n"
        "El modelo revisa qué tenían en común algunos casos que compraron y luego intenta reconocer compradores "
        "en otros casos que dejó aparte. Así vemos si las señales ayudan a orientar una decisión de marketing."
    )
    st.info(
        "La base es sintética: esta práctica ayuda a aprender, pero no prueba cómo responderán clientes reales. "
        "Una señal relacionada con compra tampoco demuestra que un mensaje o promoción haya causado esa compra."
    )
    if OBJETIVO not in df.columns:
        st.error("No encontré el dato que indica si cada caso compró en la última campaña.")
        return

    st.subheader("Paso 1 · Elegir qué queremos anticipar")
    st.write("Usaremos el resultado de la campaña anterior: **compró** o **no compró**.")
    resultados = pd.to_numeric(df[OBJETIVO], errors="coerce").dropna()
    cantidad_compra = int((resultados == 1).sum())
    cantidad_no_compra = int((resultados == 0).sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Casos en el archivo", len(resultados))
    c2.metric("Compraron", cantidad_compra)
    c3.metric("No compraron", cantidad_no_compra)

    st.subheader("Paso 2 · Elegir señales que conoceríamos a tiempo")
    st.caption(
        "Selecciona intereses o interacciones que el equipo ya conocería antes de decidir a quién contactar. "
        "El identificador y el grupo preparado en el archivo se dejan fuera para que el modelo busque sus propias señales."
    )
    candidatas = [col for col in df.columns if col not in EXCLUIR]
    variables = st.multiselect(
        "¿Qué información del cliente tomamos en cuenta?",
        options=candidatas,
        default=candidatas,
        format_func=lambda col: NOMBRES.get(col, col),
        key="senales_modelo_mercadotecnia",
    )
    with st.expander("Antes de continuar: ¿cuándo se midieron estas señales?"):
        st.write(
            "Para anticipar una compra, la información debe existir antes de la campaña. "
            "Si una interacción ocurrió después del envío, incluirla podría dar al modelo una pista que el equipo no tendría al decidir."
        )

    st.subheader("Paso 3 · Decidir qué tan amplia será la lista para revisar")
    umbral = st.slider(
        "Señalar casos con posibilidad estimada de compra de al menos",
        min_value=20, max_value=80, value=50, step=5,
        format="%d%%",
        help="Un valor menor hace una lista más amplia y puede incluir más personas que al final no compran. Un valor mayor hace la lista más corta.",
        key="umbral_senal_modelo",
    ) / 100
    st.caption("El modelo aprende con tres cuartas partes de los casos y se revisa con la cuarta parte restante, que no usó para aprender.")

    if st.button("Ver qué tan bien reconoce a quienes compran", type="primary", key="iniciar_modelo_mercadotecnia"):
        if not variables:
            st.warning("Elige al menos una señal para que el modelo pueda hacer la comparación.")
            return
        try:
            st.session_state["resultado_modelo_mercadotecnia"] = _aprender_y_revisar(
                df, variables, umbral
            )
            st.session_state["config_modelo_mercadotecnia"] = (variables, umbral)
        except ImportError as error:
            paquete = getattr(error, "name", None) or "una dependencia del modelo"
            st.error(f"No se encontró {paquete} en el entorno de Python que abrió esta app.")
            st.caption(f"Entorno activo: {sys.executable}")
            st.write("Detén el Streamlit actual con **Ctrl + C** en su terminal y vuelve a abrir la app con el entorno que ya tiene las dependencias instaladas:")
            st.code(r".\stream_train_ml\Scripts\python.exe -m streamlit run app.py", language="powershell")
            return
        except ValueError as error:
            st.error(str(error))
            return

    resultado = st.session_state.get("resultado_modelo_mercadotecnia")
    if resultado is None or st.session_state.get("config_modelo_mercadotecnia") != (variables, umbral):
        st.info("Elige las señales y pulsa el botón para ver la comparación.")
        return

    st.subheader("Paso 4 · Revisar qué encontró")
    encontrados = resultado["compradores_encontrados"]
    recomendados = resultado["recomendados"]
    compradores = resultado["compradores_en_revision"]
    m1, m2 = st.columns(2)
    m1.metric(
        "De cada 10 casos señalados, cuántos compraron",
        f"{resultado['porcentaje_recomendados_que_compraron'] * 10:.1f} de 10",
        help="Un valor mayor significa que la lista fue más precisa, aunque quizá deje fuera a algunos compradores.",
    )
    m2.metric(
        "De cada 10 compradores, a cuántos encontró",
        f"{resultado['porcentaje_compradores_encontrados'] * 10:.1f} de 10",
        help="Un valor mayor significa que encontró a más compradores, aunque la lista podría incluir más casos que no compren.",
    )
    st.write(
        f"En los {resultado['casos_revisados']} casos apartados para esta revisión, señaló {recomendados} para considerar. "
        f"Entre ellos, {encontrados} sí compraron. Del total de {compradores} compradores en esa revisión, "
        f"encontró {encontrados} y no detectó {resultado['matriz'][1, 0]}."
    )
    with st.expander("Ver el detalle de aciertos y errores"):
        matriz = resultado["matriz"]
        st.dataframe(
            pd.DataFrame(
                [[int(matriz[1, 1]), int(matriz[1, 0])], [int(matriz[0, 1]), int(matriz[0, 0])]],
                index=["Sí compraron", "No compraron"],
                columns=["El modelo los señaló", "El modelo no los señaló"],
            ),
            use_container_width=True,
        )
        st.caption("Una lista más amplia puede encontrar más compradores, pero también puede incluir más personas que no compren.")

    st.subheader("Paso 5 · Llevarlo a una decisión de marketing")
    st.write(
        "Estos son algunos casos apartados para la revisión. La posibilidad estimada resume lo que el modelo aprendió; "
        "no es una promesa de compra ni debe convertirse automáticamente en una lista de envío."
    )
    st.dataframe(resultado["resultados"].head(10), hide_index=True, use_container_width=True)
    st.markdown(
        "**Para decidir:** ¿conviene una lista amplia que encuentre más compradores o una lista pequeña con menos contactos que no compran? "
        "¿Qué prueba de campaña permitiría comprobar la idea con clientes reales?"
    )
