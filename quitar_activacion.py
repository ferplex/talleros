from pathlib import Path
from bs4 import BeautifulSoup
import shutil

app = Path("app/talleros.html")
backup = Path("app/talleros.html.bak")

if not backup.exists():
    shutil.copy2(app, backup)

html = app.read_text(encoding="utf-8", errors="ignore")
soup = BeautifulSoup(html, "html.parser")

required = [
    "TALLER·OS · Activación",
    "ID DE EQUIPO",
    "Activar"
]

def depth(tag):
    d = 0
    parent = tag.parent
    while parent:
        d += 1
        parent = parent.parent
    return d

candidates = []

for tag in soup.find_all(True):
    if tag.name in ("html", "body", "script", "style", "template"):
        continue

    try:
        text = tag.get_text(" ", strip=True)
    except Exception:
        continue

    if all(piece in text for piece in required):
        candidates.append(tag)

removed = False

if candidates:
    # Busca el bloque más específico posible, no todo el body.
    best = sorted(
        candidates,
        key=lambda t: (-depth(t), len(t.get_text(" ", strip=True)))
    )[0]

    best.decompose()
    removed = True
    print("Bloque de activación eliminado.")

else:
    # Búsqueda más suave por si el texto no coincide exactamente.
    for tag in soup.find_all(True):
        if tag.name in ("html", "body", "script", "style", "template"):
            continue

        text = tag.get_text(" ", strip=True)

        if "TALLER·OS · Activación" in text and "ID DE EQUIPO" in text:
            tag.decompose()
            removed = True
            print("Bloque de activación eliminado por búsqueda parcial.")
            break

# Quitar posibles mensajes sueltos de error de activación.
for txt in soup.find_all(string=lambda s: s and "Código incorrecto para este equipo" in s):
    parent = txt.parent

    if parent and parent.name not in ("script", "style", "template"):
        parent_text = parent.get_text(" ", strip=True)

        if len(parent_text) < 200:
            parent.decompose()
            print("Mensaje de código incorrecto eliminado.")

if removed:
    app.write_bytes(soup.encode(encoding="utf-8", formatter=None))
    print("Archivo guardado.")
    print("Ahora prueba con: npm start")
else:
    print("No encontré automáticamente el bloque de activación.")
    print("Necesitamos buscarlo manual.")
