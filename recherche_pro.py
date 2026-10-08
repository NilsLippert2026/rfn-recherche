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
    """Adresse → Koordinaten. Vier unabhängige Wege, der erste Erfolg gewinnt:
    1) Google Geocoding API  2) Google Places Text Search (gleicher Key, andere API)
    3) OSM Nominatim  4) Photon (komoot). Schlägt alles fehl, werden die echten Gründe genannt."""
    q = (adresse or "").replace("·", ",").strip()
    reasons = []
    if google_key:
        for attempt in range(3):
            try:
                r = requests.get("https://maps.googleapis.com/maps/api/geocode/json",
                                 params={"address": q, "region": "de", "language": "de", "key": google_key}, timeout=15).json()
                st_ = r.get("status")
                if st_ == "OK":
                    res = r["results"][0]; loc = res["geometry"]["location"]
                    return loc["lat"], loc["lng"], res["formatted_address"], "Google"
                reasons.append(f"Google Geocoding: {st_} {r.get('error_message', '')}".strip())
                if st_ == "REQUEST_DENIED":
                    _log(f"⚠ Google Geocoding abgelehnt: {r.get('error_message', '')}")
                if st_ in ("OVER_QUERY_LIMIT", "UNKNOWN_ERROR"):
                    time.sleep(2 + attempt * 3); continue
                break
            except Exception as e:
                reasons.append(f"Google Geocoding: {type(e).__name__}"); time.sleep(2)
        try:
            r = requests.post(PLACES_URL, json={"textQuery": q, "languageCode": "de", "regionCode": "DE", "pageSize": 1},
                              headers={"Content-Type": "application/json", "X-Goog-Api-Key": google_key,
                                       "X-Goog-FieldMask": "places.location,places.formattedAddress"}, timeout=20).json()
            p = (r.get("places") or [None])[0]
            if p and p.get("location"):
                return p["location"]["latitude"], p["location"]["longitude"], p.get("formattedAddress", q), "Google Places"
            reasons.append("Google Places: " + (google_error_text(r["error"])[:200] if r.get("error") else "keine Treffer"))
        except Exception as e:
            reasons.append(f"Google Places: {type(e).__name__}")
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q": q if "deutschland" in q.lower() else q + ", Deutschland", "format": "json", "limit": 1},
                         headers=HEADERS, timeout=15)
        if r.text.strip().startswith("["):
            d = r.json()
            if d:
                return float(d[0]["lat"]), float(d[0]["lon"]), d[0]["display_name"], "OSM"
            reasons.append("Nominatim: Adresse unbekannt")
        else:
            reasons.append(f"Nominatim: HTTP {r.status_code}")
    except Exception as e:
        reasons.append(f"Nominatim: {type(e).__name__}")
    try:
        r = requests.get("https://photon.komoot.io/api/", params={"q": q, "limit": 1, "lang": "de"}, headers=HEADERS, timeout=15).json()
        f = (r.get("features") or [None])[0]
        if f:
            lon, lat = f["geometry"]["coordinates"][:2]
            pr = f.get("properties", {})
            name = ", ".join(str(x) for x in [pr.get("street"), pr.get("housenumber"), pr.get("postcode"), pr.get("city")] if x)
            return float(lat), float(lon), name or q, "Photon"
        reasons.append("Photon: Adresse unbekannt")
    except Exception as e:
        reasons.append(f"Photon: {type(e).__name__}")
    raise SystemExit("Adresse konnte nicht in Koordinaten umgewandelt werden – " + " | ".join(reasons))

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.asin(math.sqrt(a))

# ═══════════════════════════════════════════════════════════════════
# QUELLE A: GOOGLE PLACES (New) – Text Search mit Radius-Beschränkung
# ═══════════════════════════════════════════════════════════════════
VERSION = "v12 · 08.10. · Google-Sperre → OSM"

