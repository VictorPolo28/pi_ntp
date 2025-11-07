
from datetime import datetime
import pandas as pd
import numpy as np  #cálculos numéricos y científicos.
import streamlit as st
import plotly.express as px
import io #flujos de entrada y salida (input/output streams).

st.set_page_config(page_title="Anime Explorer — Streamlit + Pandas", layout="wide", initial_sidebar_state="expanded")

@st.cache_data(ttl=600)
def load_data(csv_path: str):
    # Lee el CSV 
    df = pd.read_csv(csv_path, low_memory=False)
    # Normalizar nombres de columnas quita espacios extremos
    df.columns = [c.strip() for c in df.columns]
   
    for col in ["Aired From", "AiredTo", "Aired To", "Aired From"]:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except Exception:
                df[col] = pd.to_datetime(df[col].astype(str), errors="coerce")

    # Años derivados
    if "Aired From" in df.columns:
        df["start_year"] = df["Aired From"].dt.year
    else:
        df["start_year"] = pd.NA

    #  validar que la  informacion  es string 
    if "Genres" in df.columns:
        df["Genres"] = df["Genres"].fillna("").astype(str)
    else:
        df["Genres"] = ""

    # Score 
    for col in ["Score", "score"]:
        if col in df.columns:
            df["Score"] = pd.to_numeric(df[col], errors="coerce")
            break
    df["Score"] = pd.to_numeric(df.get("Score"), errors="coerce")

    #  ajusta los espacio  para las columnas  de texto
    for text_col in ["Title", "Title English", "Title Japanese", "Synopsis", "Studios"]:
        if text_col in df.columns:
            df[text_col] = df[text_col].astype(str).replace("nan", "")
    return df

def multi_genre_explode(df, genre_column="Genres"):
    # Devuelve listado unico de géneros y funcion para filtrar por por selectores multiples
    unique_genres = set()
    for g in df[genre_column].dropna().astype(str):
        if g.strip() == "":
            continue
        # asumir separador ',' o ajustar en caso de que sea un separador diferente
        parts = [x.strip() for x in g.split(",")]
        unique_genres.update([p for p in parts if p])
    return sorted(unique_genres)


#### Parte de aplicado  extenso  de los filtros 

def filter_dataframe(df, filters):
    q = df.copy()
    # Tipo
    if filters["types"]:
        q = q[q["Type"].isin(filters["types"])]
    # estado
    if filters["status"]:
        q = q[q["Status"].isin(filters["status"])]
    # Score
    q = q[(q["Score"].isna()) | ((q["Score"] >= filters["score_min"]) & (q["Score"] <= filters["score_max"]))]
    # año
    if filters["year_min"] or filters["year_max"]:
        # permite años perdidos
        yr_min = filters["year_min"]
        yr_max = filters["year_max"]
        q = q[((q["start_year"].isna()) & filters["include_missing_years"]) |
               ((q["start_year"].notna()) & (q["start_year"] >= yr_min) & (q["start_year"] <= yr_max))]
    # multiples generos
    if filters["genres"]:
        mask = np.zeros(len(q), dtype=bool)
        for g in filters["genres"]:
            # me permite incluir mas  de  un genero para filtrarlo
            mask |= q["Genres"].str.contains(rf"\b{pd.regex.escape(g)}\b", na=False)
        q = q[mask]
    # buscador 
    if filters["search_text"]:
        txt = filters["search_text"].lower()
        txt_mask = q["Title"].str.lower().str.contains(txt, na=False) | q["Synopsis"].str.lower().str.contains(txt, na=False) | q["Title English"].str.lower().str.contains(txt, na=False)
        q = q[txt_mask]
    # orenar la lista de forma acendente 
    if filters["sort_by"]:
        q = q.sort_values(by=filters["sort_by"], ascending=filters["sort_asc"])
    return q

def to_csv_bytes(df):
    out = io.BytesIO()
    df.to_csv(out, index=False)
    return out.getvalue()



#parte de estilos 
st.markdown(
    """
    <style>
    /* Estilo oscuro/suave para la app */
    .reportview-container { background: #0b0f14; color: #e6eef3; }
    .stButton>button { border-radius: 8px; }
    .big-title { font-size:30px; font-weight:700; color:#ffffff; margin-bottom:8px; }
    .subtle { color:#9aa6b2; }
    </style>
    """, unsafe_allow_html=True
)

st.sidebar.title("Filtros")
csv_path = st.sidebar.text_input("Ruta CSV", value="anime-dataset-2025.csv", help="Pon el nombre del CSV (ej: anime_dataset.csv).")
load_button = st.sidebar.button("Cargar datos")

# Cargar datos si existe
if not csv_path:
    st.sidebar.error("Proporciona la ruta al CSV.")
    st.stop()

df = None
try:
    df = load_data(csv_path)
except Exception as e:
    st.sidebar.error(f"No se pudo leer el CSV: {e}")
    st.stop()

# Calida   de los datos 
st.sidebar.markdown("### Calidad de datos")
missing_summary = (df.isna().mean() * 100).round(2)
top_missing = missing_summary.sort_values(ascending=False).head(8)
for col, pct in top_missing.items():
    st.sidebar.write(f"{col}: {pct}% faltante")

# Filter widgets values
types = sorted(df["Type"].dropna().unique()) if "Type" in df.columns else []
status = sorted(df["Status"].dropna().unique()) if "Status" in df.columns else []
unique_genres = multi_genre_explode(df, "Genres")

