"""
I colori dei temi, tenuti allineati fra CSS e JavaScript.

Due controlli che nessuno puo' fare a occhio:

  1. Ogni tema e' definito due volte. In `style.css` come variabili, che sono
     quelle che disegnano davvero l'interfaccia, e in `app.js` come terna di
     colori per il pallino di anteprima del selettore temi. L'anteprima deve
     restare letterale: mostra i colori di un tema mentre ne e' attivo un
     altro, quindi non puo' leggere le variabili. Il prezzo e' che le due
     copie possono divergere in silenzio, ed era gia' successo: il tema
     "dark" era stato scurito nel CSS (#09090b) e il pallino era rimasto al
     grigio vecchio (#0f1115). Nessuno se ne accorge, perche' un pallino
     leggermente sbagliato sembra semplicemente un pallino.

  2. Il badge di notifica scrive sopra `--red`. In tutti i temi tranne
     "light" il rosso e' chiaro, e il bianco ci finiva a 2.55:1 su un testo
     bold da 10px: leggibile per chi ha una vista buona su un buon monitor, e
     non per tutti gli altri. Il contrasto e' aritmetica, quindi conviene
     misurarlo qui invece di fidarsi dello screenshot in cui sembrava ok.
"""
import re
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parent.parent / "static"
CSS = (STATIC / "style.css").read_text(encoding="utf-8")
JS = (STATIC / "app.js").read_text(encoding="utf-8")

# Soglia WCAG 2.1 AA per il testo normale. Il badge e' bold ma da 10px, sotto
# i 18.66px che farebbero scattare la soglia piu' bassa da 3:1.
AA_TESTO_NORMALE = 4.5


def _varianti_tema():
    """Le variabili di ogni tema, lette dai blocchi :root[data-theme=...]."""
    temi = {}
    for blocco in re.finditer(r':root\[data-theme="([a-z]+)"\]\s*\{(.*?)\}', CSS, re.S):
        nome, corpo = blocco.group(1), blocco.group(2)
        temi[nome] = {
            k: v.strip()
            for k, v in re.findall(r"--([a-z0-9-]+):\s*([^;]+);", corpo)
        }
    return temi


def _anteprime():
    """Le terne [bg, accent, card] dichiarate in THEMES dentro app.js."""
    return {
        m.group(1): [c.lower() for c in re.findall(r'"(#[0-9a-fA-F]{3,8})"', m.group(2))]
        for m in re.finditer(
            r'\{ id: "([a-z]+)", name: "[^"]+", colors: (\[[^\]]+\]) \}', JS
        )
    }


def _luminanza(hex_colore):
    h = hex_colore.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    canali = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        canali.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = canali
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrasto(a, b):
    la, lb = _luminanza(a), _luminanza(b)
    chiaro, scuro = max(la, lb), min(la, lb)
    return (chiaro + 0.05) / (scuro + 0.05)


TEMI = _varianti_tema()
ANTEPRIME = _anteprime()


def test_i_due_elenchi_coprono_gli_stessi_temi():
    """Un tema aggiunto solo da una parte non comparirebbe nel selettore, o
    comparirebbe senza colori: entrambi i casi passano inosservati finche'
    qualcuno non apre quella schermata."""
    assert set(TEMI) == set(ANTEPRIME), (
        f"solo nel CSS: {sorted(set(TEMI) - set(ANTEPRIME))}, "
        f"solo nel JS: {sorted(set(ANTEPRIME) - set(TEMI))}"
    )


@pytest.mark.parametrize("tema", sorted(ANTEPRIME))
def test_anteprima_uguale_alle_variabili(tema):
    """Il pallino deve mostrare i colori che il tema applica davvero."""
    bg, accent, card = ANTEPRIME[tema]
    atteso = TEMI[tema]
    assert bg == atteso["bg"].lower(), f"{tema}: anteprima {bg}, --bg {atteso['bg']}"
    assert accent == atteso["accent"].lower(), f"{tema}: anteprima {accent}, --accent {atteso['accent']}"
    assert card == atteso["card"].lower(), f"{tema}: anteprima {card}, --card {atteso['card']}"


def _regola_badge():
    """I due token che .nav-badge usa davvero, letti dalla regola.

    Fissarli qui a mano renderebbe il test cieco proprio al cambio che deve
    sorvegliare: se qualcuno riscrive `color`, il controllo continuerebbe a
    misurare la coppia vecchia e a passare."""
    regola = re.search(r"\.nav-badge\s*\{(.*?)\}", CSS, re.S)
    assert regola, "regola .nav-badge non trovata: il test non sa piu' cosa misurare"
    corpo = regola.group(1)
    sfondo = re.search(r"background:\s*var\(--([a-z0-9-]+)\)", corpo)
    testo = re.search(r"(?<!-)color:\s*var\(--([a-z0-9-]+)\)", corpo)
    assert sfondo and testo, (
        "background e color di .nav-badge devono essere token: "
        "un valore fisso non segue i dodici temi"
    )
    return testo.group(1), sfondo.group(1)


@pytest.mark.parametrize("tema", sorted(TEMI))
def test_badge_di_notifica_leggibile(tema):
    """Il badge scrive su uno sfondo che cambia con il tema."""
    token_testo, token_sfondo = _regola_badge()
    rapporto = _contrasto(TEMI[tema][token_testo], TEMI[tema][token_sfondo])
    assert rapporto >= AA_TESTO_NORMALE, (
        f"{tema}: {rapporto:.2f}:1 fra --{token_testo} e --{token_sfondo}, "
        f"sotto {AA_TESTO_NORMALE}:1"
    )


def test_nessun_colore_scritto_a_mano_fuori_dai_temi():
    """I colori vivono nei blocchi :root. Uno scritto altrove non segue il
    tema e diventa il punto in cui la palette si spacca: e' cosi' che il
    badge si era ritrovato un #fff fisso addosso a undici sfondi diversi."""
    blocchi = [
        (m.start(), m.end())
        for m in re.finditer(r":root[^{]*\{[^}]*\}", CSS, re.S)
    ]
    fuori = [
        (CSS[: m.start()].count("\n") + 1, m.group(0))
        for m in re.finditer(r"#[0-9a-fA-F]{3,8}\b", CSS)
        if not any(a <= m.start() < b for a, b in blocchi)
    ]
    assert not fuori, f"colori fuori dai blocchi :root: {fuori}"
