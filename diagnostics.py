"""
Diagnostica automatica calcolata da codice (zero chiamate AI, zero costo,
istantanea).

Non si limita a "l'API risponde": i controlli piu' utili per chi pubblica
sono quelli sul contenuto - da quanti giorni un account e' fermo, se un
canale ha video ma nessuna visualizzazione, se un account non ha ancora
dati. Un problema di token va segnalato, ma un account fermo da due
settimane e' altrettanto importante e nessuna API te lo dice.

Ogni voce ha: severita', categoria, titolo breve, dettaglio, prossimo passo
e - dove ha senso - un'azione che il frontend puo' trasformare in bottone.

I testi viaggiano come `code` + `params` perche' l'interfaccia esiste in sei
lingue: una frase italiana decisa qui resterebbe italiana anche con l'app in
inglese. Le stringhe italiane restano comunque nel payload come fallback,
cosi' una chiave di traduzione mancante degrada nel testo di prima invece
che in un codice grezzo a schermo.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import time
from datetime import datetime, timezone

import config

# Soglie di "contenuto fermo", in giorni.
STALE_WARN_DAYS = 4
STALE_BAD_DAYS = 8


def _days_since(iso_or_unix, is_unix: bool = False) -> float | None:
    if not iso_or_unix:
        return None
    try:
        if is_unix:
            ts = float(iso_or_unix)
        else:
            ts = datetime.fromisoformat(str(iso_or_unix).replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return None
    return (time.time() - ts) / 86400


def _latest_days(items, field, is_unix=False) -> float | None:
    """Giorni trascorsi dalla pubblicazione piu' recente della lista."""
    best = None
    for item in items or []:
        days = _days_since(item.get(field), is_unix)
        if days is not None and (best is None or days < best):
            best = days
    return best


def _has_accounts(platform: str) -> bool:
    """C'e' almeno un account per questa piattaforma, collegato dall'app o
    configurato a mano? Serve a distinguere "non hai ancora dati" da "non
    hai ancora collegato niente": al primo avvio suggerire un Refresh che
    non puo' trovare nulla manderebbe l'utente contro un muro."""
    import os

    env_lists = {"youtube": "YT_CHANNELS", "instagram": "IG_ACCOUNTS", "tiktok": "TT_ACCOUNTS"}
    var = env_lists.get(platform)
    if var and os.environ.get(var, "").strip():
        return True
    try:
        import connections
        return bool(connections.list_connections(platform))
    except Exception:
        return False


GOTO_CONNECTIONS = {"type": "goto", "section": "connections"}


def _no_account_issue(platform: str, label: str) -> dict:
    return _issue(
        "yellow", "Not linked", f"No {label} account",
        f"You haven't linked any {label} account yet.",
        "Press Link and sign in - it only takes a few seconds.",
        platform, GOTO_CONNECTIONS,
        code="diag_no_account", params={"p": label},
    )


def _no_data_issue(platform: str, label: str) -> dict:
    return _issue(
        "yellow", "No data", f"{label} has no data",
        "No data has been loaded yet.", "Press Refresh to load your data.",
        platform, code="diag_no_data", params={"p": label},
    )


def _all_ok_issue(platform: str, label: str, n: int) -> dict:
    return _issue(
        "green", "All good", f"{label}: {n} accounts healthy",
        "Every account responds and posts consistently.",
        "No action needed.", platform,
        code="diag_all_ok", params={"p": label, "n": n},
    )


def _issue(severity, category, title, text, next_step, platform=None, action=None,
           code=None, params=None) -> dict:
    out = {
        "severity": severity, "category": category, "title": title,
        "text": text, "next_step": next_step,
    }
    if platform:
        out["platform"] = platform
    if action:
        out["action"] = action
    if code:
        out["code"] = code
        out["params"] = params or {}
    return out