# Freitext-Suchbegriffe je Branche (wie ein Mensch bei Google Maps sucht).
# Erfasst auch Betriebe, die bei Google unter keinem passenden Typ eingetragen sind.
GOOGLE_QUERIES = {
  "gastronomie": ["Restaurant", "Café", "Gaststätte", "Bäckerei", "Konditorei", "Imbiss", "Pizzeria", "Hotel", "Bar", "Eiscafé"],
  "handel": ["Einzelhandel", "Supermarkt", "Modegeschäft", "Schuhgeschäft", "Baumarkt", "Elektrofachgeschäft", "Möbelhaus",
             "Optiker", "Blumenladen", "Metzgerei", "Juwelier", "Buchhandlung", "Getränkemarkt", "Drogerie", "Raumausstatter"],
  "handwerk": ["Elektriker", "Sanitär Heizung", "Tischlerei", "Malerbetrieb", "Dachdecker", "Schlosserei", "Metallbau",
               "Bauunternehmen", "Zimmerei", "Fliesenleger", "Garten- und Landschaftsbau", "Glaserei", "Fensterbau",
               "Klimatechnik", "Schornsteinfeger", "Bodenleger", "Steinmetz"],
  "gesundheit": ["Arztpraxis", "Zahnarzt", "Apotheke", "Physiotherapie", "Pflegedienst", "Sanitätshaus", "Hörakustiker",
                 "Tierarzt", "Heilpraktiker", "Ergotherapie", "Logopädie", "Kieferorthopäde"],
  "automobil": ["Autohaus", "KFZ-Werkstatt", "Autoteile", "Reifenservice", "Tankstelle", "Autowaschanlage",
                "Abschleppdienst", "Motorradhändler", "Autovermietung", "Autolackiererei"],
  "finanzen": ["Bank", "Sparkasse", "Volksbank", "Versicherungsagentur", "Versicherungsmakler", "Steuerberater",
               "Finanzberatung", "Rechtsanwalt", "Notar", "Wirtschaftsprüfer"],
  "dienstleistung": ["Immobilienmakler", "Architekt", "Werbeagentur", "IT-Dienstleister", "Friseur", "Kosmetikstudio",
                     "Reisebüro", "Gebäudereinigung", "Fahrschule", "Bestatter", "Fotograf", "Druckerei",
                     "Ingenieurbüro", "Hausverwaltung"],
  "fitness": ["Fitnessstudio", "Sportgeschäft", "Fahrradladen", "Tanzschule", "Yogastudio", "Kampfsportschule", "Reitstall"],
  "industrie": ["Spedition", "Logistik", "Maschinenbau", "Großhandel", "Industriebetrieb", "Entsorgung",
                "Containerdienst", "Elektrotechnik", "Kunststofftechnik", "Holzverarbeitung"],
}

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

class GoogleDenied(Exception):
    """Google verweigert den Zugriff (Schlüssel, Abrechnung, Freischaltung)."""

GOOGLE_REASONS = {
    "BILLING_DISABLED": "Abrechnung im Google-Projekt deaktiviert oder pausiert (Abrechnung → Übersicht / Budgets prüfen)",
    "API_KEY_SERVICE_BLOCKED": "Der Schlüssel darf diese Schnittstelle nicht nutzen (Anmeldedaten → Schlüssel → API-Einschränkungen)",
    "SERVICE_DISABLED": "Places API (New) ist im Projekt nicht aktiviert (APIs & Dienste → Aktivierte APIs)",
    "API_KEY_INVALID": "Der Schlüssel ist ungültig oder gelöscht (Anmeldedaten prüfen, Key in den Streamlit-Secrets erneuern)",
    "CONSUMER_SUSPENDED": "Das Google-Projekt wurde von Google gesperrt (E-Mail von Google prüfen)",
    "API_KEY_HTTP_REFERRER_BLOCKED": "Schlüssel ist auf Websites eingeschränkt – für Server-Nutzung 'Keine' bzw. nur API-Einschränkung wählen",
    "API_KEY_IP_ADDRESS_BLOCKED": "Schlüssel ist auf IP-Adressen eingeschränkt – Streamlit hat wechselnde Adressen",
    "RATE_LIMIT_EXCEEDED": "Abfragelimit pro Minute überschritten",
    "RESOURCE_EXHAUSTED": "Tages- oder Monatskontingent erschöpft (APIs & Dienste → Places API (New) → Kontingente)",
}

