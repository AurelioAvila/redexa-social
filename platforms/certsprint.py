"""
Audit locale del repo CertSprint (npm audit + eslint se configurato) piu'
un ping di uptime/latenza sull'URL pubblico. Nessuna chiamata LLM qui -
e' analisi statica/rete, a costo zero di token.

npm audit ed eslint girano in thread paralleli (non uno dopo l'altro) e il
risultato viene cachato su disco per 15 minuti (sopravvive alla chiusura
dell'app, non solo in memoria): il codice del repo non cambia da un
refresh all'altro, quindi rilanciare npx ogni volta (il passaggio piu'
lento, specie a freddo) e' tempo sprecato - specialmente al primo refresh
dopo aver riaperto l'app, quando una cache solo in RAM sarebbe gia' vuota.
L'uptime resta invece live ad ogni refresh perche' quello puo' davvero
cambiare.
"""
import json
import os
import subprocess
import threading
import time

import requests

import cache

_CACHE_TTL = 15 * 60  # secondi


def _run_npm_audit(repo_path: str) -> dict:
    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=repo_path, capture_output=True, text=True, timeout=60, shell=True,
        )
        data = json.loads(result.stdout or "{}")
        meta = data.get("metadata", {}).get("vulnerabilities", {})
        return {"ok": True, "vulnerabilities": meta}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _run_eslint(repo_path: str) -> dict:
    has_eslint_config = any(
        os.path.exists(os.path.join(repo_path, f))
        for f in (".eslintrc.json", ".eslintrc.js", ".eslintrc.cjs", "eslint.config.js", "eslint.config.mjs")
    )
    if not has_eslint_config:
        return {"ok": True, "configured": False, "note": "Nessuna config ESLint trovata nel repo"}
    try:
        result = subprocess.run(
            ["npx", "eslint", ".", "-f", "json"],
            cwd=repo_path, capture_output=True, text=True, timeout=60, shell=True,
        )
        files = json.loads(result.stdout or "[]")
        errors = sum(f.get("errorCount", 0) for f in files)
        warnings = sum(f.get("warningCount", 0) for f in files)
        return {"ok": True, "configured": True, "errors": errors, "warnings": warnings}
    except Exception as exc:
        return {"ok": False, "configured": True, "error": str(exc)}


def _check_uptime(url: str) -> dict:
    try:
        start = time.time()
        resp = requests.get(url, timeout=15)
        latency_ms = round((time.time() - start) * 1000)
        return {"ok": True, "status_code": resp.status_code, "latency_ms": latency_ms, "up": resp.status_code < 500}
    except Exception as exc:
        return {"ok": False, "up": False, "error": str(exc)}


def count_units() -> int:
    return 3  # audit, lint, uptime


def fetch_stats(on_item=None) -> dict:
    repo_path = os.environ.get("CERTSPRINT_REPO_PATH")
    public_url = os.environ.get("CERTSPRINT_PUBLIC_URL")
    valid_repo = bool(repo_path and os.path.isdir(repo_path))

    results = {}

    def _audit_job():
        cached = cache.kv_get("certsprint_audit", _CACHE_TTL)
        if cached is not None:
            results["audit"] = cached
        else:
            r = _run_npm_audit(repo_path) if valid_repo else {"ok": False, "error": "CERTSPRINT_REPO_PATH non valido"}
            cache.kv_set("certsprint_audit", r)
            results["audit"] = r
        if on_item:
            on_item()

    def _lint_job():
        cached = cache.kv_get("certsprint_lint", _CACHE_TTL)
        if cached is not None:
            results["lint"] = cached
        else:
            r = _run_eslint(repo_path) if valid_repo else {"ok": False, "error": "CERTSPRINT_REPO_PATH non valido"}
            cache.kv_set("certsprint_lint", r)
            results["lint"] = r
        if on_item:
            on_item()

    def _uptime_job():
        results["uptime"] = _check_uptime(public_url) if public_url else {"ok": False, "error": "CERTSPRINT_PUBLIC_URL non configurato"}
        if on_item:
            on_item()

    threads = [threading.Thread(target=fn) for fn in (_audit_job, _lint_job, _uptime_job)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return {"platform": "certsprint", "npm_audit": results["audit"], "eslint": results["lint"], "uptime": results["uptime"]}
