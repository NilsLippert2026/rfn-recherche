"""
═══════════════════════════════════════════════════════════════════
  Regionalfußball.net – Sponsoren-Recherche PRO
═══════════════════════════════════════════════════════════════════

Findet Unternehmen im Umkreis einer EXAKTEN ADRESSE, reichert sie mit
E-Mail, Telefon und Firmeninfos an, klassifiziert nach Branche und
Unternehmensgröße (EU-KMU-Definition) und schreibt eine fertige Excel.

Datenquelle:  Google Places (Hauptquelle, Key nötig)
              → automatischer Fallback auf OpenStreetMap ohne Key
E-Mails:      Impressum-Scraping der Firmenwebsites
Größe:        Mitarbeiterangabe · Rechtsform · Ketten-Erkennung · Bewertungen

Nutzung lokal:      python recherche_pro.py            (interaktiv)
                    python recherche_pro.py --adresse "Parkstraße 7, 31812 Bad Pyrmont" --radius 15
Nutzung Colab:      siehe recherche_pro.ipynb (Formularfelder, kein Terminal)

Einmalig:  pip install requests beautifulsoup4 openpyxl
═══════════════════════════════════════════════════════════════════
"""

import sys, re, time, math, argparse, os
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("\n❌ Bibliotheken fehlen. Einmalig ausführen:\n   pip install requests beautifulsoup4 openpyxl\n")
    sys.exit(1)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RFN-Sponsoring/2.0)"}

# ── Ausgabe-Hooks: Terminal standardmäßig, Dashboard setzt eigene Funktionen ──
LOG = print
PROGRESS = None   # callable(i, n, text) oder None → Terminal
def _prog(i, n, text):
    if PROGRESS: PROGRESS(i, n, text)
    else:
        sys.stdout.write(f"\r     {i}/{n}  {text[:46]:<46}"); sys.stdout.flush()
def _log(msg):
    LOG(msg)

# ═══════════════════════════════════════════════════════════════════
# BRANCHEN
# key → (Label, Google-Suchbegriffe, OSM-Tags)
# ═══════════════════════════════════════════════════════════════════
BRANCHEN = {
  "gastronomie": ("Gastronomie",
      ["restaurant", "cafe", "bar", "bakery"],
      [("amenity","restaurant"),("amenity","cafe"),("amenity","bar"),("amenity","fast_food"),("amenity","pub"),("shop","bakery"),("tourism","hotel")]),
  "handel": ("Handel",
      ["supermarket", "clothing_store", "hardware_store", "furniture_store", "store"],
      [("shop","supermarket"),("shop","convenience"),("shop","clothes"),("shop","hardware"),("shop","electronics"),("shop","furniture"),("shop","optician"),("shop","florist"),("shop","butcher"),("shop","jewelry"),("shop","doityourself"),("shop","shoes"),("shop","bakery"),("shop","kiosk"),("shop","mall"),("shop","department_store")]),
  "handwerk": ("Handwerk",
      ["electrician", "plumber", "roofing_contractor", "painter"],
      [("craft","electrician"),("craft","plumber"),("craft","carpenter"),("craft","painter"),("craft","roofer"),("craft","hvac"),("craft","locksmith"),("craft","builder"),("craft","gardener"),("craft","metal_construction"),("craft","tiler"),("craft","glaziery"),("craft","sawmill"),("craft","electronics_repair"),("shop","trade")]),
  "gesundheit": ("Gesundheit",
      ["doctor", "dentist", "pharmacy", "physiotherapist"],
      [("amenity","doctors"),("amenity","dentist"),("amenity","pharmacy"),("amenity","physiotherapist"),("amenity","clinic"),("amenity","veterinary"),("healthcare","doctor"),("healthcare","physiotherapist"),("healthcare","dentist"),("healthcare","alternative"),("shop","medical_supply"),("shop","optician"),("shop","hearing_aids")]),
  "automobil": ("Automobil",
      ["car_dealer", "car_repair", "gas_station"],
      [("shop","car"),("shop","car_repair"),("shop","car_parts"),("shop","tyres"),("shop","motorcycle"),("amenity","fuel"),("amenity","car_wash"),("amenity","car_rental")]),
  "finanzen": ("Finanzen & Versicherung",
      ["bank", "insurance_agency", "accounting"],
      [("amenity","bank"),("office","insurance"),("office","tax_advisor"),("office","financial_advisor"),("office","accountant"),("office","lawyer"),("office","notary")]),
  "dienstleistung": ("Dienstleistung & Büro",
      ["lawyer", "real_estate_agency", "hair_care", "beauty_salon"],
      [("office","estate_agent"),("office","architect"),("office","it"),("office","advertising_agency"),("office","company"),("office","employment_agency"),("shop","hairdresser"),("shop","beauty"),("shop","travel_agency"),("shop","dry_cleaning"),("shop","laundry"),("shop","funeral_directors"),("shop","photo"),("amenity","driving_school")]),
  "fitness": ("Sport & Freizeit",
      ["gym", "sporting_goods_store"],
      [("leisure","fitness_centre"),("leisure","sports_centre"),("leisure","swimming_pool"),("leisure","dance"),("shop","sports"),("shop","bicycle"),("shop","outdoor")]),
  "industrie": ("Industrie & Logistik",
      ["moving_company", "storage"],
      [("office","logistics"),("office","company"),("shop","wholesale"),("craft","sawmill"),("man_made","works")]),
}

