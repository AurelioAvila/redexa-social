"""
Analisi della singola piattaforma, calcolata dal codice sui dati gia'
scaricati.

Prima questa funzione chiamava un modello a pagamento: ogni clic su
"Analizza" costava, richiedeva una chiave API, impiegava secondi e - quando
il credito finiva - mostrava al cliente l'errore grezzo del fornitore
("credit balance is too low..."). Per un prodotto venduto e' inaccettabile
su tre fronti: costo variabile, dipendenza esterna e messaggi che parlano
di servizi che il cliente non ha comprato.

Le stesse domande utili si rispondono con i dati che l'app ha gia' in casa:
qual e' il contenuto migliore, quali sono sotto la media, con che ritmo si
pubblica, quanto engagement genera una view. Istantaneo, gratuito, senza
rete e identico ad ogni esecuzione.

Come per la diagnostica il testo viaggia come `code` + `params`, cosi'
segue la lingua scelta nell'interfaccia; la frase italiana resta come
fallback.
"""
import time
from datetime import datetime

# Sotto queste soglie un'osservazione sarebbe rumore, non un'informazione:
# con due post qualsiasi "media" e "migliore" coincidono e non dicono nulla.
MIN_ITEMS_FOR_COMPARISON = 4
FLOP_RATIO = 0.4          # sotto il 40% della media = sotto-performante
STAR_RATIO = 1.5          # sopra il 150% della media = da replicare

# Con sei account collegati un'osservazione per metrica per account fa venti
# righe: nessuno le legge, e il valore di un riquadro di sintesi e' proprio
# non doverle leggere tutte. Si tengono le poche che contano davvero.
MAX_PER_ENTITY = 2
MAX_TOTAL = 6
KIND_PRIORITY = {"warn": 0, "good": 1, "info": 2}


def _to_unix(value, is_unix: bool = False) -> float | None:
    if not value:
        return None
    try:
        if is_unix:
            return float(value)
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return None


def _entities(platform: str, data: dict) -> list[dict]:
    """Canali/account della piattaforma, normalizzati in una forma comune
    cosi' il resto del modulo non deve sapere da chi arrivano i dati."""
    if not data:
        return []
    if platform == "youtube":
        raw, items_key, ts_field, is_unix = data.get("channels", []), "recent_videos", "published", False
    elif platform == "instagram":
        raw, items_key, ts_field, is_unix = data.get("accounts", []), "recent_posts", "timestamp", False
    elif platform == "tiktok":
        raw, items_key, ts_field, is_unix = data.get("accounts", []), "recent_videos", "create_time", True
    else:
        return []

    out = []
    for e in raw:
        if not e.get("ok"):
            continue
        items = []
        for it in e.get(items_key, []) or []:
            ts = _to_unix(it.get(ts_field), is_unix)
            hour = it.get("publish_hour_utc")
            if hour is None and ts is not None:
                hour = datetime.utcfromtimestamp(ts).hour
            items.append({
                "title": (it.get("title") or it.get("caption") or "").strip(),
                "views": it.get("views", 0) or 0,
                "likes": it.get("likes", 0) or 0,
                "comments": it.get("comments", 0) or 0,
                "shares": it.get("shares", 0) or 0,
                "ts": ts,
                "hour": hour,
            })
        out.append({"name": e.get("name", ""), "items": items, "raw": e})
    return out


def _insight(kind: str, code: str, text: str, **params) -> dict:
    return {"kind": kind, "code": code, "text": text, "params": params}


def _short(title: str, n: int = 60) -> str:
    title = (title or "").replace("\n", " ").strip()
    if not title:
        return "(untitled)"
    return title if len(title) <= n else title[: n - 1] + "…"


