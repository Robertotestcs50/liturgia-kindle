"""Valida los EPUB con EPUBCheck (el validador oficial del W3C)."""
import sys

from epubcheck import EpubCheck

ok = True
for ruta in sys.argv[1:]:
    r = EpubCheck(ruta)
    errores = [m for m in r.messages if m.level in ("FATAL", "ERROR")]
    avisos = [m for m in r.messages if m.level == "WARNING"]
    print(f"{ruta}: {'válido' if r.valid else 'NO válido'} "
          f"({len(errores)} errores, {len(avisos)} avisos)")
    for m in errores + avisos:
        print(f"  {m.level} {m.id} {m.location}: {m.message}")
    ok = ok and r.valid
sys.exit(0 if ok else 1)