def google_error_text(err):
    """Google-Fehler in verständlichen Text mit Grund-Code übersetzen."""
    msg = err.get("message", "")
    reason = ""
    for d in err.get("details", []) or []:
        if isinstance(d, dict) and d.get("reason"):
            reason = d["reason"]; break
    status = str(err.get("status", ""))
    expl = GOOGLE_REASONS.get(reason) or GOOGLE_REASONS.get(status, "")
    return f"{msg} [{reason or status}]" + (f" → {expl}" if expl else "")

# Weltweite öffentliche Overpass-Server (Stand OSM-Wiki 2026). Reihenfolge = Priorität.
# overpass-api.de vergibt nur 2 Abfrageplätze je IP – auf geteilten Cloud-Servern oft belegt,
# daher zuerst die großen Alternativ-Instanzen.
OVERPASS_SERVERS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]
LAST_STATS = {}

def _overpass(query):
    """Fragt die Server nacheinander ab (je 2 Versuche). Gibt (daten, server) oder (None, fehler)."""
    last = ""
    for ep in OVERPASS_SERVERS:
        host = urlparse(ep).netloc
        for attempt in range(2):
            try:
                r = requests.post(ep, data={"data": query}, headers=HEADERS, timeout=150)
                txt = r.text.strip()
                if r.status_code == 200 and txt.startswith("{"):
                    d = r.json()
                    remark = str(d.get("remark", ""))
                    if "runtime error" in remark.lower() or "timed out" in remark.lower():
                        last = f"{host}: {remark[:80]}"
                    else:
                        return d, host
                else:
                    last = f"{host}: HTTP {r.status_code}"
            except Exception as e:
                last = f"{host}: {type(e).__name__}"
            time.sleep(3 + attempt * 4)
    return None, last

def search_osm(lat, lng, radius_m, keys):
    """OpenStreetMap-Umkreissuche, pro Branche aufgeteilt (kleinere, robustere Abfragen).
    Fällt eine Branche aus, laufen die übrigen weiter."""
    seen, out, ok, failed = set(), [], 0, []
    for k in keys:
        label, _, osm_tags = BRANCHEN[k]
        pairs = [(tk, tv) for tk, tv in osm_tags if tv != "*"]
        if not pairs:
            continue
        filt = "\n".join(f'  nwr["{tk}"="{tv}"](around:{radius_m},{lat},{lng});' for tk, tv in pairs)
        query = f"[out:json][timeout:120];\n(\n{filt}\n);\nout center tags;"
        _prog(len(failed) + ok + 1, len(keys), f"OpenStreetMap · {label}")
        data, info = _overpass(query)
        if data is None:
            failed.append(label); _log(f"⚠ OSM {label}: nicht erreichbar ({info})")
            continue
        ok += 1
        n0 = len(out)
        for el in data.get("elements", []):
            t = el.get("tags", {}); name = (t.get("name") or "").strip()
            if not name or is_excluded(name):
                continue
            street = t.get("addr:street", ""); nr = t.get("addr:housenumber", "")
            city = t.get("addr:city") or t.get("addr:town") or t.get("addr:village") or ""
            plz = t.get("addr:postcode", "")
            adresse = ", ".join(x for x in [f"{street} {nr}".strip(), f"{plz} {city}".strip()] if x)
            center = el.get("center", {})
            elat = el.get("lat", center.get("lat")); elng = el.get("lon", center.get("lon"))
            dk = name.lower() + "|" + (adresse.lower() or f"{round(elat or 0, 4)},{round(elng or 0, 4)}")
            if dk in seen:
                continue
            seen.add(dk)
            out.append({
                "firma": name, "branche": label, "typ": "", "adresse": adresse, "lat": elat, "lng": elng,
                "telefon": (t.get("contact:phone") or t.get("phone") or t.get("contact:mobile") or "").strip(),
                "website": (t.get("contact:website") or t.get("website") or "").replace("http://", "https://").strip(),
                "email": (t.get("contact:email") or t.get("email") or "").strip(),
                "rating": None, "reviews": None, "quelle": "OSM",
            })
        _log(f"✓ OSM {label}: {len(out) - n0} Einträge ({info})")
    if ok == 0:
        raise SystemExit("OSM-Server nicht erreichbar")
    return out

