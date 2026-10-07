"""
RFN Sponsoren-Recherche – Web-Dashboard (Streamlit)
Start lokal:  streamlit run app.py
Online:       Streamlit Community Cloud (siehe DEPLOY.md)
"""
import io, time
import streamlit as st
import pandas as pd
import recherche_pro as rp

# ─────────────────────────── Seite & Design ───────────────────────────
st.set_page_config(page_title="RFN Sponsoren-Recherche", page_icon="🏟️", layout="wide")
G, Y = "#003D30", "#D6FF29"
st.markdown(f"""
<style>
  .stApp {{ background: #f1efe8; }}
  header[data-testid="stHeader"] {{ background: {G}; }}
  h1, h2, h3 {{ color: {G} !important; }}
  .rfn-hdr {{ background:{G}; color:white; padding:18px 24px; border-radius:14px; margin-bottom:18px; }}
  .rfn-hdr b {{ color:{Y}; font-size:20px; }}
  .rfn-hdr span {{ color:rgba(255,255,255,.7); font-size:13px; }}
  div[data-testid="stMetric"] {{ background:white; border:1px solid rgba(0,0,0,.08); border-radius:12px; padding:12px 16px; }}
  .stButton>button[kind="primary"] {{ background:{G}; color:{Y}; border:none; font-weight:600; }}
  .stDownloadButton>button {{ background:{G}; color:{Y}; border:none; font-weight:600; }}
  section[data-testid="stSidebar"] {{ background:#e8e6df; }}
</style>""", unsafe_allow_html=True)

# ─────────────────────────── Zugangsschutz ───────────────────────────
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "")
if APP_PASSWORD:
    if not st.session_state.get("auth_ok"):
        st.markdown('<div class="rfn-hdr"><b>🏟️ RFN Sponsoren-Recherche</b><br><span>Bitte anmelden</span></div>', unsafe_allow_html=True)
        pw = st.text_input("Zugangspasswort", type="password")
        if st.button("Anmelden", type="primary"):
            if pw == APP_PASSWORD:
                st.session_state.auth_ok = True; st.rerun()
            else:
                st.error("Falsches Passwort.")
        st.stop()

st.markdown('<div class="rfn-hdr"><b>🏟️ RFN Sponsoren-Recherche</b><br><span>Unternehmen im Umkreis finden · E-Mail & Telefon · Branche & Unternehmensgröße · Excel-Export</span></div>', unsafe_allow_html=True)

# ─────────────────────────── Eingaben (Sidebar) ───────────────────────────
with st.sidebar:
    st.markdown("### Neuer Suchauftrag")
    verein = st.text_input("Verein", "FC Bad Pyrmont Hagen")
    adresse = st.text_input("Start-Adresse (Straße Nr, PLZ Ort)", "Parkstraße 7, 31812 Bad Pyrmont")
    radius = st.slider("Radius (km)", 1, 50, 15)
    labels = {k: v[0] for k, v in rp.BRANCHEN.items()}
    sel = st.multiselect("Branchen", options=list(labels.keys()), default=list(labels.keys()), format_func=lambda k: labels[k])
    scrape = st.checkbox("Impressen durchsuchen (E-Mails, Firmeninfos)", True, help="Langsamer, aber liefert E-Mails, Rechtsform, Mitarbeiterzahl.")

    # Google-Key: bevorzugt aus Secrets (unsichtbar für Nutzer), sonst Eingabe
    key_secret = st.secrets.get("GOOGLE_API_KEY", "")
    if key_secret:
        st.success("Google Places aktiv (Key hinterlegt)")
        google_key = key_secret
    else:
        google_key = st.text_input("Google-API-Key (leer = OpenStreetMap)", type="password")
        st.caption("Ohne Key läuft die Suche über OpenStreetMap – weniger Treffer, E-Mails trotzdem aus Impressen.")

    start = st.button("🔍 Recherche starten", type="primary", use_container_width=True, disabled=not sel)

# ─────────────────────────── Lauf ───────────────────────────
if start:
    if not adresse.strip():
        st.error("Bitte eine Adresse eingeben."); st.stop()
    log_box = st.container()
    with st.status("Recherche läuft …", expanded=True) as status:
        pbar = st.progress(0, text="Starte …")
        logs = []
        log_area = st.empty()

        def on_log(msg):
            logs.append(msg); log_area.markdown("<br>".join(f"<span style='font-size:13px'>{m}</span>" for m in logs[-12:]), unsafe_allow_html=True)
        def on_prog(i, n, text):
            pbar.progress(min(1.0, i / max(n, 1)), text=f"{i}/{n} · {text[:60]}")

        rp.LOG, rp.PROGRESS = on_log, on_prog
        t0 = time.time()
        try:
            _, rows = rp.run(verein, adresse, radius, sel, google_key.strip(), scrape=scrape, write=False)
            st.session_state.rows = rows
            st.session_state.meta = dict(verein=verein, adresse=adresse, radius=radius,
                                         quelle="Google Places" if google_key.strip() else "OpenStreetMap",
                                         dauer=round(time.time() - t0))
            pbar.progress(1.0, text="Fertig")
            status.update(label=f"✓ Fertig – {len(rows)} Unternehmen in {round(time.time()-t0)} s", state="complete", expanded=False)
        except SystemExit as e:
            status.update(label="Abgebrochen", state="error"); st.error(str(e)); st.stop()
        except Exception as e:
            status.update(label="Fehler", state="error"); st.exception(e); st.stop()
        finally:
            rp.LOG, rp.PROGRESS = print, None

