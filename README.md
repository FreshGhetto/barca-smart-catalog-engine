# BARCA Smart Catalog Engine

Sistema modulare per la generazione automatica di cataloghi prodotto a partire da report CSV grezzi.

Il progetto consente di:

- Pulire automaticamente export CSV impaginati (ANART report)
- Estrarre dati strutturati prodotto
- Calcolare KPI (sell-through, giacenza, ecc.)
- Generare catalogo fotografico automatico
- Scaricare immagini prodotto dal sito
- Creare ZIP con:
  - Card prodotto impaginate (A6)
  - Cartella immagini raw
  - Report immagini mancanti

---

## 🏗 Architettura Modulare

Il sistema è diviso in moduli indipendenti:

- `barca_parser.py`  
  Pulizia e normalizzazione CSV grezzo.

- `barca_heel.py`  
  Estrazione altezza tacco dalla descrizione prodotto.

- `barca_image_fetcher.py`  
  Download immagini tramite logica del catalog generator originale.

- `barca_layout.py`  
  Layout grafico A6 (foto + box informazioni).

- `barca_engine.py`  
  Generazione catalogo ZIP finale.

- `app.py`  
  Interfaccia web Streamlit per orchestrare il flusso.

---

## ⚙️ Requisiti

- Python 3.10+
- pip

Installazione dipendenze:

```bash
pip install -r requirements.txt