def search_google(lat, lng, radius_m, keys, google_key, max_calls=None):
    """Google-Umkreissuche, auf maximale Vollständigkeit ausgelegt.

    - Freitext-Suchbegriffe je Branche (GOOGLE_QUERIES), damit auch Betriebe
      gefunden werden, die bei Google unter keinem passenden Typ eingetragen sind.
    - Strikte Begrenzung auf ein Rechteck (locationRestriction) – Google liefert
      nur Treffer innerhalb des Gebiets.
    - Quadtree: Liefert ein Gebiet die Google-Höchstzahl von 60 Treffern, wird es
      in 4 Teilgebiete zerlegt und erneut abgefragt – so lange, bis nichts mehr
      abgeschnitten wird (max. 5 Ebenen).
    """
    seen, out = set(), []
    radius_m = min(radius_m, 50000)
    dlat = radius_m / 111320.0
    dlng = radius_m / (111320.0 * _math.cos(_math.radians(lat)))
    stats = {"calls": 0, "splits": 0}
    MAX_DEPTH = 5

    def query_rect(q, label, lo_lat, lo_lng, hi_lat, hi_lng):
        got, token = 0, None
        for _page in range(3):
            body = {"textQuery": q, "languageCode": "de", "regionCode": "DE", "pageSize": 20,
                    "locationRestriction": {"rectangle": {"low": {"latitude": lo_lat, "longitude": lo_lng},
                                                          "high": {"latitude": hi_lat, "longitude": hi_lng}}}}
            if token:
                body["pageToken"] = token
            stats["calls"] += 1
            try:
                r = requests.post(PLACES_URL, json=body, timeout=20,
                                  headers={"Content-Type": "application/json", "X-Goog-Api-Key": google_key,
                                           "X-Goog-FieldMask": FIELD_MASK})
                data = r.json()
            except Exception as e:
                _log(f"⚠ Google-Fehler ({q}): {e}"); return got
            if "error" in data:
                err = data["error"]; status = str(err.get("status", ""))
                if "API key" in err.get("message", "") or status in ("PERMISSION_DENIED", "UNAUTHENTICATED") or err.get("code") in (401, 403):
                    raise GoogleDenied(google_error_text(err))
                if status == "RESOURCE_EXHAUSTED" or err.get("code") == 429:
                    _log(f"⚠ Google-Limit: {google_error_text(err)} – kurze Pause"); time.sleep(10); return got
                _log(f"⚠ Google ({q}): {google_error_text(err)[:160]}"); return got
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
            if not token or (max_calls and stats["calls"] >= max_calls * 1.15): break
            time.sleep(1.2)
        return got

    budget = {"warned": False}
    def over_budget():
        return bool(max_calls) and stats["calls"] >= max_calls

    def search_cell(q, label, lo_lat, lo_lng, hi_lat, hi_lng, depth):
        got = query_rect(q, label, lo_lat, lo_lng, hi_lat, hi_lng)
        if got >= 60 and depth < MAX_DEPTH and over_budget():
            if not budget["warned"]:
                _log(f"⚠ Kostenbremse erreicht ({max_calls} Google-Abfragen) – dichte Gebiete werden nicht weiter zerlegt")
                budget["warned"] = True
            return
        if got >= 60 and depth < MAX_DEPTH:
            stats["splits"] += 1
            mid_lat, mid_lng = (lo_lat + hi_lat) / 2, (lo_lng + hi_lng) / 2
            for a, b, c2, d in ((lo_lat, lo_lng, mid_lat, mid_lng), (lo_lat, mid_lng, mid_lat, hi_lng),
                                (mid_lat, lo_lng, hi_lat, mid_lng), (mid_lat, mid_lng, hi_lat, hi_lng)):
                # nur Teilgebiete prüfen, die den Suchkreis berühren
                clat = min(max(lat, a), c2); clng = min(max(lng, b), d)
                if haversine_km(lat, lng, clat, clng) * 1000 <= radius_m:
                    search_cell(q, label, a, b, c2, d, depth + 1)

    jobs = [(q, BRANCHEN[k][0]) for k in keys for q in GOOGLE_QUERIES.get(k, [])]
    for i, (q, label) in enumerate(jobs, 1):
        _prog(i, len(jobs), f"Google · {label} · {q}  ({len(out)} gefunden)")
        search_cell(q, label, lat - dlat, lng - dlng, lat + dlat, lng + dlng, 0)
        time.sleep(0.1)
    _log(f"✓ Google: {len(out)} Unternehmen · {stats['calls']} Abfragen · {stats['splits']} verdichtete Gebiete")
    LAST_STATS["google_calls"] = stats["calls"]
    return out


