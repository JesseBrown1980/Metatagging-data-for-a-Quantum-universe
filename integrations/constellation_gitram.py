#!/usr/bin/env python3
"""Asolaria MetaTag + Q-PRISM + 3x3x3 constellation + GitRAM public source lane.
Integer-only, stdlib-only. A source-bound digital test; NOT a quantum/optical detector.
Source: CDS J/A+A/700/A11/spec.dat; 722 real radial-velocity records.
GitRAM: 9 independent source-pinned shard checkpoints -> all-or-nothing Omega.
"""
import argparse,base64,hashlib,json,zlib
from collections import Counter
from decimal import Decimal
from pathlib import Path

SOURCE_SHA="027cff5c10b541608b727abada2af531037223edec3bb9112fcbb45fc333e474"
SOURCE_URL="https://cdsarc.cds.unistra.fr/ftp/J/A+A/700/A11/spec.dat"
SCHEMA="ASOLARIA-METATAG-QPRISM-CONSTELLATION-GITRAM-V1"
RAINBOW=("violet","indigo","blue","green","yellow","orange","red")
def sha(b):return hashlib.sha256(b).hexdigest()
def row_records(data):
    rows=[]
    for i,line in enumerate(data.splitlines(keepends=True)):
        parts=line.split()
        if len(parts)!=11:raise ValueError("invalid source row")
        t=int(Decimal(parts[0].decode())*1000)
        rv=int(Decimal(parts[1].decode())*1000)
        err=int(Decimal(parts[2].decode())*1000)
        inst=int(parts[-1])
        if err<=0 or not 0<=inst<=5:raise ValueError("invalid measurement")
        rows.append((i,line,t,rv,err,inst))
    return rows
def hbp(tag,**fields):
    return "|".join([tag,"json=0"]+[str(k)+"="+str(v) for k,v in fields.items()])+"\n"
def fnv64(s):
    v=0xcbf29ce484222325
    for b in s.encode():v=((v^b)*0x100000001b3)&((1<<64)-1)
    return format(v,"016x")
def bh1024(h):
    n=int(h,16);digits=[]
    for i in range(6):digits.insert(0,n%1024);n//=1024
    return ".".join(map(str,digits))
def qprism256(data):
    bits=left=0;symbols=[]
    for b in data:
        bits=(bits<<8)|b;left+=8
        while left>=10:
            left-=10;symbols.append((bits>>left)&1023)
    if left:symbols.append((bits<<(10-left))&1023)
    return symbols
def qprism1024(symbols,nbytes):
    bits=left=0;out=bytearray()
    for s in symbols:
        if not 0<=s<1024:raise ValueError("bad glyph")
        bits=(bits<<10)|s;left+=10
        while left>=8:
            left-=8;out.append((bits>>left)&255)
    return bytes(out[:nbytes])
