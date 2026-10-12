"""
Benutzer & Rechte für das RFN Sponsoring Cockpit.

Rollen
  admin       – sieht und darf alles (Chef)
  vertriebler – sieht nur die ihm zugeordneten Vereine; beim Geld nur Sponsoringwert und eigene Provision

Passwörter werden ausschließlich als PBKDF2-SHA256-Fingerabdruck gespeichert (nie im Klartext).
Einladung: Der Admin erzeugt einen Einladungslink; damit legt der Kollege sein eigenes Passwort fest.
"""
import hashlib, hmac, secrets, time, uuid

ITER = 200_000
INVITE_DAYS = 7
OWNER_ID = "inhaber"


def hash_pw(pw: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), bytes.fromhex(salt), ITER).hex()
    return f"pbkdf2${ITER}${salt}${h}"


def check_pw(pw: str, stored: str) -> bool:
    try:
        _, it, salt, h = stored.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), bytes.fromhex(salt), int(it)).hex()
        return hmac.compare_digest(calc, h)
    except Exception:
        return False


def pw_problem(pw: str) -> str:
    """Leerer Text = Passwort in Ordnung, sonst Hinweis."""
    if len(pw) < 10:
        return "Mindestens 10 Zeichen."
    if pw.lower() == pw or pw.upper() == pw or not any(ch.isdigit() for ch in pw):
        return "Bitte Groß- und Kleinbuchstaben sowie mindestens eine Ziffer verwenden."
    return ""


def new_user(name, email, role="vertriebler", club_ids=None, may_research=False, may_google=False):
    return {"id": uuid.uuid4().hex[:10], "name": name.strip(), "email": email.strip().lower(), "role": role,
            "clubs": list(club_ids or []), "may_research": bool(may_research), "may_google": bool(may_google),
            "active": True, "pw": "", "invite": None, "created": time.strftime("%Y-%m-%d"), "last_login": ""}


def make_invite(user):
    token = secrets.token_urlsafe(24)
    user["invite"] = {"token": token, "expires": time.time() + INVITE_DAYS * 86400}
    return token


def find_by_invite(users, token):
    for u in users:
        inv = u.get("invite") or {}
        if token and hmac.compare_digest(str(inv.get("token", "")), str(token)):
            return u if inv.get("expires", 0) > time.time() and u.get("active", True) else None
    return None


def find_by_email(users, email):
    e = (email or "").strip().lower()
    return next((u for u in users if u.get("email") == e), None)


def owner_user():
    """Notzugang über APP_PASSWORD – immer Admin."""
    return {"id": OWNER_ID, "name": "Inhaber", "email": "", "role": "admin", "clubs": [], "may_research": True,
            "may_google": True, "active": True}


def is_admin(u):
    return bool(u) and u.get("role") == "admin"
