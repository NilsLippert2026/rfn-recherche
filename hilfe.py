"""
Hilfetexte für das RFN Sponsoring Cockpit.
Diese Datei enthält nur Text – sie kann ohne Programmierkenntnisse angepasst werden.
Markdown ist erlaubt (**fett**, Listen mit "- ").
"""

# ─────────────────────────────── Geführte Tour ───────────────────────────────
# page = Seite, auf die der Knopf "Zur Seite" springt (Index in PAGES, None = kein Sprung)
TOUR = [
    {"icon": "👋", "title": "Willkommen im Sponsoring Cockpit", "page": 0, "text": """
Das Cockpit begleitet dich vom ersten Kontakt bis zum gewonnenen Sponsor – in drei Schritten:

1. **Recherche** – Unternehmen im Umkreis eines Vereins finden, inklusive E-Mail, Telefon und Firmeninfos
2. **Pipeline** – Unternehmen ansprechen, Status pflegen, Leistungen anbieten
3. **Sponsoren** – Abschlüsse, Umsatz und Aufteilung im Blick behalten

Links in der Seitenleiste wählst du die Bereiche. Darunter steht die **Vereinsauswahl**: „Alle Vereine“ oder ein einzelner Verein – alle Seiten zeigen dann nur dessen Daten.
"""},
    {"icon": "🔍", "title": "Neue Recherche", "page": None, "text": """
Klick oben links auf **„＋ Neue Recherche“**. Im Fenster legst du fest:

- **Verein** – bestehenden wählen oder neuen anlegen
- **Standort** – Adresse mit Straße, Hausnummer und PLZ, von hier aus wird gesucht
- **Umkreis** – Kleinstadt 10–15 km, Großstadt 2–5 km
- **Branchen** und **Unternehmensgröße**
- **Google zusätzlich nutzen** – mehr Treffer, aber kostenpflichtig. Aus = nur OpenStreetMap, kostenlos

Die Recherche läuft **im Hintergrund** auf dem Server. Du kannst weiterarbeiten oder den Tab schließen. Mit **„Zwischenstand laden“** siehst du schon erste Ergebnisse.
"""},
    {"icon": "🎯", "title": "Leads & Pipeline", "page": 1, "text": """
Hier landen alle gefundenen Unternehmen.

- **Filter** oben: Suche, Kontakt (E-Mail / nur Telefon / kein Kontakt), Status, Branche, Größe, Vertriebler
- **Direkt in der Tabelle ändern**: Status, Vertriebler, E-Mail, Telefon, Ansprechpartner – danach unten auf **„Änderungen speichern“**
- **Excel / CSV** exportiert genau die aktuell gefilterte Auswahl

Tipp: Filter **Kontakt = „E-Mail vorhanden“** zeigt dir alle sofort anschreibbaren Unternehmen.
"""},
    {"icon": "🏢", "title": "Ein Unternehmen bearbeiten", "page": 1, "text": """
Unter der Tabelle wählst du bei **„Unternehmen öffnen“** eine Firma aus. Dort kannst du:

- Status, Vertriebler, Notiz und bei Absagen den **Verlustgrund** pflegen
- **Leistungen buchen** – aus dem Katalog des Vereins wählen, Menge und Preis individuell anpassen
- Den **Sponsoring-Wert** und die Aufteilung (Verein / RFN / Provision) sofort sehen
- Mit **🏆 Gewonnen** oder **✕ Verloren** abschließen
- Im **Verlauf** Telefonate und Absprachen notieren
"""},
    {"icon": "🤝", "title": "Sponsoren & Dashboard", "page": 2, "text": """
- **Sponsoren** zeigt alle gewonnenen Unternehmen mit gebuchten Leistungen und Werten, alle verlorenen mit Gründen und eine Übersicht, welche Leistungen am meisten gebucht werden.
- Das **Dashboard** fasst alles zusammen: Pipeline, Abschlussquote, Sponsoring-Volumen und die Aufteilung auf Verein, RFN und Vertriebsprovision.
"""},
    {"icon": "💶", "title": "Leistungen & Preise", "page": 3, "text": """
Jeder Verein hat einen eigenen **Leistungskatalog** (Bande, Trikot, Website-Logo …) mit Listenpreisen.

- **Leistungen pro Verein**: Leistungen aktivieren/deaktivieren, neue Zeilen ergänzen, Preise anpassen, dann speichern
- **Globale Vorlage**: Startkatalog für jeden **neuen** Verein

Beim Buchen in einem Unternehmen kannst du den Preis trotzdem individuell verhandeln.
"""},
    {"icon": "⚙️", "title": "Einstellungen & Hilfe", "page": 5, "nur_admin": True, "text": """
In den **Einstellungen** legst du fest:

- **Provisionsmodell** – RFN-Anteil und Vertriebsprovision
- **Team** – Namen der Vertriebler für die Zuordnung
- **Kostenbremse Google** und ob Google standardmäßig an ist
- **Branchen & Suchbegriffe** – fehlende Begriffe selbst ergänzen
- **Backup** und **Vereine verwalten**

Als Admin lädst du unter **👥 Team & Zugänge** Kollegen ein und legst fest, welche Vereine sie sehen.
Das eigene Passwort änderst du unter **👤 Mein Konto**.

Alle Fragen und Antworten findest du jederzeit unter **❓ Hilfe** in der Seitenleiste. Viel Erfolg! ⚽
"""},
]