# Pattern d'errore -> (categoria, prossimo passo, codice per la traduzione).
_ERROR_PATTERNS = [
    (("video.list",), "Permission not granted",
     "The stats-read permission must be approved on the platform's developer portal - it cannot be fixed from the app.",
     "diagerr_scope_denied"),
    (("invalid_grant", "expired", "revoked"), "Access expired",
     "Link this account again: the authorization expired or was revoked.",
     "diagerr_expired"),
    (("invalid_scope",), "Permissions out of sync",
     "The requested permissions don't match the ones originally granted: link the account again to realign them.",
     "diagerr_scope_mismatch"),
    (("permission", "#10", "does not have permission"), "Missing permission",
     "The account didn't grant the required permission: link it again and accept every request.",
     "diagerr_permission"),
    (("quota", "rate limit", "429"), "Too many requests",
     "Wait a few minutes before refreshing again: the platform's rate limit was reached.",
     "diagerr_rate"),
    (("401", "unauthorized", "authentication"), "Invalid credentials",
     "Link the account again to reissue access.",
     "diagerr_auth"),
    (("404", "not found"), "Account not found",
     "The linked account can no longer be reached: it may have been removed or renamed.",
     "diagerr_notfound"),
    (("timeout", "connection", "network"), "Network problem",
     "Try refreshing again: this looks like a temporary connection issue.",
     "diagerr_network"),
]


def _classify_error(err: str) -> tuple[str, str, str]:
    """Riconosce pattern comuni negli errori OAuth/API per dare una categoria
    e un prossimo passo concreto invece di un generico 'errore sconosciuto'."""
    low = (err or "").lower()
    for needles, category, step, code in _ERROR_PATTERNS:
        if any(n in low for n in needles):
            return category, step, code
    return ("Unclassified error", "Try refreshing again; if it persists, link the account again.",
            "diagerr_unknown")


def _unreachable_issue(name: str, error: str, platform: str, action=None) -> dict:
    category, step, code = _classify_error(error)
    return _issue("red", category, f"{name}: not responding", str(error or "")[:220], step,
                  platform, action, code=code, params={"name": name})


def _check_content_freshness(label: str, name: str, days: float | None, platform: str) -> dict | None:
    """Il controllo piu' utile per chi pubblica: da quanto e' fermo."""
    if days is None:
        return None
    d = int(days)
    if days >= STALE_BAD_DAYS:
        return _issue("red", "Posting stalled", f"{name}: nothing for {d} days",
                      f"The latest content on {label} is {d} days old.",
                      "Post something: platforms reward consistency, and reach drops fast on inactive profiles.",
                      platform, code="diag_stale_bad", params={"name": name, "p": label, "d": d})
    if days >= STALE_WARN_DAYS:
        return _issue("yellow", "Slowing down", f"{name}: last post {d} days ago",
                      f"Nothing new on {label} for {d} days.",
                      "Get back to your usual pace before reach starts to slide.",
                      platform, code="diag_stale_warn", params={"name": name, "p": label, "d": d})
    return None


def _check_youtube(data: dict) -> list[dict]:
    if not _has_accounts("youtube"):
        return [_no_account_issue("youtube", "YouTube")]
    if not data:
        return [_no_data_issue("youtube", "YouTube")]
    issues = []
    channels = data.get("channels", [])
    if not channels:
        return [_no_account_issue("youtube", "YouTube")]

    for c in channels:
        if not c.get("ok"):
            issues.append(_unreachable_issue(c.get("name"), c.get("error", ""), "youtube", GOTO_CONNECTIONS))
            continue

        stale = _check_content_freshness("YouTube", c.get("name"), _latest_days(c.get("recent_videos"), "published"), "youtube")
        if stale:
            issues.append(stale)

        if c.get("video_count", 0) > 0 and c.get("recent_views_last10", 0) == 0:
            issues.append(_issue("yellow", "No views", f"{c.get('name')}: 0 views on the latest videos",
                                 "The most recent videos have no views yet.",
                                 "That's normal if they just went up; if they are a few days old, revisit the title, thumbnail and opening seconds.",
                                 "youtube", code="diag_zero_views", params={"name": c.get("name")}))

    if not issues:
        issues.append(_all_ok_issue("youtube", "YouTube", len(channels)))
    return issues


def _check_instagram(data: dict) -> list[dict]:
    if not _has_accounts("instagram"):
        return [_no_account_issue("instagram", "Instagram")]
    if not data:
        return [_no_data_issue("instagram", "Instagram")]
    issues = []
    accounts = data.get("accounts", [])
    if not accounts:
        return [_no_account_issue("instagram", "Instagram")]

    for a in accounts:
        if not a.get("ok"):
            issues.append(_unreachable_issue(a.get("name"), a.get("error", ""), "instagram", GOTO_CONNECTIONS))
            continue

        stale = _check_content_freshness("Instagram", a.get("name"), _latest_days(a.get("recent_posts"), "timestamp"), "instagram")
        if stale:
            issues.append(stale)

    if not issues:
        issues.append(_all_ok_issue("instagram", "Instagram", len(accounts)))
    return issues


