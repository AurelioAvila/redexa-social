"""
Copyright (c) 2026 Aurelio Avila. All rights reserved.

Valori medi di engagement per piattaforma e dimensione dell'account.

A cosa serve: "engagement 3,2%" da solo non dice niente. Dice qualcosa
solo confrontato con quello che fa chi ha un pubblico simile sulla stessa
piattaforma - un 3% su TikTok e' sotto la media, lo stesso 3% su Instagram
e' sopra.

Perche' sta in una tabella dentro l'app e non dietro una chiamata di rete:
sono dati pubblici di settore che cambiano una volta l'anno, non a ogni
apertura dell'app. Tenerli qui significa zero chiamate, zero costo, zero
dati dell'utente che escono dal suo computer, e nessun servizio esterno da
mantenere vivo. Si aggiornano con una release, come tutto il resto.

L'engagement rate qui e' inteso sui follower (interazioni / follower), che
e' la definizione usata da tutti i report di settore. E' diversa da quella
sulla reach (interazioni / persone raggiunte) che l'app calcola in
analytics.py: la prima dice "quanto e' attivo il tuo pubblico", la seconda
"quanto convince chi lo vede". Confrontare l'una con i valori dell'altra
darebbe numeri senza senso, quindi le due non si mescolano mai.

Fonte dei valori: report pubblici di benchmark 2026 (Socialinsider,
Influencer Marketing Factory, Improvado). Sono ordini di grandezza, non
misure esatte: l'app li presenta come riferimento, mai come voto.
"""

# Soglie delle fasce, in follower. La regola che vale su tutte le
# piattaforme e' che l'engagement CALA al crescere del pubblico: un account
# da mille persone parla a una comunita', uno da un milione a un pubblico.
# Confrontare un piccolo account con la media generale lo farebbe sembrare
# bravissimo, e uno grande un disastro, per il solo effetto della taglia.
TIERS = (
    (10_000, "nano"),
    (100_000, "micro"),
    (500_000, "mid"),
    (1_000_000, "macro"),
    (float("inf"), "mega"),
)

# piattaforma -> fascia -> engagement medio atteso (% sui follower).
BENCHMARKS = {
    "tiktok": {"nano": 9.0, "micro": 5.0, "mid": 3.8, "macro": 3.2, "mega": 2.8},
    "instagram": {"nano": 4.0, "micro": 2.5, "mid": 1.6, "macro": 1.3, "mega": 1.1},
    "youtube": {"nano": 3.5, "micro": 2.0, "mid": 1.5, "macro": 1.2, "mega": 1.0},
}

# Sotto questo numero di follower il rapporto e' troppo ballerino: un solo
# contenuto andato bene manda l'engagement al 40% e il confronto con la
# media di settore diventa una barzelletta invece di un'indicazione.
MIN_FOLLOWERS = 300

# Quanto ci si puo' discostare dalla media restando "in linea". Sotto questa
# banda non ha senso dire a qualcuno che sta andando male: la variabilita'
# normale fra un mese e l'altro e' piu' ampia di cosi'.
BANDA = 0.25


def tier_for(followers: int) -> str:
    for soglia, nome in TIERS:
        if followers < soglia:
            return nome
    return "mega"


def expected_rate(platform: str, followers: int) -> float | None:
    """Engagement medio atteso per un account di questa taglia."""
    per_piattaforma = BENCHMARKS.get(platform)
    if not per_piattaforma or not followers:
        return None
    return per_piattaforma.get(tier_for(followers))


def compare(platform: str, followers: int, follower_rate: float | None) -> dict | None:
    """Confronta l'engagement dell'utente con la media della sua fascia.

    Restituisce None quando il confronto non reggerebbe (piattaforma senza
    dati di riferimento, follower non disponibili o troppo pochi): meglio
    non dire niente che dare un giudizio costruito sul nulla.
    """
    if follower_rate is None or not followers or followers < MIN_FOLLOWERS:
        return None
    # inf e NaN sopravvivono a float() e passano indenni da json.loads, che
    # accetta Infinity e NaN: arrivati fin qui farebbero esplodere round()
    # con un OverflowError e porterebbero giu' tutta la pagina.
    if follower_rate != follower_rate or follower_rate in (float("inf"), float("-inf")):
        return None
    atteso = expected_rate(platform, followers)
    if not atteso:
        return None

    scarto = (follower_rate - atteso) / atteso
    if scarto > BANDA:
        stato = "above"
    elif scarto < -BANDA:
        stato = "below"
    else:
        stato = "inline"

    return {
        "platform": platform,
        "tier": tier_for(followers),
        "followers": followers,
        "rate": round(follower_rate, 2),
        "expected": atteso,
        "state": stato,
        "delta_pct": round(scarto * 100),
    }