selected_types = st.sidebar.multiselect("Tipo", options=types, default=None)
selected_status = st.sidebar.multiselect("Estado", options=status, default=None)
selected_genres = st.sidebar.multiselect("Generos", options=unique_genres, default=None)

score_min, score_max = st.sidebar.slider("Score range", min_value=0.0, max_value=10.0, value=(0.0, 10.0), step=0.1)
year_min = int(df["start_year"].dropna().min()) if df["start_year"].dropna().shape[0] > 0 else 1900
year_max = int(df["start_year"].dropna().max()) if df["start_year"].dropna().shape[0] > 0 else datetime.today().year
selected_years = st.sidebar.slider("Start year range", min_value=year_min, max_value=year_max, value=(year_min, year_max))
include_missing_years = st.sidebar.checkbox("Incluir animes sin año conocido", value=True)
search_text = st.sidebar.text_input("Buscar título / sinopsis")
sort_by = st.sidebar.selectbox("Ordenar por", options=[None] + [c for c in df.columns if df[c].dtype in [np.number, float, int] or c in ["Score","Members"]], index=0)
sort_asc = st.sidebar.checkbox("Orden ascendente", value=False)

# Filtro de objeto
filters = {
    "types": selected_types,
    "status": selected_status,
    "genres": selected_genres,
    "score_min": score_min,
    "score_max": score_max,
    "year_min": selected_years[0],
    "year_max": selected_years[1],
    "include_missing_years": include_missing_years,
    "search_text": search_text,
    "sort_by": sort_by,
    "sort_asc": sort_asc
}


#layout 
st.markdown('<div class="big-title">Anime Explorer Conoce las estadisticas de los animes de eras pasada</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">Explora, filtra y visualiza tu archivo. </div>', unsafe_allow_html=True)
st.write("---")

# Data quality panel
with st.expander(" Resumen de dataset y calidad de datos", expanded=True):
    st.write(f"**Filas:** {len(df):,}   —   **Columnas:** {df.shape[1]}")
    st.write("Valores faltantes por columna (porcentaje):")
    st.dataframe(missing_summary.sort_values(ascending=False).head(30).to_frame("pct_missing").style.format("{:.2f}%"))

# Aplicar filtros
filtered = filter_dataframe(df, filters)
st.markdown(f"### Resultados filtrados: {len(filtered):,} filas")

# Top KPIs row
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Filas originales", f"{len(df):,}")
with k2:
    st.metric("Filas filtradas", f"{len(filtered):,}")
with k3:
    mean_score = filtered["Score"].mean(skipna=True)
    st.metric("Score promedio", f"{mean_score:.2f}" if not np.isnan(mean_score) else "N/A")
with k4:
    st.metric("Favoritos avg", f"{filtered.get('Favorites', pd.Series(dtype=float)).mean():.0f}")



# Gráficas

st.markdown("## Visualizaciones")

col1, col2 = st.columns([2,1])
with col1:
    st.markdown("### Distribución de Score")
    fig_score = px.histogram(filtered, x="Score", nbins=30, title="Distribución de Score (filtrado)", marginal="box")
    st.plotly_chart(fig_score, use_container_width=True)

    st.markdown("### Score vs Miembros (personas que dieron una calificación)")
    if "Members" in filtered.columns:
        fig_scatter = px.scatter(filtered, x="Members", y="Score", hover_data=["Title", "Type", "Status"], title="Score vs Miembros", log_x=True)
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Columna 'Members' no encontrada en el dataset.")

with col2:
    st.markdown("### Top géneros (conteo)")
    # contar géneros
    genre_counts = {}
    for row in filtered["Genres"].dropna().astype(str):
        if row.strip()=="":
            continue
        for g in [x.strip() for x in row.split(",")]:
            if g:
                genre_counts[g] = genre_counts.get(g, 0) + 1
    genre_df = pd.DataFrame.from_dict(genre_counts, orient="index", columns=["count"]).sort_values("count", ascending=False).reset_index().rename(columns={"index":"genre"})
    if not genre_df.empty:
        fig_gen = px.bar(genre_df.head(20), x="count", y="genre", orientation="h", title="Top géneros")
        st.plotly_chart(fig_gen, use_container_width=True)
    else:
        st.info("No se encontraron géneros en el dataset filtrado.")

st.markdown("### Series temporales (número de lanzamientos por año)")
if "start_year" in filtered.columns:
    ts = filtered.dropna(subset=["start_year"]).groupby("start_year").size().reset_index(name="count")
    if not ts.empty:
        fig_ts = px.line(ts, x="start_year", y="count", title="Animes por año (start_year)")
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.info("No hay años disponibles para mostrar la serie temporal.")
else:
    st.info("No se encontró columna de año de inicio.")


# Tabla y descarga

st.markdown("## Tabla de resultados")
# Seleccionar columnas más relevantes para mostrar (si existen)
display_cols = [c for c in ["Title", "Title English", "Type", "Source", "Episodes", "Status", "start_year", "Score", "Members", "Favorites", "Genres", "Synopsis"] if c in filtered.columns]
st.dataframe(filtered[display_cols].head(1000))  # mostrar hasta 1000 filas en UI

# Descargar CSV
csv_bytes = to_csv_bytes(filtered[display_cols])
st.download_button(label="Descargar CSV de resultados", data=csv_bytes, file_name="anime_filtrado.csv", mime="text/csv")


# Footer 

st.info("Datos  tomados   de un  dataset publico  si te intereza  mas esta informacion la base dedatos mas grande pertenece a MyAnimeList")