# Pfade, unter denen deutsche Firmen-Websites ihr Impressum/Kontakt führen
IMPRESSUM_PATHS = ["/impressum", "/impressum/", "/impressum.html", "/impressum.php",
                   "/imprint", "/kontakt", "/kontakt/", "/contact", "/kontakt.html",
                   "/ueber-uns", "/about", "/datenschutz"]

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

def _decode_cfemail(h):
    """Cloudflare-Email-Schutz entschlüsseln ([email protected] → echte Adresse)."""
    try:
        key = int(h[:2], 16)
        return "".join(chr(int(h[i:i + 2], 16) ^ key) for i in range(2, len(h), 2))
    except Exception:
        return ""

def _get(url):
    """GET mit https→http-Fallback. Gibt Response oder None."""
    for u in (url, url.replace("https://", "http://", 1)) if url.startswith("https://") else (url,):
        try:
            r = requests.get(u, headers=HEADERS, timeout=7, allow_redirects=True)
            if r.status_code == 200 and r.text:
                return r
        except Exception:
            continue
    return None

def _soup_text(soup):
    """Sichtbarer Text + versteckte E-Mails (mailto-Links, Cloudflare-Schutz)."""
    extras = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if h.lower().startswith("mailto:"):
            extras.append(h[7:].split("?")[0])
        elif "email-protection#" in h:
            extras.append(_decode_cfemail(h.split("#")[-1]))
    for el in soup.find_all(attrs={"data-cfemail": True}):
        extras.append(_decode_cfemail(el["data-cfemail"]))
    for s in soup(["script", "style", "noscript"]):
        s.decompose()
    return " ".join(extras) + " " + soup.get_text(" ")

def fetch_text(url):
    r = _get(url)
    if not r:
        return ""
    return _soup_text(BeautifulSoup(r.text, "html.parser"))

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

FREEMAIL = ("t-online.de", "gmx.de", "gmx.net", "web.de", "gmail.com", "googlemail.com", "outlook.com",
            "outlook.de", "hotmail.com", "hotmail.de", "yahoo.de", "yahoo.com", "freenet.de", "arcor.de",
            "online.de", "icloud.com", "posteo.de", "mail.de", "aol.com")
AGENCY_HINTS = ("agentur", "webdesign", "design", "media", "werbung", "marketing", "hosting", "ionos", "strato", "jimdo", "wix")