def _check_tiktok(data: dict) -> list[dict]:
    if not _has_accounts("tiktok"):
        return [_no_account_issue("tiktok", "TikTok")]
    if not data:
        return [_no_data_issue("tiktok", "TikTok")]
    issues = []
    accounts = data.get("accounts", [])
    if not accounts:
        return [_no_account_issue("tiktok", "TikTok")]

    for a in accounts:
        if a.get("not_configured"):
            issues.append(_issue("yellow", "Needs setup", f"{a.get('name')}: not configured",
                                 "The account is listed but has no credentials attached.",
                                 "Link the account, or remove it from the list if you don't need it.",
                                 "tiktok", GOTO_CONNECTIONS,
                                 code="diag_not_configured", params={"name": a.get("name")}))
            continue
        if not a.get("ok"):
            issues.append(_unreachable_issue(a.get("name"), a.get("error", ""), "tiktok"))
            continue

        stale = _check_content_freshness("TikTok", a.get("name"), _latest_days(a.get("recent_videos"), "create_time", is_unix=True), "tiktok")
        if stale:
            issues.append(stale)

    if not issues:
        issues.append(_all_ok_issue("tiktok", "TikTok", len(accounts)))
    return issues


def _check_x(data: dict) -> list[dict]:
    if not data:
        return [_no_data_issue("x", "X")]
    if not data.get("credentials_configured"):
        return [_issue("yellow", "Not linked", "X not linked",
                       "No X credentials configured.",
                       "X doesn't expose read analytics on the free plan, so this section stays informational for now.",
                       "x", code="diag_x_not_linked", params={})]
    return [_issue("green", "Linked", "X linked",
                   "Credentials are in place. Read analytics aren't available on X's free plan.",
                   "No action needed.", "x", code="diag_x_linked", params={})]


def _check_certsprint(data: dict) -> list[dict]:
    # Personal module: config.enabled_platforms excludes it from customer builds.
    if not data:
        return [_no_data_issue("certsprint", "CertSprint")]
    issues = []
    uptime = data.get("uptime", {})
    if not uptime.get("up"):
        issues.append(_issue("red", "Website unavailable", "CertSprint offline",
                             f"The website is not responding ({uptime.get('error', 'unknown error')}).",
                             "Confirm the deployment is active and the configured URL is correct.", "certsprint"))
    elif uptime.get("latency_ms", 0) > 2000:
        issues.append(_issue("yellow", "Performance", "CertSprint is slow",
                             f"The website responded in {uptime['latency_ms']}ms.",
                             "Check the hosting logs for a cold start or elevated load.", "certsprint"))

    vulns = data.get("npm_audit", {}).get("vulnerabilities", {})
    if vulns.get("critical") or vulns.get("high"):
        issues.append(_issue("red", "Dependency security", "Vulnerabilities require attention",
                             f"npm audit found {vulns.get('critical', 0)} critical and {vulns.get('high', 0)} high vulnerabilities.",
                             "Run 'npm audit fix', review breaking changes, and audit the repository again.", "certsprint"))
    elif vulns.get("moderate"):
        issues.append(_issue("yellow", "Dependency security", "Moderate vulnerabilities",
                             f"npm audit found {vulns['moderate']} moderate vulnerabilities.",
                             "Schedule an 'npm audit fix' after reviewing the proposed changes.", "certsprint"))

    lint = data.get("eslint", {})
    if lint.get("configured") and lint.get("errors"):
        issues.append(_issue("yellow", "Code quality", f"{lint['errors']} ESLint errors",
                             "The linter found errors in the repository.",
                             "Run 'npx eslint . --fix' and review any remaining errors manually.", "certsprint"))

    if not issues:
        issues.append(_issue("green", "All clear", "CertSprint is healthy",
                             "The website is online, no relevant vulnerabilities were found, and the code is clean.", "No action required.", "certsprint"))
    return issues


CHECKS = {
    "youtube": _check_youtube,
    "instagram": _check_instagram,
    "tiktok": _check_tiktok,
    "x": _check_x,
    "certsprint": _check_certsprint,
}


# ----------------------------------------------------------- strategia
#
# I controlli qui sotto non guardano se le API rispondono, ma se quello che
# pubblichi sta funzionando. Sono trasversali alle piattaforme e usano
# l'analisi gia' calcolata (analytics.py), quindi non costano nessuna
# chiamata in piu'.
#
# Regola che vale per tutti: meglio tacere che dire qualcosa costruito su
# due contenuti. Ogni controllo ha una soglia minima di dati sotto la quale
# semplicemente non si esprime.

