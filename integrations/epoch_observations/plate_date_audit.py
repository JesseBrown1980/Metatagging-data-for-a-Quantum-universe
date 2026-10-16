#!/usr/bin/env python3
"""Read official DSS plate metadata to recover original photographic exposures.
No epoch is inferred from the SkyView reprojection timestamp or survey label.
"""
import csv
import io
import urllib.request
from pathlib import Path

URL="https://outerspace.stsci.edu/download/attachments/176435492/SurveyPlateListLatest.csv"
PLATES=("S134","XV098","XS098","GR134")
out=Path("epoch_outputs")
out.mkdir(exist_ok=True)
req=urllib.request.Request(URL,headers={"User-Agent":"Asolaria-Source-Custody/1.0"})
try:
    with urllib.request.urlopen(req,timeout=60) as resp:
        body=resp.read(10_000_001)
        if len(body)>=10_000_001:raise ValueError("EXCEEDS_INDEX_LIMIT")
    (out/"DSS-PLATE-INDEX.csv").write_bytes(body)
    source=body.decode("utf-8-sig",errors="replace")
    print("PLATE_INDEX_BYTES",len(body))
    lines=source.splitlines()
    print("PLATE_INDEX_FIRST",lines[0][:350])
    print("PLATE_INDEX_SECOND",lines[1][:350] if len(lines)>1 else "NONE")
    matches=0
    for plate in PLATES:
        needle=plate.lower()
        hits=[line for line in lines[1:] if needle in line.lower()]
        for hit in hits[:8]:
            print("PLATE_MATCH",plate,hit[:500]);matches+=1
        if not hits:print("PLATE_MISSING",plate)
    print("PLATE_MATCH_TOTAL",matches)
except Exception as exc:
    print("PLATE_INDEX_UNAVAILABLE",type(exc).__name__,str(exc)[:260])