# ─────────────────────────── Ergebnisse ───────────────────────────
rows = st.session_state.get("rows")
if not rows:
    st.info("👈 Links Adresse, Radius und Branchen wählen und **Recherche starten**.")
    with st.expander("Was das Tool macht"):
        st.markdown("""
- **Exakte Adresse** als Mittelpunkt, Radius bis 50 km, Entfernung je Firma
- **Google Places** als Hauptquelle (Fallback OpenStreetMap)
- **Impressum-Scraping**: E-Mail, Ansprechpartner, Rechtsform, Handelsregister, Mitarbeiter, Gründung
- **Unternehmensgröße** nach EU-KMU-Definition (Kleinst < 10 · Klein < 50 · Mittel < 250 · Groß ≥ 250), Ketten-Filialen markiert
- **Excel** mit Leads + Übersicht, farbcodiert, filterbar
""")
    st.stop()

meta = st.session_state.meta
df = pd.DataFrame(rows)
df["Status"] = df.apply(lambda r: "E-Mail vorhanden" if r["email"] else ("Anruf nötig" if r["telefon"] else "kein Kontakt"), axis=1)

# Kennzahlen
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Unternehmen", len(df))
c2.metric("Mit E-Mail", int((df["email"] != "").sum()))
c3.metric("Anruf nötig", int((df["Status"] == "Anruf nötig").sum()))
c4.metric("Ø Score", round(df["score"].mean(), 1) if len(df) else 0)
c5.metric("Dauer", f"{meta['dauer']} s")
st.caption(f"**{meta['verein']}** · {meta['radius']} km um {meta['adresse']} · Quelle: {meta['quelle']}")

# Filter
f1, f2, f3, f4 = st.columns([2, 2, 2, 3])
fb = f1.multiselect("Branche", sorted(df["branche"].unique()), default=sorted(df["branche"].unique()))
fg = f2.multiselect("Größe", sorted(df["groesse"].unique(), key=lambda g: -rp.SIZE_ORDER.get(g, 0)),
                    default=sorted(df["groesse"].unique(), key=lambda g: -rp.SIZE_ORDER.get(g, 0)))
fs = f3.multiselect("Status", ["E-Mail vorhanden", "Anruf nötig", "kein Kontakt"], default=["E-Mail vorhanden", "Anruf nötig", "kein Kontakt"])
q = f4.text_input("Suche (Firma, Ort, Ansprechpartner)")

v = df[df["branche"].isin(fb) & df["groesse"].isin(fg) & df["Status"].isin(fs)]
if q:
    ql = q.lower()
    v = v[v.apply(lambda r: ql in f"{r['firma']} {r['adresse']} {r.get('ansprechpartner','')}".lower(), axis=1)]

# Tabelle
show = v[["firma", "branche", "groesse", "dist_km", "telefon", "email", "ansprechpartner", "website",
          "rechtsform", "mitarbeiter", "score", "Status", "rating", "reviews"]].rename(columns={
    "firma": "Firma", "branche": "Branche", "groesse": "Größe", "dist_km": "km", "telefon": "Telefon",
    "email": "E-Mail", "ansprechpartner": "Ansprechpartner", "website": "Website", "rechtsform": "Rechtsform",
    "mitarbeiter": "MA", "score": "Score", "rating": "★", "reviews": "Bew."})
show["km"] = show["km"].round(1)
st.dataframe(show, use_container_width=True, hide_index=True, height=520,
             column_config={"Website": st.column_config.LinkColumn("Website"),
                            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d")})
st.caption(f"{len(v)} von {len(df)} Unternehmen angezeigt")

# Übersicht
with st.expander("Übersicht nach Branche und Größe"):
    a, b = st.columns(2)
    a.dataframe(df.groupby("branche").agg(Anzahl=("firma", "count"), mit_EMail=("email", lambda s: int((s != "").sum()))).rename_axis("Branche"), use_container_width=True)
    b.dataframe(df.groupby("groesse").agg(Anzahl=("firma", "count"), mit_EMail=("email", lambda s: int((s != "").sum()))).rename_axis("Größe"), use_container_width=True)

# Excel-Download (gesamt + gefiltert)
def excel_bytes(subset):
    import os, tempfile
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            fname = rp.write_excel(list(subset), meta["verein"], meta["adresse"], meta["radius"], meta["quelle"])
            data = open(fname, "rb").read()
        finally:
            os.chdir(cwd)
    return data, fname

d1, d2 = st.columns(2)
data_all, name_all = excel_bytes(rows)
d1.download_button("⬇️ Excel – alle Unternehmen", data_all, file_name=name_all,
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
if len(v) != len(df):
    sel_rows = [r for r in rows if r["firma"] in set(v["firma"])]
    data_f, name_f = excel_bytes(sel_rows)
    d2.download_button(f"⬇️ Excel – gefilterte Auswahl ({len(v)})", data_f, file_name=name_f.replace(".xlsx", "_Auswahl.xlsx"),
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