_NOMI_PIATTAFORMA = {"youtube": "YouTube", "instagram": "Instagram", "tiktok": "TikTok"}

# Sotto questi contenuti un rapporto non descrive un andamento, descrive un
# caso singolo.
MIN_CONTENUTI_ENGAGEMENT = 4
MIN_CONTENUTI_RISONANZA = 5

# Un contenuto visto molto ma mai salvato ne' condiviso e' stato consumato,
# non apprezzato. La soglia e' volutamente bassa: bastano poche condivisioni
# per uscirne, quindi finirci dentro significa davvero zero risonanza.
SOGLIA_RISONANZA = 0.15  # % su reach, salvataggi + condivisioni

# Quanto una piattaforma puo' restare indietro rispetto alla migliore prima
# che valga la pena dirlo. Sotto questo rapporto non e' uno squilibrio, e'
# normale che un canale renda piu' di un altro.
SQUILIBRIO = 0.15


def _check_benchmark(analisi: dict) -> list[dict]:
    """Il tuo engagement rispetto a chi ha un pubblico della tua taglia."""
    fuori = []
    for confronto in analisi.get("benchmarks", []):
        piattaforma = confronto["platform"]
        nome = _NOMI_PIATTAFORMA.get(piattaforma, piattaforma)
        parametri = {"p": nome, "r": confronto["rate"], "e": confronto["expected"]}

        if confronto["state"] == "below":
            fuori.append(_issue(
                "yellow", "Engagement under benchmark",
                f"{nome}: engagement below average for your size",
                f"Your engagement on {nome} is {confronto['rate']}% against an average of "
                f"{confronto['expected']}% for accounts with a similar following.",
                "Look at which of your own posts got the most saves and shares, and do more of those: "
                "reach follows engagement, not the other way around.",
                piattaforma, code="diag_bench_below", params=parametri))
        elif confronto["state"] == "above":
            fuori.append(_issue(
                "green", "Engagement above benchmark",
                f"{nome}: engagement above average",
                f"Your engagement on {nome} is {confronto['rate']}%, above the "
                f"{confronto['expected']}% average for accounts of your size.",
                "Keep the format that is working: this is the audience responding, not the algorithm.",
                piattaforma, code="diag_bench_above", params=parametri))
    return fuori


def _check_risonanza(analisi: dict) -> list[dict]:
    """Views senza salvataggi ne' condivisioni: guardato e dimenticato."""
    fuori = []
    for piattaforma, misura in (analisi.get("engagement_per_platform") or {}).items():
        # YouTube non espone salvataggi ne' condivisioni con lo scope di
        # lettura: li' un valore a zero non vuol dire niente e accusare il
        # cliente di scarsa risonanza sarebbe un errore nostro, non suo.
        if piattaforma == "youtube":
            continue
        if misura.get("items", 0) < MIN_CONTENUTI_RISONANZA:
            continue
        risonanza = (misura.get("save_rate", 0) or 0) + (misura.get("share_rate", 0) or 0)
        if risonanza < SOGLIA_RISONANZA and misura.get("reach", 0) > 0:
            nome = _NOMI_PIATTAFORMA.get(piattaforma, piattaforma)
            fuori.append(_issue(
                "yellow", "Low resonance",
                f"{nome}: seen but not saved or shared",
                f"Across your last {misura['items']} posts on {nome}, saves and shares add up to "
                f"{round(risonanza, 2)}% of the accounts you reached.",
                "Views alone don't compound. Content people save or send to someone else is what the "
                "platform pushes further - try something useful enough to keep, or worth passing on.",
                piattaforma, code="diag_resonance",
                params={"p": nome, "n": misura["items"], "r": round(risonanza, 2)}))
    return fuori


def _check_squilibrio(analisi: dict) -> list[dict]:
    """Una piattaforma ferma mentre le altre girano."""
    per_piattaforma = analisi.get("per_platform") or {}
    attive = {p: d for p, d in per_piattaforma.items()
              if p in _NOMI_PIATTAFORMA and d.get("count", 0) > 0}
    if len(attive) < 2:
        return []

    medie = {p: d["views"] / d["count"] for p, d in attive.items()}
    migliore = max(medie, key=medie.get)
    if medie[migliore] <= 0:
        return []

    fuori = []
    for piattaforma, media in medie.items():
        if piattaforma == migliore or media / medie[migliore] >= SQUILIBRIO:
            continue
        nome = _NOMI_PIATTAFORMA.get(piattaforma, piattaforma)
        nome_migliore = _NOMI_PIATTAFORMA.get(migliore, migliore)
        fuori.append(_issue(
            "yellow", "Platform lagging",
            f"{nome} is far behind {nome_migliore}",
            f"Your posts average {round(media)} views on {nome} against {round(medie[migliore])} on "
            f"{nome_migliore}.",
            f"Either adapt what already works on {nome_migliore} to {nome}'s format, or stop spreading "
            f"yourself thin and put that time where it already pays.",
            piattaforma, code="diag_imbalance",
            params={"p": nome, "b": nome_migliore, "v": round(media), "bv": round(medie[migliore])}))
    return fuori