# Lesbare Namen für die offiziellen Google-Typen (nur für die Fortschrittsanzeige)
TYPE_LABELS = {
  "restaurant":"Restaurants","cafe":"Cafés","bar":"Bars","bakery":"Bäckereien","meal_takeaway":"Imbiss/Takeaway",
  "supermarket":"Supermärkte","grocery_store":"Lebensmittel","clothing_store":"Mode","hardware_store":"Baumärkte",
  "electronics_store":"Elektro","furniture_store":"Möbel","shoe_store":"Schuhe","jewelry_store":"Schmuck","book_store":"Buchhandel","store":"Einzelhandel",
  "electrician":"Elektriker","plumber":"Sanitär/Heizung","painter":"Maler",
  "roofing_contractor":"Dachdecker/Bau","locksmith":"Schlosser","moving_company":"Umzug/Logistik",
  "doctor":"Ärzte","dentist":"Zahnärzte","pharmacy":"Apotheken","physiotherapist":"Physio","medical_lab":"Labore","veterinary_care":"Tierärzte",
  "car_dealer":"Autohäuser","car_repair":"KFZ-Werkstätten","car_wash":"Waschanlagen","gas_station":"Tankstellen","auto_parts_store":"Autoteile",
  "bank":"Banken","insurance_agency":"Versicherungen","accounting":"Steuer/Buchhaltung","atm":"Geldautomaten",
  "lawyer":"Kanzleien","real_estate_agency":"Immobilien","travel_agency":"Reisebüros","hair_care":"Friseure","beauty_salon":"Kosmetik","funeral_home":"Bestatter",
  "gym":"Fitnessstudios","sporting_goods_store":"Sportgeschäfte","bicycle_store":"Fahrradläden",
  "storage":"Lager","warehouse_store":"Großhandel",
}

# Keine Sponsoring-Zielgruppe
EXCLUDE = ["schützenverein","schuetzenverein","musikverein","gesangverein","sportverein","turnverein",
    "fußballverein","tennisverein","reitverein","angelverein","kleingartenverein","gartenverein",
    "heimatverein","förderverein","foerderverein","bürgerverein","kulturverein","karnevalsverein",
    "feuerwehr","rotes kreuz","drk ","johanniter","malteser","caritas","diakonie","kirchengemeinde",
    "pfarramt"," e.v."," e. v.","vereinsheim","tierheim","rathaus","stadtverwaltung","landkreis",
    "finanzamt","amtsgericht","grundschule","gymnasium","realschule","kindergarten","kita "]
def is_excluded(name):
    n = " " + name.lower() + " "
    return any(w in n for w in EXCLUDE)

# Bekannte Ketten/Konzerne → "Filiale einer Kette" (Entscheider sitzt meist nicht vor Ort)
KETTEN = ["rewe","edeka","aldi","lidl","penny","netto","kaufland","real ","dm ","dm-","rossmann","müller ",
    "sparkasse","volksbank","raiffeisenbank","commerzbank","deutsche bank","postbank","targobank","ing ",
    "mcdonald","burger king","subway","kfc","starbucks","nordsee","vapiano",
    "shell","aral","esso","total","jet ","star ","hem ",
    "obi","hornbach","bauhaus","toom","hagebau","globus",
    "mediamarkt","saturn","expert","euronics","c&a","h&m","zara","deichmann","tk maxx","kik","takko","ernsting",
    "fielmann","apollo","douglas","thalia","hugendubel","ikea","xxxlutz","poco","roller",
    "allianz","ergo","huk","axa","debeka","signal iduna","r+v","zurich","generali","devk","lvm","württembergische",
    "telekom","vodafone","o2","1&1","dhl","hermes","dpd","gls","ups",
    "fressnapf","futterhaus","dehner","blume 2000","mcpaper","woolworth","action","tedi","nkd",
    "fitx","mcfit","clever fit","fitness first","kieser","easyfitness","john reed",
    "backwerk","kamps","ditsch","le crobag","nordsee","block house","l'osteria","hans im glück","peter pane"]
def chain_match(name):
    n = " " + name.lower() + " "
    for k in KETTEN:
        if k in n: return k.strip()
    return ""

# ═══════════════════════════════════════════════════════════════════
# GEOCODING – exakte Adresse → Koordinaten
# ═══════════════════════════════════════════════════════════════════
def geocode(adresse, google_key):
    # 1) Google Geocoding (präzise bei Hausnummern)
    if google_key:
        try:
            r = requests.get("https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": adresse, "region": "de", "language": "de", "key": google_key}, timeout=15).json()
            if r.get("status") == "OK":
                res = r["results"][0]; loc = res["geometry"]["location"]
                return loc["lat"], loc["lng"], res["formatted_address"], "Google"
            if r.get("status") == "REQUEST_DENIED":
                _log(f"⚠ Google Geocoding abgelehnt: {r.get('error_message','')} → nutze OSM")
        except Exception as e:
            _log(f"⚠ Google Geocoding: {e} → nutze OSM")
    # 2) OSM Nominatim
    for _ in range(3):
        try:
            r = requests.get("https://nominatim.openstreetmap.org/search",
                params={"q": adresse if "deutschland" in adresse.lower() else adresse + ", Deutschland",
                        "format": "json", "limit": 1, "addressdetails": 1}, headers=HEADERS, timeout=15)
            if not r.text.strip().startswith("["): time.sleep(2); continue
            d = r.json()
            if not d: raise SystemExit(f"\n❌ Adresse '{adresse}' nicht gefunden. Bitte Straße, Hausnummer, PLZ und Ort angeben.")
            return float(d[0]["lat"]), float(d[0]["lon"]), d[0]["display_name"], "OSM"
        except SystemExit: raise
        except Exception: time.sleep(2)
    raise SystemExit("\n❌ Adress-Suche nicht erreichbar. Bitte in 1–2 Minuten erneut versuchen.")

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.asin(math.sqrt(a))