def pick_email(text, domain="", strict=False):
    """E-Mail wählen: 1) passend zur Firmendomain, 2) Freemail (typisch Kleinbetrieb),
    3) nur im Impressum (strict=False): sonstige Adresse, Agentur-Adressen zuletzt.
    strict=True (Startseite): nur Firmendomain oder Freemail – vermeidet Agentur-Footer."""
    text = (text or "").replace("(at)", "@").replace("[at]", "@").replace(" at ", "@").replace("(dot)", ".").replace("[dot]", ".")
    found = []
    for m in re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text):
        low = m.lower().strip(".")
        if any(x in low for x in ("noreply", "no-reply", "example", "mailer", "sentry", "wixpress", "@2x", ".png", ".jpg",
                                  ".gif", ".webp", "webmaster@", "domain.", "beispiel", "muster@", "@sentry")):
            continue
        if low not in found:
            found.append(low)
    if not found:
        return ""
    d = (domain or "").lower().replace("www.", "")
    root = d.rsplit(".", 1)[0] if "." in d else d
    own = [e for e in found if d and (e.split("@")[1] == d or e.split("@")[1].endswith("." + d) or (len(root) > 3 and root in e.split("@")[1]))]
    if own:
        return own[0]
    free = [e for e in found if e.split("@")[1] in FREEMAIL]
    if free:
        return free[0]
    if strict:
        return ""
    others = sorted(found, key=lambda e: any(h in e for h in AGENCY_HINTS))
    return others[0]

