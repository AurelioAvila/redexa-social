"""
Analisi statistica calcolata dal codice sui dati gia' raccolti (zero
chiamate esterne, zero costo) - top post per views e fascia oraria di
pubblicazione con la performance media migliore, per piattaforma e
complessiva. Serve a rispondere a "quali post funzionano e quando li
pubblico" senza dover chiedere un'analisi AI ogni volta.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import benchmarks


def _num(valore) -> float:
    """Un numero utilizzabile, qualunque cosa sia arrivata.

    I dati passano da JSON salvato su disco e riletto: basta una riga
    rovinata da una scrittura interrotta, o una piattaforma che cambia il
    tipo di un campo (YouTube per esempio manda le statistiche come
    stringhe), perche' un confronto ">" fra str e int faccia esplodere
    tutta la pagina Overview. Qui il dato strano diventa zero e si tira
    avanti, come gia' si fa in cache.py per le righe illeggibili.
    """
    if valore is None or isinstance(valore, bool):
        return 0.0
    try:
        n = float(valore)
    except (TypeError, ValueError):
        return 0.0
    # inf e NaN passano indenni da float() e da json.loads (che accetta
    # Infinity e NaN): se arrivassero fin qui manderebbero in errore ogni
    # arrotondamento successivo.
    if n != n or n in (float("inf"), float("-inf")):
        return 0.0
    return n


def _lista(valore) -> list:
    """Solo le liste si iterano: un dizionario o una stringa al posto di una
    lista arriverebbe fino a `.get()` su un carattere."""
    return valore if isinstance(valore, list) else []


def _weekday(iso_or_epoch) -> int | None:
    """0 = lunedi', 6 = domenica. None se la data non c'e' o non si legge.

    Serve per la mappa giorno x ora: sapere che rendi meglio "alle 18" e'
    molto meno utile che sapere "il martedi' alle 18", ma finora il giorno
    veniva buttato via anche se le tre piattaforme lo mandano tutte.
    """
    from datetime import datetime, timezone

    if iso_or_epoch in (None, ""):
        return None
    try:
        if isinstance(iso_or_epoch, (int, float)):
            return datetime.fromtimestamp(iso_or_epoch, tz=timezone.utc).weekday()
        testo = str(iso_or_epoch).replace("Z", "+00:00")
        return datetime.fromisoformat(testo).weekday()
    except (ValueError, TypeError, OSError, OverflowError):
        return None


def _youtube_items(data: dict) -> list[dict]:
    if not data:
        return []
    out = []
    for c in _lista(data.get("channels")):
        if not isinstance(c, dict) or not c.get("ok"):
            continue
        for v in _lista(c.get("recent_videos")):
            if not isinstance(v, dict):
                continue
            likes = _num(v.get("likes"))
            comments = _num(v.get("comments"))
            views = _num(v.get("views"))
            out.append({
                "platform": "youtube", "account": c.get("name", ""), "title": v.get("title", ""),
                "views": views, "hour": v.get("publish_hour_utc"),
                "weekday": _weekday(v.get("published")),
                # YouTube non espone ne' salvataggi ne' condivisioni con lo
                # scope readonly: restano a zero invece di essere inventati.
                "likes": likes, "comments": comments, "shares": 0, "saved": 0,
                "interactions": likes + comments,
                # Le impression non sono disponibili senza la YouTube
                # Analytics API (autorizzazione diversa): la base di
                # confronto per l'engagement sono le views.
                "reach": views,
            })
    return out


def _instagram_items(data: dict) -> list[dict]:
    if not data:
        return []
    out = []
    for a in _lista(data.get("accounts")):
        if not isinstance(a, dict) or not a.get("ok"):
            continue
        for p in _lista(a.get("recent_posts")):
            if not isinstance(p, dict):
                continue
            hour = None
            ts = p.get("timestamp")
            if ts:
                try:
                    hour = int(str(ts)[11:13])
                except (ValueError, TypeError):
                    hour = None
            likes = _num(p.get("likes"))
            comments = _num(p.get("comments"))
            shares = _num(p.get("shares"))
            saved = _num(p.get("saved"))
            views = _num(p.get("views"))
            # total_interactions arriva gia' sommato da Meta: quando c'e' si
            # usa quello, cosi' non si perdono le interazioni che l'API
            # conta e noi non elenchiamo (per esempio le risposte).
            interactions = _num(p.get("total_interactions"))
            if not interactions:
                interactions = likes + comments + shares + saved
            out.append({
                "platform": "instagram", "account": a.get("name", ""),
                "title": p.get("caption", "(senza didascalia)"),
                "views": views, "hour": hour,
                "weekday": _weekday(ts),
                "likes": likes, "comments": comments, "shares": shares, "saved": saved,
                "interactions": interactions,
                # reach = account unici raggiunti, la base corretta per
                # l'engagement su Instagram. Se manca si ripiega sulle views.
                "reach": _num(p.get("reach")) or views,
            })
    return out


def _tiktok_items(data: dict) -> list[dict]:
    if not data:
        return []
    out = []
    for a in _lista(data.get("accounts")):
        if not isinstance(a, dict) or not a.get("ok"):
            continue
        for v in _lista(a.get("recent_videos")):
            if not isinstance(v, dict):
                continue
            likes = _num(v.get("likes"))
            comments = _num(v.get("comments"))
            shares = _num(v.get("shares"))
            views = _num(v.get("views"))
            out.append({
                "platform": "tiktok", "account": a.get("name", ""), "title": v.get("title", ""),
                "views": views, "hour": v.get("publish_hour_utc"),
                "weekday": _weekday(v.get("create_time")),
                # TikTok non espone i salvataggi con gli scope di lettura.
                "likes": likes, "comments": comments, "shares": shares, "saved": 0,
                "interactions": likes + comments + shares,
                "reach": views,
            })
    return out


def _followers_by_platform(snapshot: dict) -> dict:
    """Follower totali per piattaforma, sommati sugli account collegati.

    Serve al confronto con i valori medi del settore, che sono espressi in
    percentuale sui follower. Le piattaforme che non li espongono restano
    fuori invece di comparire con uno zero che falserebbe ogni rapporto.
    """
    out = {}

    canali = _lista((snapshot.get("youtube") or {}).get("channels"))
    iscritti = [_num(c.get("subscribers")) for c in canali
                if isinstance(c, dict) and c.get("ok")]
    if any(iscritti):
        out["youtube"] = int(sum(iscritti))

    for piattaforma in ("instagram", "tiktok"):
        conti = _lista((snapshot.get(piattaforma) or {}).get("accounts"))
        valori = [_num(a.get("followers")) for a in conti
                  if isinstance(a, dict) and a.get("ok")]
        if any(valori):
            out[piattaforma] = int(sum(valori))

    return out


def _engagement(items: list[dict]) -> dict | None:
    """Quanto chi vede un contenuto ci interagisce davvero.

    Si calcola sulla reach (o sulle views dove la reach non esiste) e non
    sul numero di contenuti: dieci post da mille visualizzazioni e uno da
    diecimila devono pesare per quello che hanno realmente raggiunto.
    """
    base = sum(i.get("reach", 0) or 0 for i in items)
    if base <= 0:
        return None
    interazioni = sum(i.get("interactions", 0) or 0 for i in items)
    salvataggi = sum(i.get("saved", 0) or 0 for i in items)
    condivisioni = sum(i.get("shares", 0) or 0 for i in items)
    return {
        "rate": round(interazioni / base * 100, 2),
        "save_rate": round(salvataggi / base * 100, 2),
        "share_rate": round(condivisioni / base * 100, 2),
        "interactions": interazioni,
        "reach": base,
        "items": len(items),
    }


# Una "fascia oraria migliore" ricavata da un solo post non e' un'analisi:
# e' quel post. Sotto queste soglie l'app dice che i dati non bastano
# invece di stampare un numero che sembra un consiglio.
MIN_ITEMS_FOR_HOURS = 6      # contenuti con orario e views, in totale
MIN_SAMPLES_PER_HOUR = 2     # contenuti dentro la singola fascia


def compute_analytics(snapshot: dict) -> dict:
    all_items = (
        _youtube_items(snapshot.get("youtube"))
        + _instagram_items(snapshot.get("instagram"))
        + _tiktok_items(snapshot.get("tiktok"))
    )

    top_posts = sorted(all_items, key=lambda i: i["views"], reverse=True)[:10]

    # I contenuti ancora a zero views non dicono nulla sull'orario: tenerli
    # dentro la media abbassa ogni fascia in modo uniforme e fa sembrare
    # "migliore" semplicemente l'ora dell'unico contenuto andato bene.
    rated = [i for i in all_items if i["hour"] is not None and i["views"] > 0]

    hour_buckets = {}  # hour -> {"views": totale, "count": n}
    for item in rated:
        b = hour_buckets.setdefault(item["hour"], {"views": 0, "count": 0})
        b["views"] += item["views"]
        b["count"] += 1

    hourly = [
        {"hour": h, "avg_views": round(b["views"] / b["count"]), "count": b["count"]}
        for h, b in hour_buckets.items()
    ]
    hourly.sort(key=lambda h: h["avg_views"], reverse=True)

    # Una fascia si propone come consiglio solo se poggia su piu' di un
    # contenuto e se c'e' abbastanza materiale complessivo.
    enough = len(rated) >= MIN_ITEMS_FOR_HOURS
    reliable = [h for h in hourly if h["count"] >= MIN_SAMPLES_PER_HOUR] if enough else []

    # Tutte le 24 ore, anche quelle senza pubblicazioni: servono al grafico
    # della giornata, dove un buco e' un'informazione (li' non hai mai
    # pubblicato) tanto quanto una barra alta.
    by_hour = {h["hour"]: h for h in hourly}
    all_hours = [
        by_hour.get(h, {"hour": h, "avg_views": 0, "count": 0})
        for h in range(24)
    ]

    # Mappa giorno x ora: "il martedi' alle 18" e' un consiglio, "alle 18"
    # da solo molto meno. Si tengono solo le celle con almeno un contenuto:
    # una griglia 7x24 tutta a zero non e' un'informazione.
    celle = {}
    for item in rated:
        if item.get("weekday") is None:
            continue
        chiave = (item["weekday"], item["hour"])
        c = celle.setdefault(chiave, {"views": 0, "count": 0})
        c["views"] += item["views"]
        c["count"] += 1
    heatmap = [
        {"weekday": g, "hour": o, "avg_views": round(c["views"] / c["count"]), "count": c["count"]}
        for (g, o), c in sorted(celle.items())
    ]

    per_platform = {}
    for item in all_items:
        p = per_platform.setdefault(item["platform"], {"views": 0, "count": 0})
        p["views"] += item["views"]
        p["count"] += 1

    # Engagement complessivo e per piattaforma, dai dati che gia' scaricavamo
    # e buttavamo via: fino ad ora di ogni contenuto si guardavano solo le
    # views, mentre like, commenti, condivisioni e salvataggi arrivavano
    # dalle API a ogni aggiornamento e finivano ignorati.
    engagement = _engagement(all_items)
    followers = _followers_by_platform(snapshot)
    engagement_per_platform = {}
    confronti = []
    for piattaforma in per_platform:
        contenuti = [i for i in all_items if i["platform"] == piattaforma]
        misura = _engagement(contenuti)
        if not misura:
            continue
        # Engagement sui follower: e' la definizione usata dai report di
        # settore, diversa da quella sulla reach calcolata sopra. Serve solo
        # per il confronto con i benchmark, e non sostituisce l'altra.
        seguaci = followers.get(piattaforma)
        if seguaci and contenuti:
            interazioni = sum(i.get("interactions", 0) or 0 for i in contenuti)
            misura["follower_rate"] = round(
                interazioni / (len(contenuti) * seguaci) * 100, 2)
            confronto = benchmarks.compare(piattaforma, seguaci, misura["follower_rate"])
            if confronto:
                confronti.append(confronto)
        engagement_per_platform[piattaforma] = misura

    total_views = sum(i["views"] for i in all_items)
    with_views = [i for i in all_items if i["views"] > 0]

    # Contenuti sopra e sotto la propria media: il confronto utile e' con
    # se stessi, non con una media di settore che non sa nulla del tuo
    # pubblico. Serve una base minima, altrimenti "sopra la media" descrive
    # solo il caso.
    outliers = {"over": [], "under": []}
    if len(with_views) >= 4:
        media = total_views / len(with_views)
        if media > 0:
            ordinati = sorted(with_views, key=lambda i: i["views"], reverse=True)
            for voce in ordinati:
                scarto = round((voce["views"] - media) / media * 100)
                riga = {"platform": voce["platform"], "account": voce["account"],
                        "title": voce["title"], "views": voce["views"], "delta_pct": scarto}
                if scarto >= 50 and len(outliers["over"]) < 5:
                    outliers["over"].append(riga)
                elif scarto <= -50:
                    outliers["under"].append(riga)
            outliers["under"] = outliers["under"][-5:]
            outliers["avg"] = round(media)

    return {
        "engagement": engagement,
        "engagement_per_platform": engagement_per_platform,
        "followers_per_platform": followers,
        "benchmarks": confronti,
        "heatmap": heatmap,
        "outliers": outliers,
        "top_posts": top_posts,
        "best_hours": reliable[:5],
        "all_hours": all_hours,
        "per_platform": per_platform,
        "total_views": total_views,
        "total_items_analyzed": len(all_items),
        # Quanti contenuti hanno davvero dati: la media per contenuto
        # calcolata su tutti (compresi quelli a zero) e' matematicamente
        # corretta ma racconta una cosa diversa da quella che sembra.
        "items_with_views": len(with_views),
        "avg_views_per_item": round(total_views / len(with_views)) if with_views else 0,
        # Il frontend usa questi per dire "servono piu' dati" invece di
        # mostrare una fascia oraria inventata.
        "hours_enough_data": bool(reliable),
        "hours_items_needed": max(0, MIN_ITEMS_FOR_HOURS - len(rated)),
    }
