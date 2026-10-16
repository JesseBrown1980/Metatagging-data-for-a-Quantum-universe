//! Seat 1: MetaTag → Q-PRISM → Constellation → GitRAM, Rust 1.81 integer-only.
//! Uses original upstream Asolaria tribit crate, pinned at checkout in Actions.
//! Hot path: .hbp manifest, .hbi 3,078-byte seed, .bin exact source; NEVER JSON.
//! Digital replay is not an optical measurement or detection of a new planet.
#![forbid(unsafe_code)]
use asolaria_tribit::{seed, sha256, verify_chain, Zero, SEED_LEN};
use std::{collections::BTreeMap, env, fs, path::Path};

const SOURCE_SHA: &str = "027cff5c10b541608b727abada2af531037223edec3bb9112fcbb45fc333e474";
const SCHEMA: &str = "ASOLARIA-METATAG-QPRISM-GITRAM-RUST81-V1";
const RECORDS: usize = 722;
const RECORD_SIZE: usize = 121;
const SHARDS: usize = 9;
const TRITS: usize = 27;
const OMEGA_EXPECTED: &str = "d11121b8143ad25f3e00972a9c28e89b4923b5a8f817477a0aaed56e6b6e9c66";

fn hex(source: &[u8]) -> String {
    const H: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(source.len() * 2);
    for &b in source {
        out.push(char::from(H[usize::from(b >> 4)]));
        out.push(char::from(H[usize::from(b & 15)]));
    }
    out
}
fn digest(src: &[u8]) -> String { hex(&sha256(src)) }
fn get_number(v: &[u8]) -> Result<i64, String> {
    let s = std::str::from_utf8(v).map_err(|e| e.to_string())?.trim();
    if s.is_empty() { return Err("empty fixed decimal".into()); }
    let (sign, abs) = if let Some(rest) = s.strip_prefix('-') { (-1i64,rest) } else { (1i64,s) };
    let (whole, frac) = abs.split_once('.').ok_or("missing decimal")?;
    if frac.len() > 3 { return Err("fractional timestamp precision exceeds 3".into()); }
    let major: i64 = whole.parse().map_err(|_| "bad whole decimal")?;
    let minor: i64 = frac.parse().map_err(|_| "bad fractional decimal")?;
    let factor = 10i64.pow((3-frac.len()) as u32);
    (major.checked_mul(1000)
        .and_then(|x|x.checked_add(minor*factor))
        .and_then(|x|x.checked_mul(sign))).ok_or_else(||"decimal overflow".into())
}
fn ensure_source(raw: &[u8]) -> Result<(), String> {
    if raw.len() != RECORDS * RECORD_SIZE { return Err("WRONG_SOURCE_LENGTH".into()); }
    if digest(raw) != SOURCE_SHA { return Err("WRONG_PUBLISHED_SOURCE_SHA".into()); }
    for row in raw.chunks_exact(RECORD_SIZE) {
        if row[120]!=b'\n' || !row[..120].is_ascii() { return Err("INVALID_FIXED_WIDTH_SOURCE".into()); }
        let stamp = get_number(&row[1..10])?;
        let radial = get_number(&row[16..21])?;
        let instrument = row[119];
        if !instrument.is_ascii_digit() || instrument>b'5' { return Err("BAD_INSTRUMENT".into()); }
        let trits = [
            Zero::from_digit(stamp.rem_euclid(3) as u8),
            Zero::from_digit(radial.rem_euclid(3) as u8),
            Zero::from_digit((instrument-b'0')%3)
        ];
        // Order-three lighthouse, not a guessed spatial rotation.
        for z in trits {
            if z.rotate().rotate().rotate()!=z || z.rotate()==z.anti_rotate() {
                return Err("BAD_ASOLARIA_R3".into());
            }
        }
    }
    Ok(())
}
fn transcode_256_to_1024(src: &[u8]) -> Vec<u16> {
    let mut bits=0u32;
    let mut n=0u8;
    let mut out=Vec::new();
    for &b in src {
        bits = (bits<<8) | u32::from(b);
        n+=8;
        while n>=10 {
            n-=10;
            out.push(((bits>>n)&1023) as u16);
        }
    }
    if n>0 { out.push(((bits<<(10-n))&1023) as u16); }
    out
}
fn transcode_1024_to_256(src: &[u16], nbytes: usize) -> Result<Vec<u8>,String> {
    let mut bits=0u32;
    let mut n=0u8;
    let mut out=Vec::new();
    for &part in src {
        if part>=1024 { return Err("BAD_QPRISM_GLYPH".into()); }
        bits=(bits<<10)|u32::from(part);
        n+=10;
        while n>=8 {
            n-=8;
            out.push(((bits>>n)&255) as u8);
        }
    }
    if out.len()<nbytes { return Err("QPRISM_TOO_SHORT".into()); }
    out.truncate(nbytes);
    Ok(out)
}
fn qprism_test(src: &[u8]) -> Result<usize,String> {
    let glyphs=transcode_256_to_1024(src);
    let restored=transcode_1024_to_256(&glyphs,src.len())?;
    if restored!=src { return Err("QPRISM_RTT_BYTE_FAIL".into()); }
    Ok(glyphs.len())
}
fn shard_bounds(i: usize) -> Result<(usize,usize),String> {
    if i>=SHARDS { return Err("OUT_OF_RANGE_CELL".into()); }
    Ok((RECORDS*i/SHARDS, RECORDS*(i+1)/SHARDS))
}
fn root_for_cell(i: usize, part: &[u8]) -> Result<String,String> {
    if i>=SHARDS || part.len()%RECORD_SIZE!=0 { return Err("INVALID_SHARD".into()); }
    let records=part.chunks_exact(RECORD_SIZE).collect::<Vec<_>>();
    let mut leaf_roots=Vec::with_capacity(TRITS);
    for lane in 0..TRITS {
        let mut data=b"ASOLARIA|LEAF|".to_vec();
        data.push(i as u8);
        data.push(lane as u8);
        let count=records.iter().enumerate().filter(|(j,_)|j%TRITS==lane).count();
        data.extend_from_slice(&(count as u32).to_be_bytes());
        for (j,row) in records.iter().enumerate() {
            if j%TRITS==lane { data.extend_from_slice(row); }
        }
        leaf_roots.push(digest(&data));
    }
    let mut kernels=Vec::new();
    for a in 0..3u8 {
        let mut branch_roots=Vec::new();
        for b in 0..3u8 {
            let mut bytes=b"ASOLARIA|BRANCH|".to_vec();
            bytes.extend_from_slice(&[i as u8,a,b]);
            let begin=9*usize::from(a)+3*usize::from(b);
            for k in 0..3 { bytes.extend_from_slice(leaf_roots[begin+k].as_bytes()); }
            branch_roots.push(digest(&bytes));
        }
        let mut bytes=b"ASOLARIA|KERNEL|".to_vec();
        bytes.extend_from_slice(&[i as u8,a]);
        for child in branch_roots { bytes.extend_from_slice(child.as_bytes()); }
        kernels.push(digest(&bytes));
    }
    let mut bytes=b"ASOLARIA|CELL|".to_vec();
    bytes.push(i as u8);
    for child in kernels { bytes.extend_from_slice(child.as_bytes()); }
    Ok(digest(&bytes))
}
fn host8(value: &str) -> String {
    let mut state=0xcbf29ce484222325u64;
    for b in value.as_bytes() { state=(state^u64::from(*b)).wrapping_mul(0x100000001b3); }
    format!("{state:016x}")
}
fn brown_hilbert(address: &str) -> Result<String,String> {
    let mut v=u64::from_str_radix(address,16).map_err(|e|e.to_string())?;
    let mut digits=[0u64;6];
    for i in (0..6).rev() { digits[i]=v%1024;v/=1024; }
    Ok(digits.iter().map(u64::to_string).collect::<Vec<_>>().join("."))
}
fn write_cell(root:&Path,i:usize,source:&[u8])->Result<String,String>{
    let (a,b)=shard_bounds(i)?;
    let data=&source[a*RECORD_SIZE..b*RECORD_SIZE];
    let root_hash=root_for_cell(i,data)?;
    let id=host8(&format!("GitRAM:{i}:{root_hash}"));
    let glyphs=qprism_test(data)?;
    let seed_bytes=seed(data);
    if seed_bytes.len()!=SEED_LEN || !verify_chain(&seed_bytes) {
        return Err("ORIGINAL_ASOLARIA_SEED_CHAIN_FAILURE".into());
    }
    let filename=format!("cell-{i:02}");
    let receipt=format!(
        "GITRAM|json=0|schema={SCHEMA}|cell={i}|rows={}|source_bytes={}|source_sha256={}|omega_cell={}|seed_sha256={}|seed_bytes={}|qprism_glyphs={glyphs}|host8={id}|bh1024={}|leaves=27|R3=PASS|status=MEASURED_SOFTWARE\n",
        b-a,data.len(),digest(data),root_hash,digest(&seed_bytes),seed_bytes.len(),brown_hilbert(&id)?
    );
    fs::write(root.join(format!("{filename}.bin")),data).map_err(|e|e.to_string())?;
    fs::write(root.join(format!("{filename}.hbp")),receipt).map_err(|e|e.to_string())?;
    fs::write(root.join(format!("{filename}.hbi")),seed_bytes).map_err(|e|e.to_string())?;
    Ok(root_hash)
}
fn get_fields(data: &str) -> Result<BTreeMap<&str,&str>,String> {
    let mut parts=data.trim_end_matches('\n').split('|');
    if parts.next()!=Some("GITRAM") { return Err("NOT_A_GITRAM_RECEIPT".into()); }
    let mut kv=BTreeMap::new();
    for field in parts {
        let (k,v)=field.split_once('=').ok_or("BAD_HBP_TOKEN")?;
        if kv.insert(k,v).is_some() {return Err("DUPLICATED_HBP_FIELD".into());}
    }
    if kv.get("json")!=Some(&"0") || kv.get("schema")!=Some(&SCHEMA) {
        return Err("BAD_HBP_SCHEMA".into());
    }
    Ok(kv)
}
fn read_cell(root:&Path,i:usize,original:&[u8]) -> Result<String,String> {
    let name=format!("cell-{i:02}");
    let metadata=fs::read_to_string(root.join(format!("{name}.hbp"))).map_err(|e|e.to_string())?;
    let fields=get_fields(&metadata)?;
    if fields.get("cell")!=Some(&i.to_string().as_str()) {return Err("REPLAYED_OR_MISPLACED_CELL".into());}
    let bytes=fs::read(root.join(format!("{name}.bin"))).map_err(|e|e.to_string())?;
    let seed_bytes=fs::read(root.join(format!("{name}.hbi"))).map_err(|e|e.to_string())?;
    let (a,b)=shard_bounds(i)?;
    let expected=&original[a*RECORD_SIZE..b*RECORD_SIZE];
    if bytes!=expected {return Err("INCORRECT_OR_REPLAYED_SOURCE_BYTES".into());}
    if fields.get("rows")!=Some(&(b-a).to_string().as_str())
        || fields.get("source_bytes")!=Some(&bytes.len().to_string().as_str())
        || fields.get("source_sha256")!=Some(&digest(&bytes).as_str()) {
        return Err("FALSE_CELL_METADATA".into());
    }
    let root_hash=root_for_cell(i,&bytes)?;
    if fields.get("omega_cell")!=Some(&root_hash.as_str()) {return Err("CELL_ROOT_MISMATCH".into());}
    if seed_bytes!=seed(&bytes) || !verify_chain(&seed_bytes)
        || fields.get("seed_sha256")!=Some(&digest(&seed_bytes).as_str())
        || fields.get("seed_bytes")!=Some(&SEED_LEN.to_string().as_str()) {
        return Err("CORRUPT_NATIVE_ASOLARIA_SEED".into());
    }
    let glyphs=qprism_test(&bytes)?;
    if fields.get("qprism_glyphs")!=Some(&glyphs.to_string().as_str())
        || fields.get("leaves")!=Some(&"27") || fields.get("R3")!=Some(&"PASS") {
        return Err("QPRISM_OR_R3_RECEIPT_INVALID".into());
    }
    let id=host8(&format!("GitRAM:{i}:{root_hash}"));
    if fields.get("host8")!=Some(&id.as_str())
        || fields.get("bh1024")!=Some(&brown_hilbert(&id)?.as_str()){
        return Err("ADDRESS_MISMATCH".into());
    }
    Ok(root_hash)
}
fn fanin(root:&Path,original:&[u8],destination:&Path) -> Result<String,String> {
    let mut roots=Vec::with_capacity(SHARDS);
    for i in 0..SHARDS { roots.push(read_cell(root,i,original)?); }
    // If an unexpected extra shard appears, hold instead of quietly omitting it.
    for path in fs::read_dir(root).map_err(|e|e.to_string())? {
        let item=path.map_err(|e|e.to_string())?;
        if let Some(name)=item.file_name().to_str() {
            if name.starts_with("cell-") && name.ends_with(".hbp") {
                let accepted=(0..SHARDS).any(|i|name==format!("cell-{i:02}.hbp"));
                if !accepted{return Err("UNEXPECTED_EXTRA_GITRAM_SHARD".into());}
            }
        }
    }
    let mut material=b"ASOLARIA|OMEGA9|".to_vec();
    for root in &roots { material.extend_from_slice(root.as_bytes()); }
    let omega=digest(&material);
    if omega!=OMEGA_EXPECTED {return Err("OMEGA_REGRESSION".into());}
    let mut receipt=format!("OMEGA|json=0|schema={SCHEMA}|cells=9|source_rows=722|addressable_leaves=243|omega_sha256={omega}|source_sha256={SOURCE_SHA}|native_tribit=1|qprism_rtt=PASS|R3=PASS|held_fail_closed=1|claim=MEASURED_SOFTWARE\n");
    for (i,root) in roots.iter().enumerate() {
        receipt.push_str(&format!("CELL_ROOT|json=0|idx={i}|sha256={root}\n"));
    }
    fs::create_dir_all(destination).map_err(|e|e.to_string())?;
    fs::write(destination.join("GITRAM-OMEGA.hbp"),receipt).map_err(|e|e.to_string())?;
    println!("GITRAM_OMEGA_PASS|json=0|cells=9|omega={omega}|rust=1.81|original_seed=PASS");
    Ok(omega)
}
fn run()->Result<(),String>{
    let args=env::args().collect::<Vec<_>>();
    let mut source=None;
    let mut out=None;
    let mut cell=None;
    let mut cells_dir=None;
    let mut seal=false;
    let mut i=1usize;
    while i<args.len() {
        match args[i].as_str() {
            "--source" | "--out" | "--cell" | "--cells-dir" => {
                let option=args[i].as_str();
                i+=1;
                let value=args.get(i).ok_or("MISSING_ARGUMENT")?;
                match option {
                    "--source"=>source=Some(value.to_owned()),
                    "--out"=>out=Some(value.to_owned()),
                    "--cell"=>cell=Some(value.parse::<usize>().map_err(|_|"INVALID_CELL_NUMBER")?),
                    "--cells-dir"=>cells_dir=Some(value.to_owned()),
                    _=>unreachable!()
                }
            }
            "--fanin"=>seal=true,
            _=>return Err("UNKNOWN_ARGUMENT".into())
        }
        i+=1;
    }
    let source=fs::read(source.ok_or("MISSING_SOURCE")?).map_err(|e|e.to_string())?;
    ensure_source(&source)?;
    let dir=out.ok_or("MISSING_OUT")?;
    let destination=Path::new(&dir);
    fs::create_dir_all(destination).map_err(|e|e.to_string())?;
    match (cell,seal) {
        (Some(idx),false)=>{
            let root=write_cell(destination,idx,&source)?;
            println!("GITRAM_SHARD_PASS|json=0|cell={idx}|root={root}|rust=1.81");
        }
        (None,true)=>{
            let cell_path=cells_dir.ok_or("MISSING_CELLS_DIR")?;
            fanin(Path::new(&cell_path),&source,destination)?;
        }
        (None,false)=>{
            for idx in 0..SHARDS { write_cell(destination,idx,&source)?; }
            fanin(destination,&source,destination)?;
        }
        _=>return Err("CANNOT_SEAL_IN_SINGLE_CELL_MODE".into())
    }
    Ok(())
}
fn main(){
    if let Err(error)=run(){
        eprintln!("SEAT1_HELD|json=0|error={error}");
        std::process::exit(1);
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn upstream_three_zeros_rotate(){
        for d in 0..3 {
            let z=Zero::from_digit(d);
            assert_eq!(z.rotate().rotate().rotate(),z);
            assert_ne!(z.rotate(),z.anti_rotate());
        }
    }
    #[test] fn qprism_round_trip_all_byte_patterns(){
        for n in [0,1,2,3,4,5,9,27,81,256,3200] {
            let data=(0..n).map(|x|(x%256) as u8).collect::<Vec<_>>();
            assert_eq!(qprism_test(&data),Ok((n*8).div_ceil(10)));
        }
        assert!(transcode_1024_to_256(&[1024],1).is_err());
    }
    #[test] fn sha256_known_vector_from_original_asolaria(){
        assert_eq!(digest(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    }
    #[test] fn balanced_fixed_decimal(){
        assert_eq!(get_number(b"  -3.41 "),Ok(-3410));
        assert_eq!(get_number(b"1634.731"),Ok(1634731));
    }
    #[test] fn no_loss_seed_3078(){
        let data=(0..81u8).collect::<Vec<_>>();
        let receipt=seed(&data);
        assert_eq!(receipt.len(),SEED_LEN);
        assert!(verify_chain(&receipt));
    }
}
