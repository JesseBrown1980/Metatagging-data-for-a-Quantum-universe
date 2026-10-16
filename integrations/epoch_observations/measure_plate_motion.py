#!/usr/bin/env python3
"""Seat1 independent observational referee of real Proxima archival plates.
Original source BYTES and FITS plate/date must match exactly. Never trains.
All output is HBP; this is an independent camera-data audit, not the Rust core.
No generated zoom information and no exoplanet detection is implied.
"""
import argparse
import hashlib
import math
import statistics
import struct
from pathlib import Path

ROOT_RA=217.428942
ROOT_DEC=-62.67949
COS_DEC=math.cos(math.radians(ROOT_DEC))
SOURCES=(
 ("DSS_PLATE_25.fits","2b880f60928cf9f3c14356edf0ad6346b21cc09cfeafc01eeab8f65194806746","0025","S134","1976-03-11T18:13",123,167),
 ("DSS_PLATE_A29M.fits","a78a34ea58d4a1235d6820eb093c2e5ccb421498efdfe16efc3a8266ed8f5798","A29M","GR134","1997-03-11T17:19",286,295)
)
def sha(b):
    return hashlib.sha256(b).hexdigest()

def plate(parent,source):
    name,expected,plate_id,region,when,x0,y0=source
    raw=(parent/name).read_bytes()
    if sha(raw)!=expected:raise ValueError("FISCHER_SOURCE_SHA_HELD")
    fields={}
    for idx in range(0,len(raw),80):
        line=raw[idx:idx+80].decode("ascii","replace")
        key=line[:8].strip()
        if key=="END":
            start=((idx+80+2879)//2880)*2880
            break
        if line[8:10]=="= ":
            fields[key]=line[10:].split("/")[0].strip().strip("'")
    else: raise ValueError("FITS_MISSING_END")
    if (fields.get("BITPIX")!="16" or fields.get("PLATEID","").strip()!=plate_id
            or fields.get("REGION","").strip()!=region
            or not fields.get("DATE-OBS","").startswith(when)):
        raise ValueError("FISCHER_PLATE_ID_OR_ORIGINAL_DATE_HELD")
    w=int(fields["NAXIS1"]);h=int(fields["NAXIS2"])
    data=raw[start:start+w*h*2]
    if len(data)!=w*h*2:raise ValueError("FITS_TRUNCATED")
    samples=[x[0] for x in struct.iter_unpack(">h",data)]
    return raw,fields,(w,h,samples)

def location(x,y,fields):
    dx=x+1-float(fields["CRPIX1"])
    dy=y+1-float(fields["CRPIX2"])
    east=(float(fields["CD1_1"])*dx+float(fields["CD1_2"])*dy)*3600
    east+=(float(fields["CRVAL1"])-ROOT_RA)*COS_DEC*3600
    north=(float(fields["CD2_1"])*dx+float(fields["CD2_2"])*dy)*3600
    north+=(float(fields["CRVAL2"])-ROOT_DEC)*3600
    return east,north

def center(frame,guess,radius):
    w,h,readings=frame
    cx,cy=guess
    values=[(x,y,(x-cx)**2+(y-cy)**2,readings[y*w+x])
            for y in range(cy-17,cy+18)
            for x in range(cx-17,cx+18)]
    bg=statistics.median(v for _,_,r2,v in values if 100<r2<289)
    samples=[(x,y,max(v-bg,0)) for x,y,r2,v in values if r2<=radius*radius]
    total=sum(weight for _,_,weight in samples)
    if total<=0:raise ValueError("FISCHER_NO_STAR_SIGNAL_HELD")
    return sum(x*v for x,_,v in samples)/total,sum(y*v for _,y,v in samples)/total

def run(root,out):
    frames=[plate(root,p) for p in SOURCES]
    radius_rows=[]
    chosen=[]
    for radius in (4,5,6,7,8):
        xy=[]
        for desc,(_,h,frame) in zip(SOURCES,frames):
            px,py=center(frame,(desc[5],desc[6]),radius)
            xy.append((*location(px,py,h),px,py))
        de=xy[1][0]-xy[0][0]
        dn=xy[1][1]-xy[0][1]
        norm=math.hypot(de,dn)
        radius_rows.append((radius,de,dn,norm))
        if radius==6:chosen=xy
    _,de,dn,norm=radius_rows[2]
    pm_e=-3781.741*21/1000
    pm_n=769.465*21/1000
    residual=math.hypot(de-pm_e,dn-pm_n)
    if not 65<norm<95 or residual>3:raise ValueError("FISCHER_ASTROMETRIC_MISMATCH_HELD")
    if any(abs(v[3]-norm)>3 for v in radius_rows):
        raise ValueError("FISCHER_RADIUS_SENSITIVITY_HELD")
    if math.hypot(de+pm_e,dn+pm_n)<=residual:
        raise ValueError("FISCHER_CHRONOLOGY_REPLAY_HELD")
    for source,(raw,*_) in zip(SOURCES,frames):
        tampered=bytearray(raw);tampered[2880]^=1
        if sha(tampered)==source[1]:raise ValueError("FISCHER_MUTATION_WAS_NOT_HELD")
        forged=list(source)
        forged[2]="FORGED_ID"
        try:
            plate(root,forged)
        except ValueError:
            pass
        else:
            raise ValueError("FISCHER_FORGED_PLATE_WAS_ACCEPTED")
    lines=["HBP1|schema=ASOLARIA-SEAT1-REAL-PROXIMA-IMAGE-MOTION-V1|json=0|date=2026-10-16|trained=NO|source=REAL_PLATE_PIXELS\n"]
    for source,(_,h,frame),point in zip(SOURCES,frames,chosen):
        w,height,_=frame
        east,north,px,py=point
        lines.append(f"SOURCE|json=0|file={source[0]}|original_sha256={source[1]}|plate={source[2]}|region={source[3]}|observed_utc={source[4]}|width={w}|height={height}|original_format=FITS_BITPIX16|filter={h.get('FILTER','NOT_IN_HEADER')}|pixel_invention=NO\n")
        lines.append(f"CENTROID|json=0|plate={source[2]}|radius_px=6|x={px:.6f}|y={py:.6f}|east_arcsec={east:.6f}|north_arcsec={north:.6f}|coords=WCS_CD_TANGENT_APPROX\n")
    for radius,e,n,v in radius_rows:
        lines.append(f"CONTROL|json=0|aperture_radius_px={radius}|east_delta_arcsec={e:.6f}|north_delta_arcsec={n:.6f}|separation_arcsec={v:.6f}\n")
    lines.append(f"MOTION|json=0|baseline_years=21|delta_east_arcsec={de:.6f}|delta_north_arcsec={dn:.6f}|total_arcsec={norm:.6f}|rate_arcsec_per_year={norm/21:.6f}|catalog_predicted_east_arcsec={pm_e:.6f}|catalog_predicted_north_arcsec={pm_n:.6f}|difference_to_catalog_arcsec={residual:.6f}|known_star=PROXIMA_CENTAURI\n")
    lines.append("FISCHER|json=0|corrupted_fits=HELD|wrong_plate_id=HELD|reversed_date=HELD|five_aperture_radii=PASS|source_hash_verified=PASS\n")
    lines.append("BOUNDARY|json=0|source_image_rv_not_interchangeable=TRUE|physical_star_proper_motion=OBSERVED|new_planet=NOT_DETECTED|image_zoom_generates_new_photons=FALSE|camera_filters_identical=FALSE|trained_model=NONE\n")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("".join(lines))
    print("REAL_PROXIMA_IMAGE_MOTION_PASS",f"arcsec={norm:.6f}",f"per_year={norm/21:.6f}",f"catalog_residual={residual:.6f}")
    print("MOTION_HBP_SHA256",sha(out.read_bytes()))
if __name__=="__main__":
    pa=argparse.ArgumentParser()
    pa.add_argument("--source",required=True)
    pa.add_argument("--out",required=True)
    x=pa.parse_args()
    run(Path(x.source),Path(x.out))