def _check_orario(analisi: dict) -> list[dict]:
    """Hai una fascia oraria che rende, ma continui a pubblicare altrove."""
    migliori = analisi.get("best_hours") or []
    if len(migliori) < 2:
        return []

    migliore, peggiore = migliori[0], migliori[-1]
    # Se la fascia migliore rende almeno il doppio della peggiore fra quelle
    # affidabili, la differenza non e' rumore.
    if peggiore["avg_views"] <= 0 or migliore["avg_views"] < peggiore["avg_views"] * 2:
        return []

    return [_issue(
        "yellow", "Timing", f"Your {migliore['hour']:02d}:00 slot performs best",
        f"Posts published around {migliore['hour']:02d}:00 UTC average {migliore['avg_views']} views, "
        f"against {peggiore['avg_views']} around {peggiore['hour']:02d}:00.",
        f"Move your next posts closer to {migliore['hour']:02d}:00 and see whether the gap holds.",
        None, code="diag_timing",
        params={"h": f"{migliore['hour']:02d}", "v": migliore["avg_views"],
                "lh": f"{peggiore['hour']:02d}", "lv": peggiore["avg_views"]})]


def _check_strategia(analisi: dict) -> list[dict]:
    """Tutti i controlli che guardano i risultati invece degli errori."""
    if not analisi:
        return []
    fuori = []
    for controllo in (_check_benchmark, _check_risonanza, _check_squilibrio, _check_orario):
        try:
            fuori.extend(controllo(analisi))
        except Exception:
            # Un controllo che sbaglia i conti non deve far sparire tutta la
            # diagnostica: si perde quel controllo, non la pagina.
            import logging
            logging.warning("diagnostic check failed: %s",
                            controllo.__name__, exc_info=True)
    return fuori


# Quanto pesa ogni parte del punteggio. La somma fa 1.
#
# Perche' l'engagement pesa piu' di tutto: e' l'unica voce che dice se
# quello che pubblichi interessa a qualcuno. Le altre tre dicono se la
# macchina gira, non se sta andando da qualche parte.
PESI = {"technical": 0.25, "engagement": 0.30, "consistency": 0.25, "coverage": 0.20}

# Giorni oltre i quali la costanza va a zero. Tarato sulle stesse soglie
# usate dal controllo "da quanto non pubblichi", per non dare due giudizi
# diversi sullo stesso fatto.
GIORNI_COSTANZA_PIENA = 3
GIORNI_COSTANZA_ZERO = 30


def _voce(valore: float | None, peso: float, etichetta: str, dettaglio: str) -> dict:
    return {"key": etichetta, "score": None if valore is None else round(valore),
            "weight": peso, "detail": dettaglio}