def trits(row):
    _,_,t,rv,_,inst=row
    return ((t//1000)%3,rv%3,inst%3)
def rotate(v,n):return tuple((c+n)%3 for c in v)
def cell_root(i,rows):
    leaf=[]
    for j in range(27):
        group=[r for k,r in enumerate(rows) if k%27==j]
        raw=b"".join(r[1] for r in group)
        leaf.append(sha(b"ASOLARIA|LEAF|"+bytes([i,j])+len(group).to_bytes(4,"big")+raw))
    outer=[]
    for j in range(3):
        inner=[]
        for k in range(3):
            p=j*9+k*3
            inner.append(sha(b"ASOLARIA|BRANCH|"+bytes([i,j,k])+"".join(leaf[p:p+3]).encode()))
        outer.append(sha(b"ASOLARIA|KERNEL|"+bytes([i,j])+"".join(inner).encode()))
    return sha(b"ASOLARIA|CELL|"+bytes([i])+"".join(outer).encode())
def make_cell(i,rows):
    raw=b"".join(r[1] for r in rows)
    compressed=zlib.compress(raw,9)
    root=cell_root(i,rows)
    handle=fnv64("GitRAM:"+str(i)+":"+root)
    header=hbp("GITRAM",schema=SCHEMA,cell=i,rows=len(rows),byte_count=len(raw),
               source_sha=sha(raw),zlib_sha=sha(compressed),omega_cell=root,
               host8=handle,bh1024=bh1024(handle),
               qprism_1024_glyphs=len(qprism256(bytes.fromhex(root))),leaves27=27)
    body=hbp("SOURCE",cell=i,encoding="zlib-base64",
             payload=base64.b64encode(compressed).decode())
    return (header+body).encode()
def parse_cell(data,i):
    lines=data.decode("ascii").splitlines()
    if len(lines)!=2:raise ValueError("bad cell line count")
    def fields(line):
        v=line.split("|");out={}
        for part in v[1:]:
            if "=" not in part:raise ValueError("bad HBP field")
            k,value=part.split("=",1)
            if k in out:raise ValueError("duplicate HBP field")
            out[k]=value
        return v[0],out
    a,h=fields(lines[0]);b,p=fields(lines[1])
    if a!="GITRAM" or b!="SOURCE" or h.get("schema")!=SCHEMA or int(h["cell"])!=i or int(p["cell"])!=i:
        raise ValueError("WRONG_CELL_OR_SCHEMA")
    packed=base64.b64decode(p["payload"],validate=True)
    if sha(packed)!=h["zlib_sha"]:raise ValueError("TAMPERED_PACKED")
    raw=zlib.decompress(packed)
    if len(raw)!=int(h["byte_count"]) or sha(raw)!=h["source_sha"]:raise ValueError("TAMPERED_RAW")
    rows=row_records(raw)
    if len(rows)!=int(h["rows"]) or cell_root(i,rows)!=h["omega_cell"]:raise ValueError("TAMPERED_MERKLE")
    return raw,h["omega_cell"],rows
def fanin(cells):
    if set(cells)!=set(range(9)):raise ValueError("HELD_MISSING_GITRAM_SHARD")
    chunks=[];roots=[]
    for i in range(9):
        raw,root,rows=parse_cell(cells[i],i)
        chunks.append(raw);roots.append(root)
        if qprism1024(qprism256(raw),len(raw))!=raw:raise ValueError("QPRISM_LOSS")
        for row in rows:
            t=trits(row)
            if rotate(t,3)!=t or rotate(rotate(t,1),2)!=t:raise ValueError("R3_NOT_ID")
    raw=b"".join(chunks)
    if sha(raw)!=SOURCE_SHA:raise ValueError("SOURCE_MISMATCH")
    return raw,sha(b"ASOLARIA|OMEGA9|"+"".join(roots).encode()),roots
def source_rows(path):
    raw=Path(path).read_bytes()
    if sha(raw)!=SOURCE_SHA:raise ValueError("SOURCE_SHA_MISMATCH")
    rows=row_records(raw)
    if len(rows)!=722:raise ValueError("SOURCE_ROW_COUNT_MISMATCH")
    return raw,rows
def all_windows(rows):
    ordered=sorted(rows,key=lambda r:(r[2],r[0]))
    out=[]
    for i in range(9):
        batch=ordered[i*722//9:(i+1)*722//9]
        weight=[10**9//(r[4]*r[4]) for r in batch]
        avg=sum(w*r[3] for w,r in zip(weight,batch))//sum(weight)
        out.append([i,len(batch),batch[len(batch)//2][2],avg])
    return out
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--source",required=True);a.add_argument("--out",required=True)
    a.add_argument("--cell",type=int);a.add_argument("--fanin",action="store_true")
    a.add_argument("--cells-dir")
    x=a.parse_args();raw,rows=source_rows(x.source)
    output=Path(x.out);output.mkdir(parents=True,exist_ok=True)
    if x.cell is not None:
        i=x.cell
        if i not in range(9):raise ValueError("cell outside 0..8")
        shard=rows[i*722//9:(i+1)*722//9]
        data=make_cell(i,shard)
        target=output/("cell-%02d.hbp"%i);target.write_bytes(data)
        _,root,_=parse_cell(data,i)
        print(hbp("GITRAM_SHARD_PASS",cell=i,rows=len(shard),omega_cell=root,sha256=sha(data)).strip())
    elif x.fanin:
        if not x.cells_dir:raise ValueError("missing --cells-dir")
        cells={i:(Path(x.cells_dir)/("cell-%02d.hbp"%i)).read_bytes() for i in range(9)}
        rebuilt,omega,roots=fanin(cells)
        if rebuilt!=raw:raise ValueError("SOURCE_BYTE_PARITY_FAILED")
        (output/"GITRAM-OMEGA.hbp").write_text(hbp("GITRAM_OMEGA_PASS",cells=9,rows=722,omega=omega,source_sha256=sha(raw)))
        print(hbp("GITRAM_OMEGA_PASS",cells=9,rows=722,omega=omega).strip())
    else:
        cells={}
        for i in range(9):
            cells[i]=make_cell(i,rows[i*722//9:(i+1)*722//9])
            (output/("cell-%02d.hbp"%i)).write_bytes(cells[i])
        rebuilt,omega,roots=fanin(cells)
        counts=Counter(RAINBOW[max(0,min(6,(r[3]+8000)//2500))] for r in rows)
        report={"schema":SCHEMA,"source_sha256":sha(raw),"rows":722,"cells":9,"leaves":243,
                "omega9":omega,"roots":roots,"rainbow_velocity_class_counts":dict(counts),
                "windows":all_windows(rows),"measured_spectral_bands":False,
                "physical_optical_measurement":"NOT_RUN","source_measurement":"CDS_REAL_RV",
                "rust181_clippy":"NOT_RUN_BY_THIS_PYTHON_JOB","recovered_exact":rebuilt==raw}
        (output/"CONSTELLATION-REPORT.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
        print(hbp("CONSTELLATION_PASS",omega=omega,rows=722,cells=9).strip())
if __name__=="__main__":main()