# Abschluss-Schritt für Vertriebler (statt der Einstellungen)
TOUR_REP_END = {"icon": "👤", "title": "Mein Konto & Hilfe", "page": 8, "text": """
- Du siehst die **Vereine, die dir zugeordnet sind**, und beim Geld deine **eigene Provision** aus den Abschlüssen, die dir zugeordnet sind.
- Ordne Unternehmen, die du betreust, im Feld **Vertriebler** dir selbst zu – nur dann zählt der Abschluss für deine Provision.
- Unter **👤 Mein Konto** änderst du dein Passwort.
- Alle Fragen und Antworten findest du jederzeit unter **❓ Hilfe**. Viel Erfolg! ⚽
"""}

# Fragen bzw. Bereiche, die nur Admins sehen
ADMIN_ONLY_CATS = {"🧑‍💻 Für Admins"}
REP_ONLY_FAQ = {"Was sehe ich als Vertriebler?"}
ADMIN_ONLY_FAQ = {"Wer kann was sehen?", "Wie wird der Sponsoring-Wert aufgeteilt?", "Was ist der Inhaber-Notzugang?",
                  "Wie lade ich einen Kollegen ein?", "Ein Kollege hört auf – was passiert mit seinen Daten?",
                  "Wie mache ich ein Backup?", "Wie verhindere ich hohe Kosten?", "Mir fehlt eine Branche oder ein Suchbegriff."}

REP_TEXT = {
    "Ein Unternehmen bearbeiten": """
Unter der Tabelle wählst du bei **„Unternehmen öffnen“** eine Firma aus. Dort kannst du:

- Status, Vertriebler, Notiz und bei Absagen den **Verlustgrund** pflegen
- **Leistungen buchen** – aus dem Katalog des Vereins wählen, Menge und Preis individuell anpassen
- Den **Sponsoring-Wert** und – wenn dir das Unternehmen zugeordnet ist – **deine Provision** sofort sehen
- Mit **🏆 Gewonnen** oder **✕ Verloren** abschließen
- Im **Verlauf** Telefonate und Absprachen notieren
""",
    "Sponsoren & Dashboard": """
- **Sponsoren** zeigt alle gewonnenen Unternehmen deiner Vereine mit gebuchten Leistungen und Werten, alle verlorenen mit Gründen und welche Leistungen am meisten gebucht werden.
- Das **Dashboard** fasst alles zusammen: Pipeline, Abschlussquote, Sponsoring-Volumen sowie **deine Abschlüsse und deine Provision**.
""",
}

def tour_for(admin):
    if admin:
        return TOUR
    steps = [dict(s, text=REP_TEXT.get(s["title"], s["text"])) for s in TOUR if not s.get("nur_admin")]
    return steps + [TOUR_REP_END]

def faq_for(admin):
    if admin:
        return {cat: [(q, a) for q, a in items if q not in REP_ONLY_FAQ] for cat, items in FAQ.items()}
    return {cat: [(q, a) for q, a in items if q not in ADMIN_ONLY_FAQ]
            for cat, items in FAQ.items() if cat not in ADMIN_ONLY_CATS}

def hint_for(key, admin):
    return PAGE_HINTS.get(f"{key}_rep") if not admin and f"{key}_rep" in PAGE_HINTS else PAGE_HINTS.get(key)