# ═══════════════════════════════════════════════════════════════════
# QUELLE A: GOOGLE PLACES (New) – Text Search mit Radius-Beschränkung
# ═══════════════════════════════════════════════════════════════════
PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ("places.id,places.displayName,places.formattedAddress,places.location,"
              "places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount,"
              "places.businessStatus,places.primaryTypeDisplayName,nextPageToken")

import math as _math

def _tile_centers(lat, lng, radius_m, tile_r):
    """Zerlegt den Suchkreis (radius_m) in ein Dreiecksraster aus Kreisen mit
    Radius tile_r, die den Kreis lückenlos überdecken. Liefert (lat, lng)-Zentren.
    Kachelabstand = tile_r * 1.5 (garantiert Überlappung, keine Lücken)."""
    if radius_m <= tile_r:
        return [(lat, lng)]
    step = tile_r * 1.5
    deg_lat = step / 111320.0
    deg_lng = step / (111320.0 * _math.cos(_math.radians(lat)) or 1e-9)
    centers, n = [], int(_math.ceil(radius_m / step)) + 1
    for iy in range(-n, n + 1):
        off = 0.5 * (iy % 2)  # versetzte Reihen → Dreiecksraster, dichteste Überdeckung
        for ix in range(-n, n + 1):
            cy = lat + iy * deg_lat
            cx = lng + (ix + off) * deg_lng
            # Nur Kacheln behalten, deren Zentrum im Suchkreis (+Kachelradius) liegt
            if haversine_km(lat, lng, cy, cx) * 1000 <= radius_m + tile_r:
                centers.append((cy, cx))
    return centers or [(lat, lng)]

def search_osm(lat, lng, radius_m, keys):
    """OpenStreetMap-Umkreissuche (Overpass), serverseitig. Liefert zusätzliche,
    v.a. lokale Betriebe, die Google teils nicht kennt. Nutzt die breiten OSM-Tags
    aus BRANCHEN (dritter Eintrag je Branche)."""
    pairs, tagmap = [], {}
    for k in keys:
        label, _, osm_tags = BRANCHEN[k]
        for (tk, tv) in osm_tags:
            if tv == "*": continue
            pairs.append((tk, tv)); tagmap[f"{tk}={tv}"] = label
    # nwr = node+way+relation in einem Durchlauf
    filt = "\n".join(f'  nwr["{tk}"="{tv}"](around:{radius_m},{lat},{lng});' for tk, tv in pairs)
    query = f"[out:json][timeout:120];\n(\n{filt}\n);\nout center tags;"

    data = None
    for ep in ["https://overpass-api.de/api/interpreter",
               "https://overpass.kumi.systems/api/interpreter",
               "https://overpass.openstreetmap.fr/api/interpreter"]:
        try:
            r = requests.post(ep, data={"data": query}, headers=HEADERS, timeout=130)
            if r.text.strip().startswith("{"):
                data = r.json(); break
            _log(f"⚠ {urlparse(ep).netloc} überlastet …"); time.sleep(1.5)
        except Exception as e:
            _log(f"⚠ {urlparse(ep).netloc}: {e}")
    if not data:
        raise SystemExit("Alle OSM-Server überlastet")

    seen, out = set(), []
    for el in data.get("elements", []):
        t = el.get("tags", {}); name = (t.get("name") or "").strip()
        if not name or is_excluded(name): continue
        street = t.get("addr:street", ""); nr = t.get("addr:housenumber", "")
        city = t.get("addr:city") or t.get("addr:town") or t.get("addr:village") or ""
        plz = t.get("addr:postcode", "")
        adresse = ", ".join(x for x in [f"{street} {nr}".strip(), f"{plz} {city}".strip()] if x)
        dk = name.lower() + "|" + adresse.lower()
        if dk in seen: continue
        seen.add(dk)
        branche = "Sonstige"
        for combo, lab in tagmap.items():
            tk, tv = combo.split("=")
            if t.get(tk) == tv: branche = lab; break
        center = el.get("center", {})
        out.append({
            "firma": name, "branche": branche, "typ": "", "adresse": adresse,
            "lat": el.get("lat", center.get("lat")), "lng": el.get("lon", center.get("lon")),
            "telefon": (t.get("contact:phone") or t.get("phone") or t.get("contact:mobile") or "").strip(),
            "website": (t.get("contact:website") or t.get("website") or "").replace("http://", "https://").strip(),
            "email": (t.get("contact:email") or t.get("email") or "").strip(),
            "rating": None, "reviews": None, "quelle": "OSM",
        })
    return out

