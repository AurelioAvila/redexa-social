"""
Analisi statistica calcolata dal codice sui dati gia' raccolti (zero
chiamate esterne, zero costo) - top post per views e fascia oraria di
pubblicazione con la performance media migliore, per piattaforma e
complessiva. Serve a rispondere a "quali post funzionano e quando li
pubblico" senza dover chiedere un'analisi AI ogni volta.
"""


def _youtube_items(data: dict) -> list[dict]:
    if not data:
        return []
    out = []
    for c in data.get("channels", []):
        if not c.get("ok"):
            continue
        for v in c.get("recent_videos", []):
            out.append({
                "platform": "youtube", "account": c["name"], "title": v.get("title", ""),
                "views": v.get("views", 0), "hour": v.get("publish_hour_utc"),
            })
    return out


def _instagram_items(data: dict) -> list[dict]:
    if not data:
        return []
    out = []
    for a in data.get("accounts", []):
        if not a.get("ok"):
            continue
        for p in a.get("recent_posts", []):
            hour = None
            ts = p.get("timestamp")
            if ts:
                try:
                    hour = int(ts[11:13])
                except Exception:
                    hour = None
            out.append({
                "platform": "instagram", "account": a["name"], "title": p.get("caption", "(senza didascalia)"),
                "views": p.get("views", 0), "hour": hour,
            })
    return out


def _tiktok_items(data: dict) -> list[dict]:
    if not data:
        return []
    out = []
    for a in data.get("accounts", []):
        if not a.get("ok"):
            continue
        for v in a.get("recent_videos", []):
            out.append({
                "platform": "tiktok", "account": a["name"], "title": v.get("title", ""),
                "views": v.get("views", 0), "hour": v.get("publish_hour_utc"),
            })
    return out


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

    per_platform = {}
    for item in all_items:
        p = per_platform.setdefault(item["platform"], {"views": 0, "count": 0})
        p["views"] += item["views"]
        p["count"] += 1

    total_views = sum(i["views"] for i in all_items)
    with_views = [i for i in all_items if i["views"] > 0]

    return {
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
