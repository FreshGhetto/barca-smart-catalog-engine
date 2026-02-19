
import streamlit as st
import pandas as pd
from io import StringIO

from barca_parser import clean_anart_report_bytes, decode_best_effort
from barca_heel import extract_heel_mm_from_descr
from barca_models import CatalogItem
from barca_engine import generate_catalog_zip

st.set_page_config(page_title="BARCA - Cleaner + Catalogo", layout="wide")
st.title("BARCA - Cleaner CSV + Catalogo con Foto")

mode = st.radio("Modalità", ["1) Pulisci CSV grezzo (ANART report)", "2) Usa CSV già pulito"], index=0)
up = st.file_uploader("Carica CSV", type=["csv"])

df = None
if up:
    data = up.getvalue()

    if mode.startswith("1)"):
        df = clean_anart_report_bytes(data)
        if df.empty:
            st.error("Non sono riuscito a estrarre righe articolo dal CSV grezzo.")
            st.stop()

        # tacco da descrizione
        df["tacco_mm"] = df["product"].apply(extract_heel_mm_from_descr)

        st.success(f"OK! Estratti {len(df)} articoli dal report.")
        st.dataframe(df.head(300), use_container_width=True)

        st.download_button(
            "Scarica CSV pulito",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="anart_clean.csv",
            mime="text/csv"
        )
    else:
        text = decode_best_effort(data)
        df = pd.read_csv(StringIO(text))
        df.columns = [str(c).lower().strip() for c in df.columns]
        if "tacco_mm" not in df.columns and "product" in df.columns:
            df["tacco_mm"] = df["product"].apply(extract_heel_mm_from_descr)

    df.columns = [str(c).lower().strip() for c in df.columns]

    # required columns for catalog
    required = ["fornitore","code","product","consegnate","vendute","giacenza","tacco_mm"]
    miss = [c for c in required if c not in df.columns]
    if miss:
        st.error(f"Mancano colonne obbligatorie: {miss}")
        st.write("Colonne trovate:", list(df.columns))
        st.stop()

    # numeric + percent
    for c in ["consegnate","vendute","giacenza"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    df["perc_vendita"] = (df["vendute"] / df["consegnate"].replace({0: pd.NA})) * 100
    df["perc_vendita"] = pd.to_numeric(df["perc_vendita"], errors="coerce").fillna(0)

    st.subheader("Filtri")
    giac_min = st.number_input("Giacenza > ", value=80, step=1)
    perc_min = st.number_input("% Vendita > ", value=64.0, step=0.5)

    # optional filters
    if "reparto" in df.columns:
        reps = ["(Tutti)"] + sorted([x for x in df["reparto"].dropna().unique().tolist() if str(x).strip()])
        rep = st.selectbox("Reparto", reps)
        if rep != "(Tutti)":
            df = df[df["reparto"] == rep]

    if "categoria" in df.columns:
        cats = ["(Tutti)"] + sorted([x for x in df["categoria"].dropna().unique().tolist() if str(x).strip()])
        cat = st.selectbox("Categoria", cats)
        if cat != "(Tutti)":
            df = df[df["categoria"] == cat]

    forn_opts = ["(Tutti)"] + sorted([x for x in df["fornitore"].dropna().unique().tolist() if str(x).strip()])
    forn = st.selectbox("Fornitore", forn_opts)
    if forn != "(Tutti)":
        df = df[df["fornitore"] == forn]

    df = df[(df["giacenza"] > giac_min) & (df["perc_vendita"] > perc_min)]

    st.subheader("Ordinamento")
    sort_field = st.selectbox("Ordina per", ["perc_vendita","giacenza","consegnate","vendute","tacco_mm"])
    sort_order = st.radio("Ordine", ["Decrescente","Crescente"])
    asc = (sort_order == "Crescente")
    df = df.sort_values(by=sort_field, ascending=asc)

    st.caption(f"Articoli dopo filtri: {len(df)}")
    st.dataframe(df, use_container_width=True)

    st.subheader("Catalogo con foto (download Barca invariato)")
    folder_name = st.text_input("Nome cartella output nello ZIP", value="BARCA")

    if st.button("Crea ZIP Catalogo"):
        items = []
        for _, r in df.iterrows():
            items.append(CatalogItem(
                code=str(r["code"]).strip(),
                product=str(r["product"]).strip(),
                supplier=str(r["fornitore"]).strip(),
                consegnate=int(r["consegnate"]),
                vendute=int(r["vendute"]),
                giacenza=int(r["giacenza"]),
                perc_vendita=float(r["perc_vendita"]),
                tacco_mm=float(r["tacco_mm"]) if pd.notna(r["tacco_mm"]) else None,
            ))
        zip_bytes = generate_catalog_zip(items, folder_name=folder_name)
        st.download_button("Scarica ZIP", data=zip_bytes, file_name="barca_catalog.zip", mime="application/zip")
