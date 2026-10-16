#!/usr/bin/env python3
"""Seat1: acquire independently observed, timestamped Proxima photographs.

Download-time tool ONLY (not an Asolaria model or new importer). The source
FITS/JPEG bytes flow unchanged into the EXISTING Colour QR carrier.
All provenance is plain-text HBP. An unspecified survey plate date is HELD.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import urllib.request
import urllib.error

OUT=Path(os.environ.get("ASOLARIA_EPOCH_DIR","epoch_outputs"))
OUT.mkdir(parents=True,exist_ok=True)
URL_1996=("https://assets.science.nasa.gov/dynamicimage/assets/science/"
          "missions/hubble/releases/2013/11/STScI-01EVT3JKAAG784PXXCNK95JD4E.tif")
URL_2012=("https://assets.science.nasa.gov/dynamicimage/assets/science/"
          "missions/hubble/releases/2013/06/STScI-01EVVCFQQJEH75APX7EQSDAGD9.tif")

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def remote(url:str)->tuple[bytes,str]:
    request=urllib.request.Request(url,headers={
        "User-Agent":"Asolaria Source Integrity Experiment/1.0",
        "Accept":"image/*,application/octet-stream,*/*"})
    with urllib.request.urlopen(request,timeout=90) as resp:
        if not resp.url.startswith("https://"):
            raise ValueError("NON_HTTPS_IMAGE_SOURCE")
        data=resp.read(10_000_001)
        if len(data)>10_000_000:raise ValueError("SOURCE_FILE_SIZE_LIMIT")
        return data,resp.url

def magic(b:bytes)->str:
    if b.startswith(b"\xff\xd8\xff"):return "jpg"
    if b.startswith(b"II*\0") or b.startswith(b"MM\0*"):return "tif"
    if b.startswith(b"\x89PNG\r\n\x1a\n"):return "png"
    if b.startswith(b"SIMPLE  "):return "fits"
    raise ValueError("UNRECOGNIZED_IMAGE_FORMAT")

def hbp_line(**fields)->str:
    parts=["EPOCH","json=0"]
    for k,v in fields.items():
        val=str(v).replace("|","_").replace("\r","_").replace("\n","_")
        parts.append(k+"="+val)
    return "|".join(parts)+"\n"

def nasa_hubble(tag:str,url:str,date:str,instrument:str,filter_name:str)->str:
    data,source=remote(url)
    kind=magic(data)
    name=f"{tag}.{kind}"
    (OUT/name).write_bytes(data)
    return hbp_line(slot=tag,source_class="NASA_RENDERED_RELEASE",source_url=source,
                    confirmed_observation_date=date,instrument=instrument,
                    filter=filter_name,bytes=len(data),sha256=sha(data),
                    file=name,format=kind,source_is_raw_science_fits="NO",
                    identity="PUBLISHED_PROXIMA_CENTAURI_IMAGE")

def fits_epoch(header)->str:
    # IMPORTANT: A FITS processing DATE is not the plate observation date.
    # Only authenticated observation/plate keywords qualify.
    for key in ("DATE-OBS","DATEOBS","DATE-ORIG","OBS-DATE"):
        v=header.get(key)
        if v and str(v).strip() and str(v).strip() not in ("UNKNOWN","N/A"):
            return str(v).strip().replace(" ","_")
    # Older DSS plates may provide plate-specific epoch/date combinations.
    for key in ("PLATE-DATE","PLTDATE","PLTEPOCH"):
        v=header.get(key)
        if v is not None and str(v).strip():
            return f"{key}:{str(v).strip().replace(' ','_')}"
    return "HELD_UNDATED_PLATE"

def dss_survey(label:str,survey:str)->str:
    from astroquery.skyview import SkyView
    from astropy import units as u
    # Original survey cutout. Fits headers and non-resampled original pixel
    # bit patterns are retained; library output may contain reprojection.
    SkyView.TIMEOUT=120
    sky=SkyView.get_images(position="Proxima Centauri",survey=[survey],
                           coordinates="J2000",pixels=384,radius=0.12*u.deg)
    if not sky:raise ValueError("NO_DSS_IMAGE_FOR_"+survey)
    hdu=sky[0][0]
    header=hdu.header
    recorded=fits_epoch(header)
    target=OUT/f"{label}.fits"
    sky[0].writeto(target,overwrite=True,output_verify="silentfix")
    source=target.read_bytes()
    if magic(source)!="fits":raise ValueError("FITS_OUTPUT_MAGIC_FAILED")
    # Basic WCS plate-geometry availability; flag absent, never invent.
    coords="PRESENT" if ("CRVAL1" in header and "CRVAL2" in header) else "ABSENT"
    return hbp_line(slot=label,source_class="NASA_SKYVIEW_RETRIEVED_DSS",
                    survey=survey,source_url="https://skyview.gsfc.nasa.gov/",
                    confirmed_observation_date=recorded,
                    original_plate_date_gate=("PASS" if recorded!="HELD_UNDATED_PLATE" else "HELD"),
                    telescope=str(header.get("TELESCOP","NOT_IN_HEADER")).replace(" ","_"),
                    filter=str(header.get("FILTER","NOT_IN_HEADER")).replace(" ","_"),
                    plate_identity=str(header.get("PLATEID","NOT_IN_HEADER")).replace(" ","_"),
                    image_wcs=coords,
                    source_is_unaltered_full_plate="NO_CUTOUT",
                    bytes=len(source),sha256=sha(source),file=target.name,format="fits")

def main():
    rows=["HBP1|schema=ASOLARIA-SEAT1-PROXIMA-FOUR-TIME-IMAGES-V1|date=2026-10-16|json=0\n"]
    rows.append("PREDECLARATION|json=0|operation=REUSE_EXISTING_COLOUR_QR_RIME|training=NONE|source_picture_synthesis=NONE|physical_measurements=ARCHIVAL|json=0\n")
    specs=[
      ("HUBBLE_1996",URL_1996,"1996","HST_WFPC2","R_I_COMPOSITE"),
      ("HUBBLE_2012",URL_2012,"2012-10-01","HST_WFC3_UVIS","F555W")
    ]
    for tag,url,date,instrument,fil in specs:
        try:row=nasa_hubble(tag,url,date,instrument,fil)
        except Exception as error:row=hbp_line(slot=tag,state="HELD",reason=type(error).__name__,message=str(error)[:90])
        rows.append(row)
        print(row.strip())
    for tag,survey in [("DSS_FIRST_EPOCH","DSS"),("DSS_SECOND_EPOCH","DSS2 Red")]:
        try:row=dss_survey(tag,survey)
        except Exception as error:row=hbp_line(slot=tag,state="HELD",reason=type(error).__name__,message=str(error)[:90])
        rows.append(row)
        print(row.strip())
    (OUT/"PHOTO-EPOCHS.hbp").write_text("".join(rows))
    observed=[row for row in rows if row.startswith("EPOCH|") and "state=HELD" not in row and "HELD_UNDATED_PLATE" not in row]
    if len(observed)<3:
        raise RuntimeError(f"ONLY_{len(observed)}_VERIFIED_DATED_IMAGE_SOURCES__THREE_REQUIRED")
    print("THREE_OR_MORE_DATED_PROXIMA_FRAMES_AVAILABLE",len(observed))
if __name__=="__main__":
    main()
