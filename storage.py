"""
Speicherschicht für das RFN Sponsoring Cockpit.

• Supabase (dauerhaft, empfohlen):  SUPABASE_URL + SUPABASE_KEY in den Streamlit-Secrets
• Lokale Datei (Fallback):          data/store.json – auf Streamlit Cloud NICHT dauerhaft

Datenmodell: einfache Schlüssel/Wert-Tabelle (key text, value jsonb)
  clubs              → Liste der Vereine inkl. Leistungskatalog
  leads:<verein_id>  → Unternehmen/Sponsoren eines Vereins
  catalog            → globale Leistungsvorlage
  settings           → Provisionsmodell, Team
  runs               → Recherche-Historie
"""
import json, os
import requests

TABLE = "rfn_store"
LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "store.json")


def _secret(name):
    # Umgebungsvariable zuerst – funktioniert auch in Hintergrund-Threads ohne Streamlit-Kontext
    if os.environ.get(name):
        return os.environ[name]
    try:
        import streamlit as st
        return str(st.secrets.get(name, "") or "")
    except Exception:
        return ""


def _cfg():
    return _secret("SUPABASE_URL").rstrip("/"), _secret("SUPABASE_KEY")


def is_remote():
    url, key = _cfg()
    return bool(url and key)


def _headers(key):
    h = {"apikey": key, "Content-Type": "application/json"}
    # Neue Supabase-Keys (sb_secret_…) sind keine JWTs → nur apikey-Header
    if not key.startswith("sb_"):
        h["Authorization"] = f"Bearer {key}"
    return h


def load_all():
    url, key = _cfg()
    if url and key:
        r = requests.get(f"{url}/rest/v1/{TABLE}", params={"select": "key,value"},
                         headers=_headers(key), timeout=20)
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase {r.status_code}: {r.text[:200]}")
        return {row["key"]: row["value"] for row in r.json()}
    if os.path.exists(LOCAL_PATH):
        with open(LOCAL_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save(k, v):
    url, key = _cfg()
    if url and key:
        h = _headers(key)
        h["Prefer"] = "resolution=merge-duplicates,return=minimal"
        r = requests.post(f"{url}/rest/v1/{TABLE}", params={"on_conflict": "key"},
                          json=[{"key": k, "value": v}], headers=h, timeout=30)
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase {r.status_code}: {r.text[:200]}")
        return
    os.makedirs(os.path.dirname(LOCAL_PATH), exist_ok=True)
    data = {}
    if os.path.exists(LOCAL_PATH):
        with open(LOCAL_PATH, encoding="utf-8") as f:
            data = json.load(f)
    data[k] = v
    tmp = LOCAL_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, LOCAL_PATH)


def delete(k):
    url, key = _cfg()
    if url and key:
        r = requests.delete(f"{url}/rest/v1/{TABLE}", params={"key": f"eq.{k}"},
                            headers=_headers(key), timeout=20)
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase {r.status_code}: {r.text[:200]}")
        return
    if os.path.exists(LOCAL_PATH):
        with open(LOCAL_PATH, encoding="utf-8") as f:
            data = json.load(f)
        data.pop(k, None)
        with open(LOCAL_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)


def load(k, default=None):
    """Einen einzelnen Eintrag frisch aus dem Speicher laden."""
    url, key = _cfg()
    if url and key:
        r = requests.get(f"{url}/rest/v1/{TABLE}", params={"select": "value", "key": f"eq.{k}"},
                         headers=_headers(key), timeout=30)
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase {r.status_code}: {r.text[:200]}")
        rows = r.json()
        return rows[0]["value"] if rows else default
    if os.path.exists(LOCAL_PATH):
        with open(LOCAL_PATH, encoding="utf-8") as f:
            return json.load(f).get(k, default)
    return default