def scrape_site(website):
    """Startseite → Impressum-/Kontakt-Links → Standardpfade. Liefert Kontakte und Firmeninfos."""
    base = norm(website)
    res = {"email": "", "telefon": "", "ansprechpartner": "", "rechtsform": "", "hrb": "",
           "mitarbeiter": None, "gruendung": None, "beschreibung": ""}
    if not base:
        return res
    imp_texts, other_texts, tried = [], [], set()

    # 1) Startseite: Beschreibung, Text, Links auf Impressum/Kontakt
    links = []
    r = _get(website if website.startswith("http") else base)
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        res["beschreibung"] = find_beschreibung(soup)
        for a in soup.find_all("a", href=True):
            label = (a.get_text(" ") + " " + a["href"]).lower()
            if any(w in label for w in ("impressum", "imprint", "kontakt", "contact")):
                href = a["href"]
                if href.startswith("mailto:") or href.startswith("tel:"):
                    continue
                full = href if href.startswith("http") else base + ("" if href.startswith("/") else "/") + href
                if full not in links:
                    links.append(full)
        other_texts.append(_soup_text(soup))
    links.sort(key=lambda u: 0 if ("impressum" in u.lower() or "imprint" in u.lower()) else 1)

    # 2) Gefundene Impressum-/Kontakt-Links (max. 3)
    for u in links[:3]:
        tried.add(u.rstrip("/"))
        t = fetch_text(u)
        if t:
            imp_texts.append(t)
        if t and find_email(t) and ("impressum" in u.lower() or "imprint" in u.lower()):
            break

    # 3) Standardpfade, falls noch keine E-Mail
    if not any(find_email(t) for t in imp_texts + other_texts):
        for path in IMPRESSUM_PATHS[:8]:
            u = base + path
            if u.rstrip("/") in tried:
                continue
            t = fetch_text(u)
            if t:
                imp_texts.append(t)
                if find_email(t):
                    break

    imp = " ".join(imp_texts); alltext = imp + " " + " ".join(other_texts)
    if not alltext.strip():
        return res
    domain = urlparse(base).netloc
    other = " ".join(other_texts)
    res["email"] = pick_email(imp, domain) or pick_email(other, domain, strict=True)
    res["telefon"] = find_phone(imp) or find_phone(alltext)
    res["ansprechpartner"] = find_name(imp) or find_name(alltext)
    res["rechtsform"] = find_rechtsform(imp) or find_rechtsform(alltext)
    res["hrb"] = find_hrb(imp) or find_hrb(alltext)
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
        max_n=None, size_filter=None, workers=24, max_google_calls=None, checkpoint=None, coords=None):
    """Recherche ausführen. Rückgabe: (excel_dateiname | None, liste_unternehmen)
    max_n:        maximale Anzahl Ergebnisse (nächstgelegene passende zuerst)
    size_filter:  Menge erlaubter Größenklassen (None = alle)
    workers:      parallele Website-Analysen
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    _log(f"⚙ Recherche-Engine {VERSION}")
    _log(f"📍 Adresse: {adresse}")
    if coords:
        lat, lng = coords; disp, geo_src = adresse, "gespeichert"
    else:
        lat, lng, disp, geo_src = geocode(adresse, google_key)
    _log(f"→ {disp[:75]}  ({geo_src})")

    LEGAL = r"\b(gmbh|co|kg|ag|ug|ohg|gbr|e\.?k|ek|mbh|haftungsbeschränkt|inh|inhaber|und|the)\b"
    GENERIC = {w for qs in GOOGLE_QUERIES.values() for q in qs for w in re.sub(r"[^a-zäöüß ]", " ", q.lower()).split()}
    GENERIC |= {"praxis", "für", "der", "die", "das", "und", "service", "haus", "shop", "studio", "center", "zentrum",
                "team", "partner", "gruppe", "bad", "pyrmont", "inh", "dr", "med", "dipl", "ing", "filiale", "markt",
                "salon", "laden", "betrieb", "fachbetrieb", "meisterbetrieb", "handel", "bau", "auto", "hotel", "café", "cafe"}
    def _tokens(name):
        n = re.sub(LEGAL, " ", (name or "").lower())
        n = re.sub(r"[^a-z0-9äöüß ]", " ", n)
        return {t for t in n.split() if len(t) > 2 and t not in GENERIC}

    def _same(a, b):
        """Gleiche Firma? Namensähnlichkeit + Nähe (oder gleiche Adresse)."""
        ta, tb = _tokens(a["firma"]), _tokens(b["firma"])
        if not ta or not tb:   # nur Branchenwörter im Namen → nur bei identischem Namen zusammenlegen
            same_name = re.sub(r"[^a-z0-9]", "", a["firma"].lower()) == re.sub(r"[^a-z0-9]", "", b["firma"].lower())
            if not same_name:
                return False
            ta = tb = {"x"}
        sim = len(ta & tb) / min(len(ta), len(tb))
        if a.get("lat") and b.get("lat") and a.get("lng") and b.get("lng"):
            near = haversine_km(a["lat"], a["lng"], b["lat"], b["lng"]) <= 0.15
        else:
            near = bool(a.get("adresse")) and a.get("adresse", "").lower()[:12] == b.get("adresse", "").lower()[:12]
        return near and sim >= 0.5

    LAST_STATS.clear()
    LAST_STATS["coords"] = (lat, lng)
    if google_key:
        _log(f"🔍 Google Places – {radius_km} km Umkreis, {len(keys)} Branchen …")
        try:
            kands = search_google(lat, lng, radius_km * 1000, keys, google_key, max_calls=max_google_calls)
        except GoogleDenied as e:
            _log(f"⛔ Google abgelehnt: {e}")
            _log("→ Recherche läuft nur mit OpenStreetMap weiter")
            LAST_STATS["google_fehler"] = str(e)
            kands = []
        LAST_STATS["google"] = len(kands)
        try:
            _log("🔍 OpenStreetMap ergänzend …")
            osm = search_osm(lat, lng, radius_km * 1000, keys)
        except SystemExit as e:
            if LAST_STATS.get("google_fehler"):
                raise SystemExit(f"Weder Google noch OpenStreetMap liefern Daten. Google: {LAST_STATS['google_fehler']} · OSM: {str(e).strip()}")
            _log(f"⚠ OSM nicht verfügbar ({str(e).strip()[:60]}) – Ergebnis nur aus Google")
            osm = []
            LAST_STATS["osm_fehler"] = True
        # Raster-Index für schnellen Nachbarschaftsabgleich (~1 km Zellen)
        grid = {}
        for g in kands:
            if g.get("lat") and g.get("lng"):
                grid.setdefault((round(g["lat"], 2), round(g["lng"], 2)), []).append(g)
        added, enriched = 0, 0
        for o in osm:
            match = None
            if o.get("lat") and o.get("lng"):
                cy, cx = round(o["lat"], 2), round(o["lng"], 2)
                for dy in (-0.01, 0, 0.01):
                    for dx in (-0.01, 0, 0.01):
                        for g in grid.get((round(cy + dy, 2), round(cx + dx, 2)), []):
                            if _same(o, g):
                                match = g; break
                        if match: break
                    if match: break
            if match:
                for f in ("telefon", "website", "email"):
                    if not match.get(f) and o.get(f):
                        match[f] = o[f]; enriched += 1
            else:
                kands.append(o); added += 1
                if o.get("lat") and o.get("lng"):
                    grid.setdefault((round(o["lat"], 2), round(o["lng"], 2)), []).append(o)
        LAST_STATS["osm"] = added
        _log(f"✓ OSM: {len(osm)} Einträge · {added} zusätzliche Unternehmen · {enriched} Google-Einträge ergänzt")
        quelle = ("OpenStreetMap (Google gesperrt)" if LAST_STATS.get("google_fehler")
                  else "Google + OpenStreetMap" if osm else "Google")
    else:
        _log(f"🔍 OpenStreetMap – {radius_km} km Umkreis, {len(keys)} Branchen …")
        LAST_STATS.clear(); LAST_STATS["coords"] = (lat, lng)
        kands = search_osm(lat, lng, radius_km * 1000, keys)
        LAST_STATS["osm"] = len(kands)
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

    def _ckpt(rows, phase):
        if checkpoint:
            try:
                checkpoint(rows, phase)
            except Exception as e:
                _log(f"⚠ Zwischenspeichern fehlgeschlagen: {e}")
    if not max_n:   # bei Maximalzahl erst nach der Auswahl sichern
        _ckpt([dict(k) for k in kands if finalize(k)], "suche")

    total, done, found, kept = len(kands), 0, 0, []
    analysed, errors, first_error = 0, 0, ""
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
                    analysed += 1
                except Exception as e:
                    info = {}
                    errors += 1
                    if not first_error:
                        first_error = f"{type(e).__name__}: {e}"
                if info.get("email") and not k["email"]:
                    k["email"] = info["email"]; found += 1
                if info.get("telefon") and not k["telefon"]:
                    k["telefon"] = info["telefon"]
                for fld in ("ansprechpartner", "rechtsform", "hrb", "mitarbeiter", "gruendung", "beschreibung"):
                    if info.get(fld) not in (None, ""):
                        k[fld] = info[fld]
                done += 1
                _prog(done, total, f"{k['firma'][:40]}  ·  {found} E-Mails")
            for k in chunk:
                if finalize(k):
                    kept.append(k)
                if max_n and len(kept) >= max_n:
                    break
            _ckpt(kept, "analyse")
            if max_n and len(kept) >= max_n:
                _log(f"✓ Maximalzahl von {max_n} Unternehmen erreicht")
                break
    if scrape:
        _log(f"✓ Website-Analyse: {analysed} Websites gelesen · {found} E-Mail-Adressen gefunden")
        if errors:
            _log(f"⚠ {errors} Websites mit Programmfehler – erster Fehler: {first_error}")

    # Kontakt-Status: klar filterbar, keine Firma geht verloren
    for k in kept:
        if k.get("email"):
            k["kontakt_status"] = "E-Mail vorhanden"
        elif k.get("telefon"):
            k["kontakt_status"] = "nur Telefon"
        else:
            k["kontakt_status"] = "kein Kontakt"
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
