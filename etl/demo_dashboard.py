import os
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import psycopg

app = FastAPI(title="SafetyView Demo Dashboard", description="Demo-only dashboard to verify DB contents", version="0.1.0")


def _get_dsn() -> str:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        raise RuntimeError("PG_DSN env var is required to run the demo dashboard")
    return dsn


def _conn():
    return psycopg.connect(_get_dsn())


@app.get("/api/health")
def health() -> Dict[str, Any]:
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/summary")
def summary() -> Dict[str, Any]:
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM tps_incidents")
                total = cur.fetchone()[0]
                cur.execute(
                    """
                    SELECT dataset, COUNT(*) AS cnt
                    FROM tps_incidents
                    GROUP BY dataset
                    ORDER BY dataset
                    """
                )
                by_dataset = [{"dataset": r[0], "count": int(r[1])} for r in cur.fetchall()]
                cur.execute(
                    """
                    SELECT day::date, dataset, cnt
                    FROM v_incidents_daily
                    WHERE day >= now() - interval '30 days'
                    ORDER BY day, dataset
                    """
                )
                daily: List[Dict[str, Any]] = [
                    {"day": str(r[0]), "dataset": r[1], "count": int(r[2])} for r in cur.fetchall()
                ]
        return {"total": int(total), "by_dataset": by_dataset, "daily": daily}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    # Very simple HTML for quick verification; not for production use
    return (
        """
        <!doctype html>
        <html>
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>SafetyView Demo Dashboard</title>
          <style>
            body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; }
            h1 { margin-bottom: 0.25rem; }
            .muted { color: #666; }
            table { border-collapse: collapse; margin-top: 1rem; }
            th, td { border: 1px solid #ddd; padding: 0.5rem 0.75rem; }
            th { background: #f8f8f8; }
            .grid { display: grid; grid-template-columns: 1fr; gap: 1.5rem; }
            @media (min-width: 900px) { .grid { grid-template-columns: 1fr 1fr; } }
            .card { border: 1px solid #eee; border-radius: 8px; padding: 1rem; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
          </style>
        </head>
        <body>
          <h1>SafetyView</h1>
          <div class="muted">Demo dashboard (for testing DB only)</div>
          <div class="grid">
            <div class="card">
              <h2>Summary</h2>
              <div id="summary">Loading…</div>
            </div>
            <div class="card">
              <h2>Daily (last 30 days)</h2>
              <div id="daily">Loading…</div>
            </div>
          </div>
          <script>
            async function load() {
              const r = await fetch('/api/summary');
              const data = await r.json();
              const sum = document.getElementById('summary');
              sum.innerHTML = `
                <div><b>Total incidents:</b> ${data.total.toLocaleString()}</div>
                <table>
                  <thead><tr><th>Dataset</th><th>Count</th></tr></thead>
                  <tbody>
                    ${data.by_dataset.map(d => `<tr><td>${d.dataset}</td><td style="text-align:right">${d.count.toLocaleString()}</td></tr>`).join('')}
                  </tbody>
                </table>
              `;
              const daily = document.getElementById('daily');
              const rows = data.daily.map(d => `<tr><td>${d.day}</td><td>${d.dataset}</td><td style="text-align:right">${d.count}</td></tr>`).join('');
              daily.innerHTML = `
                <table>
                  <thead><tr><th>Day</th><th>Dataset</th><th>Count</th></tr></thead>
                  <tbody>${rows}</tbody>
                </table>
              `;
            }
            load().catch(e => {
              document.getElementById('summary').textContent = 'Error: ' + e;
            });
          </script>
        </body>
        </html>
        """
    )