# ─────────────────────────────── Hinweise je Seite ───────────────────────────────
PAGE_HINTS = {
    "team": """
- **Einladen:** Name, E-Mail, Rolle und Vereine eintragen → „Einladung erstellen“. Den Link (oder die fertige Nachricht) per E-Mail oder WhatsApp schicken. Der Link gilt 7 Tage.
- **Vertrieb** sieht nur die zugeordneten Vereine und beim Geld nur Sponsoringwert und eigene Provision. **Admin** sieht alles.
- **Rechte:** „Recherche“ erlaubt eigene Suchläufe (nur OpenStreetMap), „Google“ zusätzlich die kostenpflichtige Google-Suche.
- **Passwort vergessen:** Person auswählen → „Neuer Link“. **Ausgeschieden:** Haken „aktiv“ entfernen – Leads und Abschlüsse bleiben erhalten.
""",
    "dashboard": """
- Oben die Kennzahlen, darunter Sponsoring-Volumen und Aufteilung auf Verein / RFN / Provision.
- Die Diagramme zeigen Pipeline, Verlauf von Zu- und Absagen, Branchen und Unternehmensgrößen.
- Über die **Vereinsauswahl** in der Seitenleiste wechselst du zwischen allen Vereinen und einem einzelnen.
""",
    "dashboard_rep": """
- Oben die Kennzahlen deiner Vereine, darunter **deine Abschlüsse, dein Volumen und deine Provision**.
- Die Diagramme zeigen Pipeline, Zu- und Absagen, Branchen und Unternehmensgrößen.
- Über die **Vereinsauswahl** in der Seitenleiste wechselst du zwischen deinen Vereinen.
""",
    "sponsoren_rep": """
- **Gewonnen**: alle Sponsoren deiner Vereine mit Leistungen und Wert. Bei Abschlüssen, die dir zugeordnet sind, siehst du deine Provision.
- **Verloren**: Absagen mit Grund – hilft zu verstehen, woran es hakt.
- **Leistungsübersicht**: welche Leistungen wie oft gebucht wurden.
""",
    "leistungen_rep": """
- Hier siehst du die buchbaren Leistungen deiner Vereine mit Listenpreisen.
- Beim Buchen im Unternehmen kannst du Menge und Preis individuell anpassen.
- Änderungen am Katalog nimmt ein Admin vor.
""",
    "leads": """
- **Filtern**: Suche und Auswahlfelder oben. „Kontakt = E-Mail vorhanden“ zeigt alle direkt anschreibbaren Firmen.
- **Ändern**: Status, Vertriebler, E-Mail, Telefon und Ansprechpartner direkt in der Tabelle anklicken – dann **„Änderungen speichern“**.
- **Details & Leistungen**: unten bei „Unternehmen öffnen“ eine Firma auswählen.
- **Spalten** lassen sich oben ein- und ausblenden. Excel/CSV exportiert die gefilterte Auswahl.
""",
    "sponsoren": """
- **Gewonnen**: alle Sponsoren mit Leistungen, Wert und Aufteilung – als Excel exportierbar.
- **Verloren**: Absagen mit Grund – hilft zu verstehen, woran es hakt.
- **Leistungsübersicht**: welche Leistungen wie oft und mit welchem Umsatz gebucht wurden.
""",
    "leistungen": """
- **Aktiv** anhaken = im Verein buchbar. Neue Leistung: unten in der Tabelle eine Zeile hinzufügen.
- Zeile löschen: Zeile markieren und Entf drücken. Danach immer **Speichern**.
- Die **globale Vorlage** gilt nur für neue Vereine – bestehende ändern sich dadurch nicht.
""",
    "recherchen": """
- Jede Zeile ist ein Suchlauf. **Quelle** zeigt, wie viele Treffer aus Google und OpenStreetMap kamen.
- **Google-Abfragen** zeigt den Verbrauch – wichtig für die Kosten.
- „Neu übernommen“ sind Unternehmen, die vorher noch nicht in der Pipeline standen.
""",
    "einstellungen": """
- Änderungen in jeder Karte mit dem jeweiligen **Speichern**-Knopf übernehmen.
- **Kostenbremse**: höchstens so viele Google-Abfragen pro Recherche.
- **Backup** regelmäßig herunterladen – als doppelter Boden.
""",
}