def search_google(lat, lng, radius_m, keys, google_key):
    """Typbasierte Google-Umkreissuche mit ADAPTIVEM Kachel-Raster.

    Google liefert pro Abfrage max. 60 Treffer. Damit in dichten Gebieten nichts
    abgeschnitten wird, aber auf dem Land keine Aufrufe verschwendet werden:
    - Pro Typ zunächst EINE Abfrage über den ganzen Suchkreis.
    - Nur wenn diese ans 60er-Limit stößt (= es gibt mehr), wird dieser eine Typ
      in Kacheln zerlegt und nachgeladen. Dünne Typen kosten so nur 1 Aufruf.
    Duplikate werden über die Google-Place-ID entfernt.
    """
    seen, out = set(), []
    radius_m = min(radius_m, 50000)

    def fetch(cy, cx, rad, t, label):
        """Holt bis zu 60 Treffer für einen Typ in einem Kreis. Gibt die Anzahl
        der in DIESEM Kreis von Google gelieferten Treffer zurück (zur 60er-Erkennung)."""
        got, token = 0, None
        while True:
            body = {
                "textQuery": label, "includedType": t,
                "languageCode": "de", "regionCode": "DE", "pageSize": 20,
                "rankPreference": "DISTANCE",
                "locationBias": {"circle": {"center": {"latitude": cy, "longitude": cx}, "radius": float(rad)}},
            }
            if token: body["pageToken"] = token
            try:
                r = requests.post(PLACES_URL, json=body, timeout=20,
                    headers={"Content-Type": "application/json", "X-Goog-Api-Key": google_key, "X-Goog-FieldMask": FIELD_MASK})
                data = r.json()
            except Exception as e:
                _log(f"⚠ Google-Fehler ({label}/{t}): {e}"); return got
            if "error" in data:
                msg = data["error"].get("message", ""); status = str(data["error"].get("status", ""))
                if "API key" in msg or "PERMISSION_DENIED" in status:
                    raise SystemExit(f"\n❌ Google Places abgelehnt: {msg}\n   → Ist die 'Places API (New)' aktiviert und der Key freigeschaltet?")
                _log(f"⚠ Google ({label}/{t}): {msg}"); return got
            for p in data.get("places", []):
                got += 1
                pid = p.get("id")
                if not pid or pid in seen: continue
                if p.get("businessStatus") not in (None, "OPERATIONAL"): continue
                name = (p.get("displayName") or {}).get("text", "").strip()
                if not name or is_excluded(name): continue
                seen.add(pid)
                loc = p.get("location") or {}
                out.append({
                    "firma": name, "branche": label,
                    "typ": (p.get("primaryTypeDisplayName") or {}).get("text", ""),
                    "adresse": p.get("formattedAddress", ""),
                    "lat": loc.get("latitude"), "lng": loc.get("longitude"),
                    "telefon": p.get("nationalPhoneNumber", "") or "",
                    "website": (p.get("websiteUri") or "").replace("http://", "https://"),
                    "email": "", "rating": p.get("rating"), "reviews": p.get("userRatingCount"),
                    "quelle": "Google",
                })
            token = data.get("nextPageToken")
            if not token: break
            time.sleep(1.2)
        return got

    type_to_label, order = {}, []
    for k in keys:
        label, gtypes, _ = BRANCHEN[k]
        for t in gtypes:
            if t not in type_to_label:
                type_to_label[t] = label; order.append(t)

    tile_r = 2500 if radius_m <= 15000 else 4000  # Kachelgröße nur für den Nachlade-Fall
    total, done = len(order), 0
    for t in order:
        label = type_to_label[t]
        done += 1
        _prog(done, total, f"Google · {label} · {TYPE_LABELS.get(t, t)}")
        got = fetch(lat, lng, radius_m, t, label)
        # 60 = Google-Maximum ausgeschöpft → es gibt mehr → diesen Typ nachkacheln
        if got >= 60 and radius_m > tile_r:
            for (cy, cx) in _tile_centers(lat, lng, radius_m, tile_r):
                _prog(done, total, f"Google · {label} · {TYPE_LABELS.get(t, t)} (fein)")
                fetch(cy, cx, tile_r, t, label)
        time.sleep(0.12)
    return out

def norm(url):
    if not url: return None
    if not url.startswith("http"): url = "https://" + url
    try: p = urlparse(url); return f"{p.scheme}://{p.netloc}"
    except Exception: return None

def find_email(text):
    text = text.replace("(at)", "@").replace("[at]", "@").replace(" at ", "@").replace("(dot)", ".").replace("[dot]", ".")
    for m in re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text):
        low = m.lower()
        if any(x in low for x in ("noreply", "no-reply", "example", "mailer", "sentry", "wixpress", "@2x", ".png", ".jpg", "webmaster@")): continue
        return m
    return ""

def find_phone(text):
    m = re.search(r"(?:\+49[\s\-/]?|0)[\s\-/]?\(?\d{2,5}\)?[\s\-/]?\d{3,}[\s\-/]?\d*", text)
    return re.sub(r"\s{2,}", " ", m.group()).strip() if m else ""

def find_name(text):
    m = re.search(r"(?:Inhaber(?:in)?|Geschäftsführer(?:in|ung)?|Vertreten durch|Vertretungsberechtigt(?:er)?|Verantwortlich(?:er)?)[:\s]+"
                  r"(?:Herr |Frau |Dipl\.-\w+\.? |Dr\. )?([A-ZÄÖÜ][a-zäöüß\-]+(?:\s[A-ZÄÖÜ][a-zäöüß\-]+){1,2})", text)
    return m.group(1).strip() if m else ""

