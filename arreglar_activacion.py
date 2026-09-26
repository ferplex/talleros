from pathlib import Path
from bs4 import BeautifulSoup
import shutil, re

app = Path("app/talleros.html")
backup = Path("app/talleros.html.bak")

# Empezar siempre desde el original limpio
if backup.exists():
    shutil.copy2(backup, app)
    print("Restaurado desde backup.")

html = app.read_text(encoding="utf-8", errors="ignore")

if "TALLER·OS · Activación" not in html:
    print("AVISO: ni el archivo actual ni el backup tienen la activación.")
    print("Necesitas el talleros.html original.")
    raise SystemExit(1)

soup = BeautifulSoup(html, "html.parser")

required = ["TALLER·OS · Activación", "ID DE EQUIPO", "Activar"]

def depth(t):
    d = 0
    p = t.parent
    while p:
        d += 1
        p = p.parent
    return d

cands = [
    t for t in soup.find_all(True)
    if t.name not in ("html", "body", "script", "style", "template")
    and all(r in t.get_text(" ", strip=True) for r in required)
]

if not cands:
    print("NO encontré el bloque de activación.")
    raise SystemExit(1)

card = sorted(cands, key=lambda t: (-depth(t), len(t.get_text(" ", strip=True))))[0]

# Subir por los padres mientras el contenedor SOLO tenga texto de activación.
# Así borramos tarjeta + fondo negro juntos.
node = card
p = card.parent
while p and p.name not in ("html", "body"):
    if len(p.get_text(" ", strip=True)) <= 400:
        node = p
        p = p.parent
    else:
        break

info = f"<{node.name} id={node.get('id')} class={node.get('class')}>"
node.decompose()
print("Eliminado contenedor de activación:", info)

# Borrar velos/fondos vacíos que hayan quedado sueltos
pat = re.compile(r"(backdrop|veil|scrim|overlay|fondo|dim|lock|activ|licen)", re.I)
for t in list(soup.find_all(True)):
    if t.name in ("script", "style", "template"):
        continue
    ids = t.get("id") or ""
    cls = " ".join(t.get("class") or [])
    if pat.search(ids + " " + cls) and not t.get_text(strip=True) and not t.find_all(True):
        t.decompose()
        print("Eliminado velo/fondo:", f"<{t.name} id={ids} class={cls}>")

# Quitar clases de bloqueo en body/html (locked, modal-open, etc.)
for tag in (soup.body, soup.html):
    if tag and tag.get("class"):
        nuevas = [c for c in tag["class"] if not pat.search(c)]
        if nuevas:
            tag["class"] = nuevas
        else:
            del tag["class"]

app.write_bytes(soup.encode(encoding="utf-8", formatter=None))
print("Guardado. Ahora prueba: npm start")