# ─────────────────────────────── Statusbedeutungen ───────────────────────────────
STATUS_HELP = [
    ("Neu", "Gefunden, mit E-Mail – bereit für die erste Ansprache"),
    ("Anruf nötig", "Telefon vorhanden, aber keine E-Mail – kurz anrufen und E-Mail erfragen"),
    ("Kontaktiert", "Erste Nachricht ist raus"),
    ("Follow-Up", "Nachgefasst, noch keine Entscheidung"),
    ("Angebot", "Konkretes Angebot liegt beim Unternehmen"),
    ("Gewonnen", "Sponsor! Leistungen buchen, Wert wird automatisch berechnet"),
    ("Verloren", "Absage – Verlustgrund eintragen"),
]

# ─────────────────────────────── FAQ ───────────────────────────────
FAQ = {
    "🚀 Erste Schritte": [
        ("Wie fange ich an?",
         "Oben links **„＋ Neue Recherche“** klicken, Verein anlegen, Adresse und Umkreis eintragen, starten. "
         "Nach der Recherche findest du alle Unternehmen unter **Leads & Pipeline**."),
        ("Was bedeutet die Vereinsauswahl in der Seitenleiste?",
         "„Alle Vereine“ zeigt alles zusammen. Wählst du einen Verein, zeigen Dashboard, Pipeline und Sponsoren nur dessen Daten."),
        ("Kann ich die Tour nochmal ansehen?",
         "Ja – hier auf der Hilfe-Seite oben auf **„▶ Tour starten“** klicken."),
    ],
    "🔍 Recherche": [
        ("Welchen Umkreis soll ich wählen?",
         "Kleinstadt und ländlich: **10–15 km**. Großstadt: **2–5 km** – dort gibt es auf kleiner Fläche schon tausende Betriebe."),
        ("Wie lange dauert eine Recherche?",
         "Je nach Gebiet und Branchen **5 bis 30 Minuten**. Am längsten dauert das Auslesen der Firmen-Websites nach E-Mail-Adressen. "
         "Die Recherche läuft im Hintergrund weiter, auch wenn du den Tab schließt."),
        ("Woher kommen die Daten?",
         "Aus **OpenStreetMap** (kostenlos, immer aktiv) und optional aus **Google Places** (mehr Treffer, kostenpflichtig). "
         "E-Mail, Ansprechpartner und Firmeninfos liest das Tool anschließend aus dem **Impressum** der Firmen-Websites."),
        ("Warum haben manche Unternehmen keine E-Mail?",
         "Wenn eine Firma **keine eigene Website** hat oder im Impressum nur ein Kontaktformular steht, kann keine E-Mail gefunden werden. "
         "Diese stehen auf **„Anruf nötig“** – Telefonnummer ist meist vorhanden. E-Mail erfragen und in der Tabelle eintragen."),
        ("Was bedeutet „gesichert: … Unternehmen“ während der Recherche?",
         "Das Tool speichert unterwegs. Bricht etwas ab, bleiben alle bereits gesicherten Unternehmen erhalten."),
        ("Kann ich eine Recherche für denselben Verein wiederholen?",
         "Ja. Bereits vorhandene Unternehmen werden nicht doppelt angelegt, fehlende Angaben (z. B. E-Mail) werden ergänzt. "
         "Status und Notizen bleiben erhalten."),
        ("Was bedeutet der Score?",
         "Eine Bewertung von 0–100, wie gut ein Lead ist: E-Mail +30, Telefon +15, Ansprechpartner +15, Website +10, "
         "gute Google-Bewertung +10, viele Bewertungen +10, Klein-/Mittelstand +10, Filiale einer Kette −15 "
         "(der Entscheider sitzt dort meist nicht vor Ort)."),
        ("Wie wird die Unternehmensgröße bestimmt?",
         "Nach EU-Definition: Kleinst < 10, Klein < 50, Mittelstand < 250, Groß ab 250 Mitarbeitern. "
         "Grundlage ist – in dieser Reihenfolge – die Mitarbeiterzahl von der Website, die Rechtsform, die Erkennung als Kette oder eine Schätzung. "
         "Die Spalte „Größe – Basis“ im Export zeigt, worauf die Einstufung beruht."),
        ("Mir fehlt eine Branche oder ein Suchbegriff.",
         "Unter **Einstellungen → Branchen & Google-Suchbegriffe** kannst du je Branche eigene Begriffe ergänzen (einer pro Zeile)."),
    ],
    "🎯 Pipeline & Sponsoren": [
        ("Wie ändere ich den Status?",
         "Direkt in der Tabelle unter **Leads & Pipeline** in die Status-Zelle klicken, auswählen, unten **„Änderungen speichern“**. "
         "Oder das Unternehmen unten öffnen und dort ändern."),
        ("Wie trage ich einen gewonnenen Sponsor ein?",
         "Unternehmen öffnen → **Leistungen auswählen** → Menge und Preis prüfen → **🏆 Gewonnen**. "
         "Der Wert und die Aufteilung werden automatisch berechnet und erscheinen im Dashboard."),
        ("Ich habe mich verklickt – wie mache ich „Gewonnen“ oder „Verloren“ rückgängig?",
         "Unternehmen öffnen, Status im Auswahlfeld zurücksetzen und **Speichern**. Der Verlauf dokumentiert die Änderung."),
        ("Wie wird der Sponsoring-Wert aufgeteilt?",
         "Gesamtwert = Summe der gebuchten Leistungen. Davon geht der RFN-Anteil an Regionalfußball.net, der Rest an den Verein. "
         "Vom RFN-Anteil geht die Vertriebsprovision an den zugewiesenen Vertriebler. Die Prozentsätze stehen in den Einstellungen."),
        ("Wie exportiere ich eine Liste?",
         "Unter **Leads & Pipeline** filtern, dann **„Excel (Auswahl)“** oder **„CSV (Auswahl)“**. "
         "Unter **Sponsoren** gibt es zusätzlich Exporte für Gewonnene und Verlorene."),
        ("Wie lösche ich ein Unternehmen?",
         "Unternehmen öffnen → Mülleimer-Knopf → bestätigen."),
    ],
    "💰 Kosten & Google": [
        ("Kostet die Recherche Geld?",
         "**Nur mit eingeschaltetem Google.** OpenStreetMap und das Auslesen der Websites sind kostenlos. "
         "Im Recherche-Fenster siehst du vor dem Start, wie viele Google-Abfragen mindestens anfallen."),
        ("Was kostet Google ungefähr?",
         "Monatlich sind 1.000 Abfragen frei, danach etwa 35 $ je 1.000 Abfragen (Stand 2026, aktuelle Preise unter mapsplatform.google.com/pricing). "
         "Jeder Suchbegriff ist mindestens eine Abfrage, in dichten Großstädten deutlich mehr."),
        ("Wie verhindere ich hohe Kosten?",
         "Drei Sicherungen: die **Kostenbremse** in den Einstellungen (Abfragen pro Recherche), ein **Tageslimit** direkt in der Google Cloud Console "
         "und Google im Recherche-Fenster nur einschalten, wenn nötig. In Großstädten kleinen Umkreis und nur die wichtigsten Branchen wählen."),
        ("Was bedeutet „Google gesperrt“ in der Meldung?",
         "Google hat die Abfrage abgelehnt (z. B. Tageslimit erreicht, Abrechnung nicht aktiv). Die Recherche läuft dann automatisch "
         "nur mit OpenStreetMap weiter. Der genaue Grund steht in der Meldung."),
    ],
    "🔐 Daten & Zugang": [
        ("Wer kann was sehen?",
         "Jede Person meldet sich mit **eigener E-Mail und eigenem Passwort** an. **Admins** sehen alles. **Vertriebler** sehen nur die Vereine, "
         "die ihnen zugeordnet sind, und beim Geld nur den Sponsoringwert und ihre eigene Provision – nicht den RFN-Anteil und nicht den Vereinsanteil. "
         "Die Trennung passiert auf dem Server: Fremde Daten werden gar nicht erst an den Browser geschickt."),
        ("Was sehe ich als Vertriebler?",
         "Die Vereine, die dir zugeordnet sind, mit allen Unternehmen, Status und Abschlüssen. Beim Geld siehst du den Sponsoringwert "
         "und deine eigene Provision aus den Abschlüssen, die dir zugeordnet sind. Fehlt dir ein Verein, wende dich an einen Admin."),
        ("Wie lade ich einen Kollegen ein?",
         "**👥 Team & Zugänge → Kollegen einladen.** Name, E-Mail, Rolle und Vereine eintragen, „Einladung erstellen“. "
         "Den angezeigten Link schicken – damit legt der Kollege sein Passwort selbst fest. Der Link gilt 7 Tage."),
        ("Passwort vergessen – was tun?",
         "Ein Admin wählt die Person unter **👥 Team & Zugänge** aus und klickt **„Neuer Link“**. Damit wird ein neues Passwort festgelegt. "
         "Das eigene Passwort ändern geht jederzeit unter **👤 Mein Konto**."),
        ("Darf ein Vertriebler Recherchen starten?",
         "Nur wenn der Admin es unter **👥 Team & Zugänge** freigibt. Google (kostenpflichtig) ist ein eigenes Recht und standardmäßig aus. "
         "Neue Vereine legt nur ein Admin an."),
        ("Ein Kollege hört auf – was passiert mit seinen Daten?",
         "Beim Zugang den Haken **„aktiv“** entfernen. Er kann sich dann nicht mehr anmelden, seine Leads, Notizen und Abschlüsse bleiben erhalten."),
        ("Was ist der Inhaber-Notzugang?",
         "Anmeldung **ohne E-Mail**, nur mit dem Inhaber-Passwort aus den Streamlit-Secrets (APP_PASSWORD). Immer Admin – "
         "damit man sich nie aussperren kann. Dieses Passwort nicht weitergeben."),
        ("Warum muss ich mich nach dem Neuladen der Seite neu anmelden?",
         "Aus Sicherheitsgründen gilt die Anmeldung nur für die geöffnete Sitzung. Nach F5 oder einem neuen Tab ist eine neue Anmeldung nötig."),
        ("Wo liegen die Daten?",
         "In einer Datenbank (Supabase). Links unten zeigt „🟢 Datenbank verbunden“, dass alles dauerhaft gespeichert wird."),
        ("Wie mache ich ein Backup?",
         "**Einstellungen → Datenspeicher → Komplett-Backup (JSON)**. Am besten regelmäßig, z. B. einmal pro Woche."),
        ("Arbeiten mehrere Personen gleichzeitig?",
         "Ja, das geht. Bearbeitet ihr gleichzeitig **dasselbe** Unternehmen, gewinnt die zuletzt gespeicherte Änderung."),
    ],
    "🛠️ Probleme lösen": [
        ("„Recherche abgebrochen“ – was jetzt?",
         "Die Meldung nennt den Grund und die letzten Protokollschritte. Bereits gesicherte Unternehmen bleiben erhalten. "
         "Häufig hilft es, die Recherche nach ein paar Minuten erneut zu starten."),
        ("„OSM nicht erreichbar“ bei einzelnen Branchen",
         "Die öffentlichen OpenStreetMap-Server sind zeitweise überlastet. Die übrigen Branchen laufen weiter. "
         "Eine spätere Wiederholung ergänzt die fehlenden Branchen, ohne Doppelte anzulegen."),
        ("Die Seite zeigt alte Daten",
         "Während einer laufenden Recherche auf **„Zwischenstand laden“** klicken. Sonst die Seite im Browser neu laden (F5)."),
        ("Die App zeigt „Oh no“ oder lädt nicht",
         "Seite neu laden. Hilft das nicht, schläft die App vermutlich (nach längerer Nichtnutzung) – auf „Wake up“ klicken und 30 Sekunden warten."),
    ],
    "🧑‍💻 Für Admins": [
        ("Wie spiele ich ein Update ein?",
         "Neue Dateien in GitHub hochladen (**Add file → Upload files**). Die Dateinamen müssen exakt gleich bleiben "
         "(z. B. `recherche_pro.py`, nicht `recherche_pro_neu.py`). Danach auf share.streamlit.io → ⋮ → **Reboot app**."),
        ("Woran erkenne ich, welche Version läuft?",
         "Links unten in der Seitenleiste steht **„Engine: v…“**. Jedes Recherche-Protokoll beginnt ebenfalls mit der Versionszeile."),
        ("Wo ändere ich Inhaber-Passwort, Google-Key oder Datenbank-Zugang?",
         "share.streamlit.io → App → ⋮ → **Settings → Secrets**: `APP_PASSWORD` (Inhaber-Notzugang), `GOOGLE_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, "
         "optional `APP_URL` (Adresse der App für Einladungslinks). Nach dem Speichern startet die App neu."),
        ("Wo passe ich diese Hilfetexte an?",
         "In der Datei `hilfe.py` im GitHub-Projekt. Dort stehen Tour, Seitenhinweise und FAQ als normaler Text."),
    ],
}