def _analyze_entity(name: str, items: list[dict]) -> list[dict]:
    out = []
    with_views = [i for i in items if i["views"] > 0]

    if not items:
        return [_insight("info", "ins_no_items", f"{name}: no recent content to analyze.", name=name)]

    # Contenuti a zero: utile saperlo prima di leggere qualsiasi media.
    zeros = len(items) - len(with_views)
    if zeros and zeros == len(items):
        return [_insight("warn", "ins_all_zero",
                         f"{name}: none of the last {len(items)} posts have any views yet.",
                         name=name, n=len(items))]
    if zeros:
        # `n` e' il conteggio che decide singolare/plurale nella traduzione,
        # quindi deve essere quello che varia (i contenuti a zero), non il
        # totale: altrimenti si leggeva "1 contenuti".
        out.append(_insight("warn", "ins_some_zero",
                            f"{name}: {zeros} of the last {len(items)} posts still have zero views.",
                            name=name, n=zeros, tot=len(items)))

    avg = sum(i["views"] for i in with_views) / len(with_views)

    # Migliore e peggiore hanno senso solo con abbastanza contenuti alle
    # spalle: con due post "il migliore" e' un'ovvieta', non un'analisi.
    if len(with_views) >= MIN_ITEMS_FOR_COMPARISON:
        best = max(with_views, key=lambda i: i["views"])
        if best["views"] >= avg * STAR_RATIO:
            out.append(_insight("good", "ins_star",
                                f"{name}: \"{_short(best['title'])}\" got {best['views']:,} views, "
                                f"{round(best['views'] / avg, 1)}x the account average. Look at what sets it apart and do it again.",
                                name=name, title=_short(best["title"]), v=best["views"],
                                x=round(best["views"] / avg, 1)))

        flops = [i for i in with_views if i["views"] < avg * FLOP_RATIO]
        if flops:
            worst = min(flops, key=lambda i: i["views"])
            out.append(_insight("warn", "ins_flop",
                                f"{name}: {len(flops)} posts below 40% of the average, the weakest being "
                                f"\"{_short(worst['title'])}\" with {worst['views']:,} views.",
                                name=name, n=len(flops), title=_short(worst["title"]), v=worst["views"]))

    # Engagement: quanto una view si trasforma in interazione.
    total_views = sum(i["views"] for i in with_views)
    interactions = sum(i["likes"] + i["comments"] + i["shares"] for i in items)
    if total_views > 0 and interactions > 0:
        rate = interactions / total_views * 100
        out.append(_insight("info", "ins_engagement",
                            f"{name}: {rate:.1f}% di engagement sugli ultimi contenuti "
                            f"({interactions:,} interazioni su {total_views:,} views).",
                            name=name, rate=f"{rate:.1f}", i=interactions, v=total_views))

    # Ritmo di pubblicazione: il dato che spiega piu' spesso un calo.
    stamps = sorted([i["ts"] for i in items if i["ts"]], reverse=True)
    if len(stamps) >= 3:
        gaps = [(stamps[k] - stamps[k + 1]) / 86400 for k in range(len(stamps) - 1)]
        avg_gap = sum(gaps) / len(gaps)
        since = (time.time() - stamps[0]) / 86400
        # Chi pubblica piu' volte al giorno non ha "un contenuto ogni 0.2
        # giorni": e' vero ma illeggibile. Sotto la giornata si gira la
        # frazione e si parla di volte al giorno.
        daily = avg_gap > 0 and avg_gap < 1
        per_day = round(1 / avg_gap, 1) if daily else 0

        if since > max(avg_gap * 2, 1) and since >= 3:
            if daily:
                out.append(_insight("warn", "ins_cadence_broken_daily",
                                    f"{name}: di solito pubblichi piu' volte al giorno, ma l'ultimo contenuto "
                                    f"risale a {int(since)} giorni fa.",
                                    name=name, d=int(since)))
            else:
                out.append(_insight("warn", "ins_cadence_broken",
                                    f"{name}: di solito pubblichi ogni {avg_gap:.1f} giorni, ma l'ultimo contenuto "
                                    f"risale a {int(since)} giorni fa.",
                                    name=name, gap=f"{avg_gap:.1f}", d=int(since)))
        elif daily:
            out.append(_insight("info", "ins_cadence_daily",
                                f"{name}: pubblichi circa {per_day} volte al giorno.",
                                name=name, n=per_day))
        else:
            out.append(_insight("info", "ins_cadence",
                                f"{name}: pubblichi in media ogni {avg_gap:.1f} giorni.",
                                name=name, gap=f"{avg_gap:.1f}"))
    return out


def generate_insights(snapshot: dict, platform: str = "all") -> list[dict]:
    """Osservazioni sulla piattaforma indicata. Nessuna rete, nessun costo."""
    data = snapshot.get(platform) if isinstance(snapshot, dict) else None

    if platform == "x":
        return [_insight("info", "ins_x_free_plan",
                         "X non espone le statistiche di lettura sul piano gratuito: non c'e' nulla da analizzare.")]

    entities = _entities(platform, data)
    if not entities:
        return [_insight("info", "ins_no_data",
                         "Nessun dato da analizzare: collega un account e premi Refresh.")]

    out = []
    for e in entities:
        found = _analyze_entity(e["name"], e["items"])
        # Prima le criticita': se di un account si puo' dire una cosa sola,
        # che sia quella che chiede un intervento, non la sua cadenza.
        found.sort(key=lambda i: KIND_PRIORITY.get(i["kind"], 3))
        out.extend(found[:MAX_PER_ENTITY])

    # Confronto tra account: solo se ce n'e' piu' di uno, altrimenti e' un
    # "classifica di uno" che non aggiunge niente.
    if len(entities) > 1:
        totals = [(e["name"], sum(i["views"] for i in e["items"])) for e in entities]
        totals = [t for t in totals if t[1] > 0]
        if len(totals) > 1:
            totals.sort(key=lambda t: t[1], reverse=True)
            out.append(_insight("info", "ins_best_account",
                                f"{totals[0][0]} e' l'account che rende di piu': {totals[0][1]:,} views contro "
                                f"le {totals[-1][1]:,} di {totals[-1][0]}.",
                                best=totals[0][0], bv=totals[0][1], worst=totals[-1][0], wv=totals[-1][1]))

    if not out:
        out.append(_insight("good", "ins_nothing_notable",
                            "Nessuna criticita' rilevata sugli ultimi contenuti."))

    out.sort(key=lambda i: KIND_PRIORITY.get(i["kind"], 3))
    return out[:MAX_TOTAL]
