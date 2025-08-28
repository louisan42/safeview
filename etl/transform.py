import time
import io
import csv
from typing import Dict, Iterable, Generator, Optional, Any, List
from datetime import datetime, timezone
import requests

DEFAULT_TIMEOUT = 60


def _retry_request(url: str, params: Dict, max_retries: int, backoff: int):
    attempt = 0
    while True:
        try:
            r = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()
            return r
        except requests.RequestException:
            attempt += 1
            if attempt > max_retries:
                raise
            time.sleep(backoff * (2 ** (attempt - 1)))


def fetch_paginated(service_url: str, where: str, fields: str, batch_size: int, max_retries: int, backoff: int) -> Generator[Dict, None, None]:
    offset = 0
    while True:
        params = {
            'where': where,
            'outFields': fields,
            'orderByFields': 'OBJECTID',
            'resultRecordCount': batch_size,
            'resultOffset': offset,
            'f': 'json',
        }
        resp = _retry_request(service_url, params, max_retries, backoff)
        data = resp.json()
        feats = data.get('features', [])
        if not feats:
            break
        for f in feats:
            yield f.get('attributes', {})
        offset += len(feats)


def _epoch_ms_to_iso_utc(val: Any) -> Optional[str]:
    if val in (None, "", "null"):
        return None
    try:
        ms = int(val)
        # guard against clearly invalid values
        if ms < 0:
            return None
        dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        return dt.isoformat()
    except (ValueError, OverflowError, TypeError):
        return None


def _safe(val: Any) -> str:
    return "" if val is None else str(val)


def build_incidents_csv(dataset: str, rows: Iterable[Dict]) -> io.StringIO:
    buf = io.StringIO()
    w = csv.writer(buf)
    for a in rows:
        report_date = _epoch_ms_to_iso_utc(a.get('REPORT_DATE'))
        occ_date = _epoch_ms_to_iso_utc(a.get('OCC_DATE'))
        w.writerow([
            dataset,
            _safe(a.get('EVENT_UNIQUE_ID')),
            _safe(report_date),
            _safe(occ_date),
            _safe(a.get('OFFENCE')),
            _safe(a.get('MCI_CATEGORY')),
            _safe(a.get('HOOD_158')),
            _safe(a.get('LONG_WGS84')),
            _safe(a.get('LAT_WGS84')),
        ])
    buf.seek(0)
    return buf


def fetch_neighbourhoods_geojson(url: str, fields: str, max_retries: int, backoff: int) -> List[Dict[str, Any]]:
    """
    Returns a list of GeoJSON Feature dicts with properties and geometry (EPSG:4326).
    """
    params = {
        'where': '1=1',
        'outFields': fields,
        'returnGeometry': 'true',
        'outSR': 4326,
        'f': 'geojson',
    }
    resp = _retry_request(url, params, max_retries, backoff)
    data = resp.json()
    feats = data.get('features', [])
    # Normalize property keys we use downstream
    for f in feats:
        props = f.get('properties', {})
        # Sometimes keys vary in case; map to expected names if present
        for k in list(props.keys()):
            lk = k.upper()
            if lk == 'AREA_LONG_CODE' and k != 'AREA_LONG_CODE':
                props['AREA_LONG_CODE'] = props[k]
            if lk == 'AREA_SHORT_CODE' and k != 'AREA_SHORT_CODE':
                props['AREA_SHORT_CODE'] = props[k]
            if lk == 'AREA_NAME' and k != 'AREA_NAME':
                props['AREA_NAME'] = props[k]
    return feats
