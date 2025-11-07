import streamlit as st
from google import genai

# Configuración de la página
st.set_page_config(page_title="Templo de las musas  de la Historias ", layout="centered")
st.title("Altar  de  plegarias")
st.markdown("Ruega a las musas  por su inspiracion y que te iluminene  en tu arte")

# Input de la API key (seguridad)
api_key = "AIzaSyD9Am4Kxos0ECIYHpyhJxRxcDiDptS9fLw"

# Selección de modo
modo = st.selectbox("Selecciona qué deseas crear:", ["Personaje ", "Historia "])

# Parámetros adicionales según el modo
if modo == "Personaje ":
    nombre = st.text_input("Nombre del personaje (opcional):")
    genero = st.selectbox("Género del personaje:", ["Masculino", "Femenino", "No binario", "Otro"])
    tipo = st.selectbox("Tipo de personaje:", ["Héroe", "Villano", "Secundario", "Maestro", "Criatura mágica"])
    ambientacion = st.text_input("Ambientación (opcional):", placeholder="Ej. mundo futurista, escuela mágica, etc.")
    prompt = f"""
    Crea un personaje original de anime.
    Nombre: {nombre or "a elección"}.
    Género: {genero}.
    Tipo: {tipo}.
    Ambientación: {ambientacion or "a elección"}.
    Describe su apariencia, personalidad, poderes o habilidades, trasfondo y motivación.
    Presenta la respuesta en formato narrativo y visualmente atractivo.
    """

else:  # Historia
    genero_historia = st.selectbox("Género de la historia:", ["Acción", "Romance", "Fantasía", "Terror", "Ciencia ficción", "Comedia"])
    duracion = st.selectbox("Extensión de la historia:", ["Corta (1 párrafo)", "Media (2-3 párrafos)", "Larga (5 párrafos o más)"])
    tema = st.text_input("Tema central (opcional):", placeholder="Ej. la amistad, la venganza, el sacrificio, etc.")
    prompt = f"""
    Crea una historia original de anime.
    Género: {genero_historia}.
    Extensión: {duracion}.
    Tema central: {tema or "a elección"}.
    Describe personajes, ambientación y conflicto principal.
    Da un título atractivo y un cierre inspirador.
    """

# Botón para generar
if st.button("Eleva tu plegaria  ala   musas"):
    if not api_key:
        st.error("Por favor, ingresa tu API Key de Google GenAI.")
    else:
        try:
            with st.spinner("Las musas  atienden a tu llamado"):
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-2.0-flash", 
                    contents=prompt
                )
                resultado = response.text
            st.success("Las diosas han respondido a tu ruego")
            st.markdown(resultado)
        except Exception as e:
            st.error(f"Error al generar: {str(e)}")

else:
    st.info("Selecciona una opción, completa los campos y haz clic en **Que las musas  te den su inspiracion**.")

# Pie de página
st.markdown("---")
st.caption("Que esta sea tu musa  para grandes historias ")