def _punteggio_salute(issues: list[dict], analisi: dict, snapshot: dict) -> dict:
    """Un punteggio che dice come stanno andando i social, non quanti
    controlli sono passati.

    Il precedente era la percentuale di controlli verdi: senza errori tecnici
    faceva 100% anche con zero crescita e zero engagement, cioe' dava il
    massimo dei voti a un account fermo purche' le API rispondessero. Questo
    invece pesa quattro cose diverse e mostra da dove esce il numero, cosi'
    chi lo legge sa cosa migliorare.

    Ogni voce puo' valere None quando non ci sono abbastanza dati per
    giudicarla: in quel caso esce dal calcolo e il peso si ridistribuisce,
    invece di far finta che sia uno zero (che sarebbe una bocciatura data
    per mancanza di informazioni, non per un risultato).
    """
    voci = []

    # 1. Tecnica: gli account rispondono?
    rossi = sum(1 for i in issues if i["severity"] == "red")
    totale_controlli = len(issues) or 1
    tecnica = max(0.0, 100.0 - (rossi / totale_controlli) * 100 * 2)
    voci.append(_voce(tecnica, PESI["technical"], "technical",
                      f"{rossi} problem(s) blocking data collection"))

    # 2. Engagement rispetto alla propria fascia.
    confronti = (analisi or {}).get("benchmarks") or []
    if confronti:
        # 100 = in linea con la media di settore, 200 = doppio della media.
        rapporti = [min(2.0, c["rate"] / c["expected"]) for c in confronti if c.get("expected")]
        engagement = (sum(rapporti) / len(rapporti)) * 50 if rapporti else None
        dettaglio = f"compared against {len(confronti)} platform benchmark(s)"
    else:
        engagement, dettaglio = None, "not enough follower data to compare"
    voci.append(_voce(engagement, PESI["engagement"], "engagement", dettaglio))

    # 3. Costanza: da quanto non pubblichi.
    giorni = _giorni_dall_ultimo_contenuto(snapshot)
    if giorni is None:
        costanza, dettaglio = None, "no dated content yet"
    else:
        if giorni <= GIORNI_COSTANZA_PIENA:
            costanza = 100.0
        elif giorni >= GIORNI_COSTANZA_ZERO:
            costanza = 0.0
        else:
            arco = GIORNI_COSTANZA_ZERO - GIORNI_COSTANZA_PIENA
            costanza = 100.0 * (1 - (giorni - GIORNI_COSTANZA_PIENA) / arco)
        dettaglio = f"last post {int(giorni)} day(s) ago"
    voci.append(_voce(costanza, PESI["consistency"], "consistency", dettaglio))

    # 4. Copertura: quante piattaforme stai davvero usando.
    attive = sum(1 for p, d in ((analisi or {}).get("per_platform") or {}).items()
                 if p in _NOMI_PIATTAFORMA and d.get("count", 0) > 0)
    possibili = len([p for p in config.enabled_platforms() if p in _NOMI_PIATTAFORMA]) or 1
    copertura = min(100.0, attive / possibili * 100)
    voci.append(_voce(copertura, PESI["coverage"], "coverage",
                      f"{attive} of {possibili} platform(s) with recent content"))

    valide = [v for v in voci if v["score"] is not None]
    if not valide:
        return {"score": None, "parts": voci}

    peso_totale = sum(v["weight"] for v in valide)
    punteggio = sum(v["score"] * v["weight"] for v in valide) / peso_totale
    return {"score": round(punteggio), "parts": voci}


def _giorni_dall_ultimo_contenuto(snapshot: dict) -> float | None:
    """Da quanti giorni non pubblichi, su nessuna piattaforma.

    Si prende il piu' recente fra tutte: chi pubblica su TikTok ogni giorno
    e su YouTube ogni due mesi non e' fermo, e dirgli il contrario perche'
    un canale e' piu' lento sarebbe sbagliato.
    """
    giorni = []

    for canale in (snapshot.get("youtube") or {}).get("channels", []):
        if canale.get("ok"):
            giorni.append(_latest_days(canale.get("recent_videos"), "published"))

    for conto in (snapshot.get("instagram") or {}).get("accounts", []):
        if conto.get("ok"):
            giorni.append(_latest_days(conto.get("recent_posts"), "timestamp"))

    for conto in (snapshot.get("tiktok") or {}).get("accounts", []):
        if conto.get("ok"):
            giorni.append(_latest_days(conto.get("recent_videos"), "create_time", is_unix=True))

    disponibili = [g for g in giorni if g is not None]
    return min(disponibili) if disponibili else None


def run_diagnostics(snapshot: dict, analytics_data: dict | None = None) -> dict:
    all_issues = []
    for platform in config.enabled_platforms():
        check_fn = CHECKS.get(platform)
        if not check_fn:
            continue
        for issue in check_fn(snapshot.get(platform)):
            all_issues.append({"platform": platform, **issue})

    # Controlli di strategia: guardano i risultati, non gli errori. Arrivano
    # dopo perche' usano l'analisi gia' calcolata sugli stessi dati.
    all_issues.extend(_check_strategia(analytics_data or {}))

    order = {"red": 0, "yellow": 1, "green": 2}
    all_issues.sort(key=lambda i: order.get(i["severity"], 3))

    counts = {"red": 0, "yellow": 0, "green": 0}
    for i in all_issues:
        counts[i["severity"]] = counts.get(i["severity"], 0) + 1

    salute = _punteggio_salute(all_issues, analytics_data or {}, snapshot)

    return {"issues": all_issues, "counts": counts,
            "score": salute["score"], "score_parts": salute["parts"]}