def find_rechtsform(text):
    for rf, pat in [("AG", r"\bAG\b"), ("SE", r"\bSE\b"), ("KGaA", r"\bKGaA\b"),
                    ("GmbH & Co. KG", r"GmbH\s*&\s*Co\.?\s*KG"), ("GmbH", r"\bGmbH\b"), ("UG", r"\bUG\b|haftungsbeschränkt"),
                    ("OHG", r"\bOHG\b"), ("KG", r"\bKG\b"), ("e.K.", r"\be\.\s?K\.|eingetragener Kaufmann"), ("GbR", r"\bGbR\b"),
                    ("Einzelunternehmen", r"Einzelunternehm")]:
        if re.search(pat, text): return rf
    return ""

def find_hrb(text):
    m = re.search(r"\bHR[AB]\s?\d{3,7}\b", text)
    return m.group() if m else ""

def find_mitarbeiter(text):
    # "über 50 Mitarbeiter", "120 Mitarbeitende", "Team von 12 Mitarbeitern", "15 Beschäftigte"
    m = re.search(r"(?:über|ca\.|rund|etwa|mehr als|insgesamt)?\s*(\d{1,5})\s*(?:Mitarbeiter(?:innen|:innen|\*innen|n)?|Mitarbeitende|Beschäftigte|Angestellte|Kollegen)", text, re.I)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 50000: return n
    return None

def find_gruendung(text):
    m = re.search(r"(?:gegründet|seit|Gründung(?:sjahr)?|besteht seit|Tradition seit)[^\d]{0,15}((?:18|19|20)\d{2})", text, re.I)
    return int(m.group(1)) if m else None

def fetch_text(url):
    r = requests.get(url, headers=HEADERS, timeout=8)
    if r.status_code != 200 or len(r.text) < 200: return ""
    soup = BeautifulSoup(r.text, "html.parser")
    for s in soup(["script", "style", "noscript"]): s.decompose()
    return soup.get_text(" ")

def find_beschreibung(soup):
    """Kurzbeschreibung: Meta-Description > og:description > erster aussagekräftiger Absatz."""
    def clean(t): return re.sub(r"\s+", " ", t or "").strip()
    for attrs in ({"name": re.compile("^description$", re.I)}, {"property": "og:description"}, {"name": "twitter:description"}):
        m = soup.find("meta", attrs=attrs)
        if m and len(clean(m.get("content"))) >= 25:
            return clean(m.get("content"))[:300]
    for p in soup.find_all("p"):
        t = clean(p.get_text(" "))
        if len(t) >= 80 and "cookie" not in t.lower() and "datenschutz" not in t.lower():
            return (t[:297] + "…") if len(t) > 300 else t
    return ""

