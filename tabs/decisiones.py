"""Resume una propuesta de marketing y cómo aprender de una prueba."""

import streamlit as st


def _borrador_mensaje(propuesta):
    columna = propuesta["columna"]
    grupo = propuesta["grupo"]
    if columna == "producto_interes_principal_sintetico":
        return (
            f"Hola. Registramos tu interés en {grupo}. "
            "¿Qué te gustaría saber sobre este antojito?"
        )
    if columna == "producto_interes_secundario_sintetico":
        if grupo.lower() in {"ninguno", "sin dato"}:
            return "Hola. ¿Qué antojito de Tacos Yolis te interesa conocer?"
        return (
            f"Hola. Además de tu producto de mayor interés, también mencionaste {grupo}. "
            "¿Cuál te gustaría conocer mejor?"
        )
    if columna == "menciona_varios_antojitos_sintetico":
        if grupo == "Menciona varios antojitos":
            return (
                "Hola. Registramos tu interés en [producto principal] y [segundo antojito mencionado]. "
                "¿Cuál te gustaría conocer mejor?"
            )
        return "Hola. Registramos tu interés en [producto principal]. ¿Qué otro antojito te gustaría conocer?"
    if columna == "interes_salsa_molcajete_sintetico":
        if grupo == "Con interés":
            return "Hola. Registramos tu interés en salsa molcajete. ¿Qué te gustaría saber sobre ella?"
        return "Hola. ¿Qué antojito te interesa conocer? Queremos saber qué te gustaría probar."
    if "Explora" in grupo:
        return (
            "Hola. Registramos tu interés en [producto principal] y [segundo antojito mencionado]. "
            "¿Cuál te gustaría conocer mejor?"
        )
    producto = grupo.replace("Afinidad por ", "")
    return f"Hola. Registramos tu interés en {producto}. ¿Qué te gustaría saber sobre este antojito?"


def mostrar():
    st.header("6. Preparar una decisión")
    st.markdown(
        "### Pasar de una idea a una prueba que podamos medir\n\n"
        "Aquí reunimos a quién queremos atender, qué mensaje probar y cómo sabremos si la propuesta merece continuar."
    )

    propuesta = st.session_state.get("propuesta_marketing")
    if not propuesta:
        st.info("Primero abre la pestaña 5, elige un grupo y una acción. La propuesta aparecerá aquí.")
        return

    st.subheader("Paso 1 · Resumir la propuesta")
    c1, c2, c3 = st.columns(3)
    c1.metric("Grupo elegido", propuesta["grupo"])
    c2.metric("Personas en el grupo", f"{propuesta['personas']:,}")
    c3.metric("Compró en la campaña anterior", f"{propuesta['tasa_grupo']:.1%}")
    st.write(f"**Señal observada:** {propuesta['caracteristica']} · **Acción para probar:** {propuesta['accion']}")
    st.caption(
        f"En todo el archivo, la proporción que compró fue {propuesta['tasa_general']:.1%}. "
        "Estos datos ayudan a plantear la prueba; no garantizan el resultado futuro."
    )

    st.subheader("Paso 2 · Preparar un mensaje")
    firma = (propuesta["columna"], propuesta["grupo"], propuesta["accion"])
    if st.session_state.get("firma_mensaje_decision") != firma:
        st.session_state["firma_mensaje_decision"] = firma
        st.session_state["mensaje_decision"] = _borrador_mensaje(propuesta)
    st.text_area(
        "Borrador editable (no se envía desde esta aplicación)",
        key="mensaje_decision",
        height=110,
    )
    st.session_state.setdefault("responsable_decision", "Equipo de marketing")
    st.text_input("¿Quién dará el siguiente paso?", key="responsable_decision")

    st.subheader("Paso 3 · Acordar cómo medir el resultado")
    st.markdown(
        "1. Divide al azar a las personas del grupo en dos partes parecidas.\n"
        "2. Prueba el mensaje con una parte y deja a la otra con la comunicación habitual.\n"
        "3. Compara cuántas personas compran en cada parte."
    )
    st.success(
        "**Medida principal:** compras ÷ personas asignadas a cada parte. "
        "Usa el mismo periodo para ambos grupos y registra cuántas personas había en cada uno."
    )
    st.warning(
        "El archivo contiene casos sintéticos y no registra permisos de contacto, costos ni resultados de una prueba real. "
        "Antes de contactar clientes, confirma esos datos y las reglas de comunicación de la marca."
    )

    st.subheader("Resumen para compartir")
    responsable = st.session_state.get("responsable_decision", "Equipo de marketing")
    mensaje = st.session_state.get("mensaje_decision", "")
    resumen = (
        f"PROPUESTA DE MARKETING\n"
        f"Grupo: {propuesta['grupo']} ({propuesta['personas']} personas en los datos)\n"
        f"Evidencia: {propuesta['compradores']} de {propuesta['personas']} compraron en la campaña anterior "
        f"({propuesta['tasa_grupo']:.1%}). El promedio del archivo fue {propuesta['tasa_general']:.1%}.\n"
        f"Acción: {propuesta['accion']}\n"
        f"Responsable: {responsable}\n"
        f"Mensaje: {mensaje}\n"
        "Medición: comparar compras / personas asignadas entre el grupo que recibe el mensaje y el grupo de comparación."
    )
    st.code(resumen, language=None)
    st.download_button(
        "Descargar resumen de la propuesta",
        data=resumen,
        file_name="propuesta_marketing.txt",
        mime="text/plain",
        key="descargar_decision_marketing",
    )
