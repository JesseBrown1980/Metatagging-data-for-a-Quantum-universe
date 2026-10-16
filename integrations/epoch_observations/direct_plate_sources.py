#!/usr/bin/env python3
"""Archive exact-date DSS Proxima plate cutouts; no invented observation times.

Uses official STScI Plate ID/date index. Requests an INDIVIDUAL photographic
plate through the original archive plate-finder rather than a mixed-date
SkyView mosaic. Records HOLD if source pixels cannot be attributed to a plate.
This is archival acquisition only; runtime state remains Rust 1.81 HBP/HBI.
"""
import csv
import datetime
import hashlib
import io
import os
import pathlib
import urllib.parse
import urllib.request

TARGETS=("25","060Z","A1AG","A29M")
PATH=pathlib.Path(os.environ.get("ASOLARIA_EPOCH_DIR","epoch_outputs"))
PATH.mkdir(parents=True,exist_ok=True)
INDEX=PATH/"DSS-PLATE-INDEX.csv"
def digest(b): return hashlib.sha256(b).hexdigest()
def get(url,max_bytes=12_000_000):
    request=urllib.request.Request(url,headers={
        "User-Agent":"Asolaria-Exact-Plate-Date-Research/1.0",
        "Accept":"image/fits,application/fits,application/octet-stream,*/*"})
    with urllib.request.urlopen(request,timeout=55) as response:
        body=response.read(max_bytes+1)
        if len(body)>max_bytes: raise ValueError("SOURCE_TOO_LARGE")
        return body,response.url,response.headers.get("content-type","")

def fits_metadata(buf):
    if len(buf)<2880 or not buf.startswith(b"SIMPLE  "):
        raise ValueError("RESPONSE_NOT_PRIMARY_FITS")
    out={}
    for ix in range(0,min(2880*20,len(buf)),80):
        field=buf[ix:ix+80].decode("ascii","replace")
        key=field[:8].strip()
        if key=="END": return out
        if field[8:10]=="= ":
            out[key]=field[10:].split("/")[0].strip().strip("'")
    raise ValueError("FITS_HAS_NO_END")
def audit():
    with INDEX.open(encoding="utf-8-sig",newline="") as f:
        rows={row["plateID"].upper():row for row in csv.DictReader(f)}
    manifest=["HBP1|schema=ASOLARIA-DATED-DSS-DIRECT-PLATES-V1|source=STScI_DSS|json=0\n"]
    pass_count=0
    for identifier in TARGETS:
        plate=rows.get(identifier)
        if not plate: raise ValueError("OFFICIAL_PLATE_ID_MISSING_"+identifier)
        when=plate["UTobservation"]
        datetime.datetime.fromisoformat(when)
        q=urllib.parse.urlencode({
          "ra":"14:29:42.94","dec":"-62:40:46.16","height":"10.0",
          "width":"10.0","format":"FITS","plate_id":identifier,
          "action":"Extract"})
        url="https://archive.stsci.edu/cgi-bin/dss_plate_finder?"+q
        stem="DSS_PLATE_"+identifier
        try:
            raw,final,mime=get(url)
            if raw[:2]==b"\x1f\x8b":
                import gzip
                raw=gzip.decompress(raw)
            if not raw.startswith(b"SIMPLE  "):
                # Legacy plate-finder may now emit HTML; request native STScI
                # single-survey FITS instead and verify REGION against index.
                survey_url="https://archive.stsci.edu/cgi-bin/dss_search?"
                variant={"25":"dss1","060Z":"quickv","A1AG":"poss2ukstu_red",
                         "A29M":"poss2ukstu_red"}[identifier]
                fallback=urllib.parse.urlencode({
                    "r":"14 29 42.94","d":"-62 40 46.16","e":"J2000",
                    "h":"10.0","w":"10.0","v":variant,
                    "f":"fits","c":"none"
                })
                raw,final,mime=get(survey_url+fallback)
                if raw[:2]==b"\x1f\x8b":
                    import gzip
                    raw=gzip.decompress(raw)
            hd=fits_metadata(raw)
            region=plate["Region"].upper()
            found=str(hd.get("REGION","")).upper()
            # Exact station, region/plate must match. A CGI URL alone is not
            # enough to establish that an archive returned the requested plate.
            if region not in found and identifier not in found:
                raise ValueError("RESPONSE_DOES_NOT_IDENTIFY_ORIGINAL_PLATE")
            fn=stem+".fits"
            (PATH/fn).write_bytes(raw)
            row=(f"PLATE|json=0|status=SOURCE_VERIFIED|plate_id={identifier}|"
                 f"region={region}|official_UTC={when}|"
                 f"plate_filter={plate['Band']}|source_url={final}|"
                 f"fits_region={found}|bytes={len(raw)}|sha256={digest(raw)}|"
                 f"file={fn}|dtype=ORIGINAL_PLATE_CUTOUT\n")
            pass_count+=1
        except Exception as exc:
            row=(f"PLATE|json=0|status=HELD|plate_id={identifier}|"
                 f"region={plate['Region']}|official_UTC={when}|"
                 f"reason={type(exc).__name__}|message={str(exc)[:130]}\n")
        manifest.append(row)
        print(row.strip())
    (PATH/"DSS-SOURCE-PLATES.hbp").write_text("".join(manifest),encoding="utf-8")
    print("SOURCE_VERIFIED_INDEPENDENT_DSS_PLATES",pass_count)
    if pass_count==0: raise RuntimeError("NO_EXACT_DSS_PLATES_RETURNED")
if __name__=="__main__":audit()