def scrape_site(website):
    """Impressum + Startseite durchsuchen. Liefert Kontakte und Firmeninfos."""
    base = norm(website)
    res = {"email": "", "telefon": "", "ansprechpartner": "", "rechtsform": "", "hrb": "", "mitarbeiter": None, "gruendung": None, "beschreibung": ""}
    if not base: return res
    texts = []
    # Impressum-Pfade
    for path in IMPRESSUM_PATHS:
        try:
            t = fetch_text(base + path)
            if t: texts.append(t)
            if t and find_email(t): break
        except Exception: continue
    # Startseite (für Mitarbeiter/Gründung/Impressum-Link)
    try:
        r = requests.get(base, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")
        res["beschreibung"] = find_beschreibung(soup)
        for s in soup(["script", "style", "noscript"]): s.decompose()
        home = soup.get_text(" "); texts.append(home)
        if not any(find_email(t) for t in texts):
            for a in soup.find_all("a", href=True):
                if "impressum" in (a.get_text() + a["href"]).lower():
                    href = a["href"]; full = href if href.startswith("http") else base + ("/" if not href.startswith("/") else "") + href
                    try:
                        t = fetch_text(full)
                        if t: texts.append(t)
                    except Exception: pass
                    break
    except Exception: pass
    alltext = " ".join(texts)
    if not alltext: return res
    res["email"] = find_email(alltext)
    res["telefon"] = find_phone(alltext)
    res["ansprechpartner"] = find_name(alltext)
    res["rechtsform"] = find_rechtsform(alltext)
    res["hrb"] = find_hrb(alltext)
    res["mitarbeiter"] = find_mitarbeiter(alltext)
    res["gruendung"] = find_gruendung(alltext)
    return res

# ═══════════════════════════════════════════════════════════════════
# UNTERNEHMENSGRÖSSE – EU-KMU-Definition + Signale
# Kleinst <10 · Klein <50 · Mittel <250 · Groß ≥250 Mitarbeiter
# ═══════════════════════════════════════════════════════════════════
def classify_size(k):
    name = k["firma"]
    kette = chain_match(name)
    if kette:
        return "Filiale einer Kette", f"Kette erkannt ({kette})"
    ma = k.get("mitarbeiter")
    if ma is not None:
        if ma < 10:   return "Kleinstunternehmen", f"{ma} Mitarbeiter lt. Website"
        if ma < 50:   return "Kleinunternehmen", f"{ma} Mitarbeiter lt. Website"
        if ma < 250:  return "Mittelstand", f"{ma} Mitarbeiter lt. Website"
        return "Großunternehmen", f"{ma} Mitarbeiter lt. Website"
    rf = k.get("rechtsform", "")
    reviews = k.get("reviews") or 0
    if rf in ("AG", "SE", "KGaA"):
        return "Großunternehmen", f"Rechtsform {rf}"
    if rf == "GmbH & Co. KG":
        return "Mittelstand", f"Rechtsform {rf}" + (" · viele Bewertungen" if reviews >= 200 else "")
    if rf in ("GmbH", "UG", "OHG", "KG"):
        if reviews >= 500: return "Mittelstand", f"Rechtsform {rf} · {reviews} Bewertungen"
        return "Kleinunternehmen", f"Rechtsform {rf}"
    if rf in ("e.K.", "GbR", "Einzelunternehmen"):
        return "Kleinstunternehmen", f"Rechtsform {rf}"
    # Ohne Rechtsform: Bewertungszahl als grobes Signal
    if reviews >= 800: return "Mittelstand", f"{reviews} Bewertungen (Schätzung)"
    if reviews >= 150: return "Kleinunternehmen", f"{reviews} Bewertungen (Schätzung)"
    if k.get("website"): return "Kleinunternehmen", "Schätzung (Website vorhanden)"
    return "Kleinstunternehmen", "Schätzung (keine weiteren Signale)"

SIZE_ORDER = {"Großunternehmen": 4, "Mittelstand": 3, "Kleinunternehmen": 2, "Kleinstunternehmen": 1, "Filiale einer Kette": 0}

# ═══════════════════════════════════════════════════════════════════
# SCORE 0–100 (Kontaktierbarkeit + Relevanz)
# ═══════════════════════════════════════════════════════════════════
def score(k):
    s = 0
    if k.get("website"): s += 10
    if k.get("email"): s += 30
    if k.get("telefon"): s += 15
    if k.get("ansprechpartner"): s += 15
    if (k.get("rating") or 0) >= 4.0: s += 10
    if (k.get("reviews") or 0) >= 20: s += 10
    if k.get("groesse") in ("Kleinunternehmen", "Mittelstand"): s += 10   # Sweet Spot fürs regionale Sponsoring
    if k.get("groesse") == "Filiale einer Kette": s -= 15                  # Entscheider i.d.R. nicht vor Ort
    return max(0, min(s, 100))

# ═══════════════════════════════════════════════════════════════════
# EXCEL
# ═══════════════════════════════════════════════════════════════════
def write_excel(rows, verein, adresse, radius, quelle_label):
    wb = Workbook()
    G, Y = "003D30", "D6FF29"
    GR, YE, RE, GY = "C6EFCE", "FFEB9C", "FFC7CE", "EDEDED"
    thin = Side(style="thin", color="D9D9D9")

    # ── Blatt 1: Leads ──
    ws = wb.active; ws.title = "Leads"
    ws.merge_cells("A1:S1")
    tc = ws.cell(1, 1, f"Sponsoren-Recherche · {verein} · Umkreis {radius} km um {adresse} · {len(rows)} Unternehmen · Quelle: {quelle_label}")
    tc.fill = PatternFill("solid", fgColor=G); tc.font = Font(bold=True, color=Y, size=12)
    tc.alignment = Alignment(vertical="center"); ws.row_dimensions[1].height = 26

    cols = ["Firma", "Branche", "Typ", "Größe", "Größe – Basis", "Entf. km", "Adresse", "Telefon", "E-Mail",
            "Website", "Ansprechpartner", "Rechtsform", "Handelsregister", "Mitarbeiter", "Gegründet",
            "Score", "Status", "Google-Bewertung", "Quelle"]
    for ci, c in enumerate(cols, 1):
        cell = ws.cell(2, ci, c); cell.fill = PatternFill("solid", fgColor=G)
        cell.font = Font(bold=True, color=Y, size=10); cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[2].height = 28

    for ri, k in enumerate(rows, 3):
        sc = k["score"]
        if k["groesse"] == "Filiale einer Kette": color = GY
        elif sc >= 70 and k["email"]: color = GR
        elif sc >= 45: color = YE
        else: color = RE
        status = "E-Mail vorhanden" if k["email"] else ("Anruf nötig" if k["telefon"] else "kein Kontakt")
        rating = f'{k["rating"]}★ ({k["reviews"]})' if k.get("rating") else ""
        vals = [k["firma"], k["branche"], k.get("typ", ""), k["groesse"], k["groesse_basis"],
                round(k["dist_km"], 1) if k.get("dist_km") is not None else "",
                k["adresse"], k["telefon"], k["email"], k["website"], k["ansprechpartner"],
                k.get("rechtsform", ""), k.get("hrb", ""), k.get("mitarbeiter") or "", k.get("gruendung") or "",
                sc, status, rating, k["quelle"]]
        for ci, v in enumerate(vals, 1):
            cell = ws.cell(ri, ci, v); cell.fill = PatternFill("solid", fgColor=color)
            cell.font = Font(size=9); cell.alignment = Alignment(vertical="center")
            cell.border = Border(bottom=thin, right=thin)
    for ci, w in enumerate([32, 18, 18, 18, 26, 8, 36, 16, 30, 28, 20, 14, 14, 10, 9, 7, 15, 14, 8], 1):
        ws.column_dimensions[get_column_letter(ci)].width = w
    ws.auto_filter.ref = f"A2:{get_column_letter(len(cols))}2"
    ws.freeze_panes = "B3"

    # ── Blatt 2: Übersicht ──
    ov = wb.create_sheet("Übersicht")
    ov["A1"] = "Zusammenfassung"; ov["A1"].font = Font(bold=True, size=13, color=G)
    r = 3
    def hdr(txt):
        nonlocal r
        c = ov.cell(r, 1, txt); c.font = Font(bold=True, color=Y); c.fill = PatternFill("solid", fgColor=G)
        for ci in (2, 3, 4):
            ov.cell(r, ci).fill = PatternFill("solid", fgColor=G)
        ov.cell(r, 2, "Anzahl").font = Font(bold=True, color=Y); ov.cell(r, 3, "mit E-Mail").font = Font(bold=True, color=Y); ov.cell(r, 4, "Anruf nötig").font = Font(bold=True, color=Y)
        r += 1
    def line(label, subset):
        nonlocal r
        ov.cell(r, 1, label); ov.cell(r, 2, len(subset))
        ov.cell(r, 3, sum(1 for x in subset if x["email"])); ov.cell(r, 4, sum(1 for x in subset if x["telefon"] and not x["email"]))
        r += 1
    hdr("Nach Branche")
    for b in sorted({x["branche"] for x in rows}): line(b, [x for x in rows if x["branche"] == b])
    r += 1; hdr("Nach Unternehmensgröße")
    for g in sorted({x["groesse"] for x in rows}, key=lambda g: -SIZE_ORDER.get(g, 0)): line(g, [x for x in rows if x["groesse"] == g])
    r += 1; hdr("Gesamt")
    line("Alle Unternehmen", rows)
    r += 2
    ov.cell(r, 1, "Größenklassen nach EU-KMU-Definition: Kleinst <10 · Klein <50 · Mittel <250 · Groß ≥250 Mitarbeiter.").font = Font(italic=True, size=9, color="666666")
    ov.cell(r+1, 1, "Basis der Einstufung steht pro Firma in Spalte 'Größe – Basis' (Website-Angabe > Rechtsform > Ketten-Erkennung > Schätzung).").font = Font(italic=True, size=9, color="666666")
    for ci, w in enumerate([34, 10, 12, 12], 1): ov.column_dimensions[get_column_letter(ci)].width = w

    safe = re.sub(r"[^\w\s-]", "", verein).strip().replace(" ", "_") or "Verein"
    fname = f"Sponsoren_{safe}_{radius}km_{time.strftime('%Y-%m-%d')}.xlsx"
    wb.save(fname)
    return fname

# ═══════════════════════════════════════════════════════════════════
# HAUPTABLAUF
# ═══════════════════════════════════════════════════════════════════
def run(verein, adresse, radius_km, keys, google_key, scrape=True, max_scrape=None, write=True,
        max_n=None, size_filter=None, workers=8):
    """Recherche ausführen. Rückgabe: (excel_dateiname | None, liste_unternehmen)
    max_n:        maximale Anzahl Ergebnisse (nächstgelegene passende zuerst)
    size_filter:  Menge erlaubter Größenklassen (None = alle)
    workers:      parallele Website-Analysen
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    _log(f"📍 Adresse: {adresse}")
    lat, lng, disp, geo_src = geocode(adresse, google_key)
    _log(f"→ {disp[:75]}  ({geo_src})")

    def _dedupe_key(k):
        # Firma + Straße (ohne Hausnummer-Feinheiten) als Dublettenschlüssel
        import re as _re
        name = _re.sub(r"[^a-z0-9]", "", (k.get("firma") or "").lower())
        adr  = (k.get("adresse") or "").lower()
        m = _re.search(r"[a-zäöüß ]+\s*\d+", adr)
        street = _re.sub(r"[^a-z0-9]", "", m.group(0)) if m else _re.sub(r"[^a-z0-9]", "", adr)[:18]
        return name + "|" + street

    if google_key:
        _log(f"🔍 Google Places – {radius_km} km Umkreis, {len(keys)} Branchen …")
        kands = search_google(lat, lng, radius_km * 1000, keys, google_key)
        # Zusätzlich OpenStreetMap, zusammengeführt & entdoppelt (mehr Quantität, v.a. ländlich)
        try:
            _log(f"🔍 OpenStreetMap ergänzend …")
            osm = search_osm(lat, lng, radius_km * 1000, keys)
        except SystemExit as e:
            _log(f"⚠ OSM übersprungen ({str(e).strip()[:60]}) – nur Google")
            osm = []
        except Exception as e:
            _log(f"⚠ OSM-Fehler ({e}) – nur Google")
            osm = []
        index = {_dedupe_key(k): k for k in kands}
        added, enriched = 0, 0
        for o in osm:
            key = _dedupe_key(o)
            if key in index:
                # Bekannt – nur Lücken aus OSM füllen (Telefon/Website/E-Mail), Google-Daten bleiben führend
                g = index[key]
                for f in ("telefon", "website", "email"):
                    if not g.get(f) and o.get(f):
                        g[f] = o[f]; enriched += 1
            else:
                index[key] = o; kands.append(o); added += 1
        _log(f"✓ OSM: {added} zusätzliche Unternehmen, {enriched} Google-Einträge ergänzt")
        quelle = "Google + OpenStreetMap"
    else:
        _log(f"🔍 OpenStreetMap – {radius_km} km Umkreis, {len(keys)} Branchen …")
        kands = search_osm(lat, lng, radius_km * 1000, keys)
        quelle = "OpenStreetMap"

    for k in kands:
        k["dist_km"] = haversine_km(lat, lng, k["lat"], k["lng"]) if k.get("lat") and k.get("lng") else None
    kands = [k for k in kands if k["dist_km"] is None or k["dist_km"] <= radius_km + 0.5]
    kands.sort(key=lambda x: x["dist_km"] if x["dist_km"] is not None else 999)
    _log(f"✓ {len(kands)} Unternehmen im Umkreis")

    for k in kands:
        for f in ("ansprechpartner", "rechtsform", "hrb", "beschreibung"): k.setdefault(f, "")
        for f in ("mitarbeiter", "gruendung"): k.setdefault(f, None)

    size_filter = set(size_filter) if size_filter else None
    if size_filter and "Filiale einer Kette" not in size_filter:
        n0 = len(kands)
        kands = [k for k in kands if not chain_match(k["firma"])]
        if n0 - len(kands): _log(f"⊘ {n0 - len(kands)} Ketten-Filialen übersprungen")

    def finalize(k):
        if not k["rechtsform"]:
            k["rechtsform"] = find_rechtsform(" " + k["firma"] + " ")
        k["groesse"], k["groesse_basis"] = classify_size(k)
        k["score"] = score(k)
        return size_filter is None or k["groesse"] in size_filter

    total, done, found, kept = len(kands), 0, 0, []
    if scrape and total:
        _log("🌐 Analysiere Websites parallel (Impressum, Beschreibung, Firmendaten) …")
    batch = max(workers * 3, 12)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for start in range(0, total, batch):
            chunk = kands[start:start + batch]
            futs = {}
            for k in chunk:
                if scrape and k["website"]:
                    futs[ex.submit(scrape_site, k["website"])] = k
                else:
                    done += 1
            if not futs:
                _prog(done, total, chunk[-1]["firma"])
            for f in as_completed(futs):
                k = futs[f]
                try:
                    info = f.result()
                except Exception:
                    info = {}
                if info.get("email") and not k["email"]:
                    k["email"] = info["email"]; found += 1
                if info.get("telefon") and not k["telefon"]:
                    k["telefon"] = info["telefon"]
                for fld in ("ansprechpartner", "rechtsform", "hrb", "mitarbeiter", "gruendung", "beschreibung"):
                    if info.get(fld) not in (None, ""):
                        k[fld] = info[fld]
                done += 1
                _prog(done, total, k["firma"])
            for k in chunk:
                if finalize(k):
                    kept.append(k)
                if max_n and len(kept) >= max_n:
                    break
            if max_n and len(kept) >= max_n:
                _log(f"✓ Maximalzahl von {max_n} Unternehmen erreicht")
                break
    if scrape:
        _log(f"✓ {found} E-Mail-Adressen aus Websites ergänzt")

    kept.sort(key=lambda x: (-x["score"], x["dist_km"] if x["dist_km"] is not None else 999))
    fname = write_excel(kept, verein, adresse, radius_km, quelle) if write else None
    mit_mail = sum(1 for k in kept if k["email"])
    anruf = sum(1 for k in kept if k["telefon"] and not k["email"])
    _log(f"✓ Fertig: {len(kept)} Unternehmen · {mit_mail} mit E-Mail · {anruf} Anruf nötig"
         + (f"  →  {fname}" if fname else ""))
    return fname, kept

def interactive():
    print("\n" + "=" * 64 + "\n  RFN Sponsoren-Recherche PRO\n" + "=" * 64)
    verein = input("\n  Vereinsname (für den Dateinamen): ").strip() or "Verein"
    adresse = ""
    while not adresse:
        adresse = input("  Start-Adresse (Straße Nr, PLZ Ort), z.B. 'Parkstraße 7, 31812 Bad Pyrmont': ").strip()
    radius = 15
    r_in = input("  Radius in km [15]: ").strip()
    if r_in:
        try: radius = max(1, min(50, int(r_in)))
        except ValueError: print("  → nutze 15 km")
    print("\n  Branchen (Nummern mit Komma, 0 = alle):")
    klist = list(BRANCHEN.keys())
    for i, k in enumerate(klist, 1): print(f"    {i}) {BRANCHEN[k][0]}")
    b_in = input("  Auswahl [alle]: ").strip()
    if not b_in or b_in == "0": keys = klist
    else:
        keys = [klist[int(x) - 1] for x in b_in.split(",") if x.strip().isdigit() and 1 <= int(x) <= len(klist)] or klist
    key = os.environ.get("GOOGLE_API_KEY", "").strip() or input("  Google-API-Key (Enter = ohne, dann OpenStreetMap): ").strip()
    print(f"\n  → {adresse} · {radius} km · {len(keys)} Branchen · {'Google Places' if key else 'OpenStreetMap'}")
    input("  Enter zum Start …")
    print()
    run(verein, adresse, radius, keys, key)
    print()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="RFN Sponsoren-Recherche PRO")
    ap.add_argument("--verein"); ap.add_argument("--adresse"); ap.add_argument("--radius", type=int, default=15)
    ap.add_argument("--branchen", help="kommagetrennt, z.B. gastronomie,handel (Standard: alle)")
    ap.add_argument("--key", help="Google API Key (oder Umgebungsvariable GOOGLE_API_KEY)")
    ap.add_argument("--no-scrape", action="store_true", help="Impressum-Scraping überspringen (schneller Test)")
    a = ap.parse_args()
    try:
        if a.adresse:
            keys = [k for k in (a.branchen or "").split(",") if k in BRANCHEN] or list(BRANCHEN.keys())
            run(a.verein or "Verein", a.adresse, a.radius, keys, a.key or os.environ.get("GOOGLE_API_KEY", ""), scrape=not a.no_scrape)
        else:
            interactive()
    except KeyboardInterrupt:
        print("\n\n  Abgebrochen.\n")
