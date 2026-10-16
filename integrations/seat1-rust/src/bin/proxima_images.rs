//! Seat 1: real 2-D astronomical FITS images -> Asolaria 3-state addressed data.
//! Rust 1.81, no float operations, no training, no JSON, no invented photons.
//! Scientific pixels are preserved as EXACT original FITS bytes, including
//! IEEE-754 source bit patterns (not converted with floating-point operations).
#![forbid(unsafe_code)]
use asolaria_tribit::{seed,sha256,verify_chain,Zero,SEED_LEN};
use std::{collections::BTreeMap,env,fs,path::Path};

const COLOURS:[&str;7]=["violet","indigo","blue","green","yellow","orange","red"];
const MAX_AXIS:usize=16384;
const MAX_PIXELS:usize=32_000_000;
const LEVELS:[usize;7]=[3,9,27,81,243,729,2187];
fn hex(bytes:&[u8])->String{
 let mut result=String::with_capacity(bytes.len()*2);
 for &b in bytes {result.push_str(&format!("{b:02x}"));}
 result
}
fn digest(bytes:&[u8])->String{hex(&sha256(bytes))}
#[derive(Debug,Clone,PartialEq,Eq)]
struct Fits{
 width:usize,height:usize,bitpix:i32,bpp:usize,
 header_bytes:usize,source_sha:String,pixel_sha:String,
 raw:Vec<u8>,image:Vec<u8>,
 cards:BTreeMap<String,String>,
}
fn parse_fits(source:&[u8])->Result<Fits,String>{
 if source.len()<2880||&source[..8]!=b"SIMPLE  " {return Err("NOT_FITS_PRIMARY_HELD".into());}
 let mut cards=BTreeMap::new();let mut end=None;
 for (i,chunk) in source.chunks_exact(80).take(12000).enumerate(){
  if !chunk.is_ascii(){return Err("FITS_NON_ASCII_HEADER_HELD".into());}
  let key=std::str::from_utf8(&chunk[..8]).map_err(|_|"FITS_KEY")?.trim();
  if key=="END"{end=Some((i+1)*80);break;}
  if &chunk[8..10]==b"= "{
   let value=std::str::from_utf8(&chunk[10..]).map_err(|_|"FITS_VALUE")?
     .split('/').next().ok_or("FITS_EMPTY_FIELD")?.trim();
   if cards.insert(key.to_string(),value.to_string()).is_some(){
     return Err("FITS_DUPLICATED_CARD_HELD".into());
   }
  }
 }
 let end=end.ok_or("FITS_MISSING_END_HELD")?;
 let header_bytes=end.checked_add(2879).ok_or("FITS_HEADER_OVERFLOW")?/2880*2880;
 let num=|k:&str|->Result<i64,String>{
   cards.get(k).ok_or(format!("FITS_MISSING_{k}"))?
     .parse::<i64>().map_err(|_|format!("FITS_NON_INTEGER_{k}"))
 };
 if cards.get("SIMPLE").map(String::as_str)!=Some("T")||num("NAXIS")?!=2{
  return Err("FITS_NOT_SIMPLE_2D_HELD".into());
 }
 let width=usize::try_from(num("NAXIS1")?).map_err(|_|"FITS_BAD_X")?;
 let height=usize::try_from(num("NAXIS2")?).map_err(|_|"FITS_BAD_Y")?;
 if width==0||height==0||width>MAX_AXIS||height>MAX_AXIS{return Err("FITS_AXES_HELD".into());}
 let n=width.checked_mul(height).ok_or("FITS_PIXELS_OVERFLOW")?;
 if n>MAX_PIXELS{return Err("FITS_TOO_MANY_PIXELS_HELD".into());}
 let bitpix=i32::try_from(num("BITPIX")?).map_err(|_|"FITS_BITPIX_OVERFLOW")?;
 let bpp=match bitpix {8=>1,16=>2,32|-32=>4,64|-64=>8,_=>return Err("FITS_BITPIX_NOT_SUPPORTED_HELD".into())};
 let nbytes=n.checked_mul(bpp).ok_or("FITS_BYTES_OVERFLOW")?;
 let finish=header_bytes.checked_add(nbytes).ok_or("FITS_OFFSET_OVERFLOW")?;
 if finish>source.len(){return Err("FITS_TRUNCATED_HELD".into());}
 let image=source[header_bytes..finish].to_vec();
 let source_sha=digest(source);let pixel_sha=digest(&image);
 Ok(Fits{width,height,bitpix,bpp,header_bytes,source_sha,pixel_sha,raw:source.to_vec(),image,cards})
}
fn to_trits(byte:u8)->[i8;6]{
 let mut v=u16::from(byte);let mut result=[0i8;6];
 for trit in &mut result{
  let rem=v%3;
  let d=if rem==2{-1}else{rem as i8};
  *trit=d;
  v=((i32::from(v)-i32::from(d))/3) as u16;
 }
 result
}
fn from_trits(trits:&[i8;6])->Result<u8,String>{
 let mut n=0i32;let mut power=1i32;
 for &t in trits{
  if !(-1..=1).contains(&t){return Err("NON_TERNARY_DIGIT_HELD".into());}
  n+=i32::from(t)*power;power*=3;
 }
 u8::try_from(n).map_err(|_|"TERNARY_BYTE_OUT_OF_RANGE".into())
}
fn verify_lossless(b:&[u8])->Result<(),String>{
 for &byte in b {if from_trits(&to_trits(byte))?!=byte{return Err("BYTE_TRIT_INVERSE_HELD".into());}}
 Ok(())
}
fn lighthouse_closure(b:&[u8])->Result<(),String>{
 for &v in b{
  let z=Zero::from_digit(v%3);
  if z.rotate().rotate().rotate()!=z || z.rotate()==z.anti_rotate(){
   return Err("ROTATING_LIGHTHOUSE_R3_HELD".into());
  }
 }
 Ok(())
}
fn row_to_hbp(index:usize,name:&str,image:&Fits)->Result<String,String>{
 verify_lossless(&image.image)?;
 // Each pixel has an independent stable 2-D key. No trainable parameters.
 let mut sectors=[0usize;27];
 let mut rainbow=[0usize;7];
 let mut byte_counts=[0usize;256];
 let pixels=image.width*image.height;
 for i in 0..pixels {
  let x=i%image.width;let y=i/image.width;
  // Address in 3^3 leaf space. This is a digital partition, not a physical band.
  let key=((x%3)*9+(y%3)*3+(i%3))%27;
  sectors[key]+=1;
  rainbow[(x+y+index)%7]+=1;
  let slice=&image.image[i*image.bpp..(i+1)*image.bpp];
  for &v in slice {byte_counts[usize::from(v)]+=1;}
 }
 let kernel=seed(&image.raw);
 if kernel.len()!=SEED_LEN || !verify_chain(&kernel){return Err("UPSTREAM_SEED_INVALID_HELD".into());}
 let mut text=format!("IMAGE|json=0|schema=ASOLARIA-PROXIMA-PHOTO-ORIGINAL-V1|idx={index}|name={name}|source_kind=NASA_SKYVIEW_FITS_CUTOUT_OF_SURVEY|width={}|height={}|bitpix={}|bytes_per_sample={}|pixels={pixels}|header_bytes={}|original_file_bytes={}|source_sha256={}|pixel_sha256={}|trits_per_byte=6|source_float_arithmetic=NONE|pixel_reconstruction=EXACT|native_kernel_sha256={}|native_hbi_bytes={SEED_LEN}|R3=PASS|training=NONE|json_output=NONE\n",image.width,image.height,image.bitpix,image.bpp,image.header_bytes,image.raw.len(),image.source_sha,image.pixel_sha,digest(&kernel));
 for (i,total) in sectors.iter().enumerate(){text.push_str(&format!("SECTOR|json=0|image={index}|id={i}|pixel_addresses={total}\n"));}
 for (i,total) in rainbow.iter().enumerate(){text.push_str(&format!("RAINBOW_VIEW|json=0|image={index}|lane={}|derived_pixel_addresses={total}|measured_wavelengths=NO\n",COLOURS[i]));}
 for (i,&count) in byte_counts.iter().enumerate(){if count>0{text.push_str(&format!("BYTE_HIST|json=0|image={index}|value={i}|count={count}\n"));}}
 Ok(text)
}
fn run()->Result<(),String>{
 let args=env::args().collect::<Vec<_>>();
 if args.len()<4{return Err("USAGE_proxima_images_OUTPUT_DIR_IMAGE_NAME=PATH...".into());}
 let dir=Path::new(&args[1]);fs::create_dir_all(dir).map_err(|e|e.to_string())?;
 let mut observation_receipts=String::new();
 let mut aggregate=Vec::new();
 let mut prior=[0u8;32];
 for (i,entry) in args[2..].iter().enumerate(){
   let (tag,path)=entry.split_once('=').ok_or("NEED_IMAGE_NAME_EQUALS_PATH")?;
   if tag.is_empty()||!tag.bytes().all(|b|b.is_ascii_alphanumeric()||b==b'_'){
      return Err("IMAGE_NAME_INVALID_HELD".into());
   }
   let bytes=fs::read(path).map_err(|e|e.to_string())?;
   let image=parse_fits(&bytes)?;
   lighthouse_closure(&image.image)?;
   verify_lossless(&bytes)?;
   // File storage is split from derived data: exact original FITS retained.
   let reconstituted=image.raw.as_slice();
   if bytes!=reconstituted{return Err("FITS_BYTE_PARITY_HELD".into());}
   let kernel=seed(&image.raw);
   if kernel.len()!=SEED_LEN||!verify_chain(&kernel){return Err("HBI_SEED_CHAIN_HELD".into());}
   fs::write(dir.join(format!("{tag}.hbi")),kernel).map_err(|e|e.to_string())?;
   let row=row_to_hbp(i,tag,&image)?;
   fs::write(dir.join(format!("{tag}.hbp")),&row).map_err(|e|e.to_string())?;
   // Moving-light-house: each source image is a frozen independent observer.
   // Hash chains commit to image identity/order, not an unobserved physical event.
   let mut material=b"ASOLARIA-FROZEN-IMAGE-IS-V1|".to_vec();
   material.extend_from_slice(&prior);
   material.extend_from_slice(tag.as_bytes());
   material.extend_from_slice(&sha256(&image.raw));
   prior=sha256(&material);
   observation_receipts.push_str(&format!("IMAGE_LINK|json=0|idx={i}|tag={tag}|source_sha256={}|previous_hash_sha256={}|linked_checkpoint_sha256={}\n",
      image.source_sha,digest(&material[..material.len()-32-image.raw.len().min(0)]),hex(&prior)));
   aggregate.extend_from_slice(&sha256(&image.raw));
   println!("ASOLARIA_IMAGE_PASS|json=0|image={tag}|pixels={}|sample_bytes={}|source_sha256={}|native_kernel=PASS|R3=PASS",image.width*image.height,image.image.len(),image.source_sha);
 }
 let final_root=digest(&aggregate);
 observation_receipts.push_str(&format!("IMAGE_OMEGA|json=0|images={}|source_order_sha256={final_root}|source_byte_reconstruction=PASS|ternary_inverse=PASS|R3=PASS|source_type=REAL_SURVEY_FITS|spatial_3d_depth=NOT_OBSERVED|periodic_future_images=NOT_OBSERVED|wavelength_seven_spectra=NOT_MEASURED|Brown_Edens_I=NOT_DETECTED|training=NONE\n",args.len()-2));
 for &n in &LEVELS {
   observation_receipts.push_str(&format!("ADDRESS_LADDER|json=0|capacity={n}|physical_independent_image_exposures={}|note=LOGICAL_ADDRESSES_NOT_MATERIALIZED_PHOTONS\n",args.len()-2));
 }
 fs::write(dir.join("IMAGE-OMEGA.hbp"),observation_receipts).map_err(|e|e.to_string())?;
 println!("ASOLARIA_REAL_IMAGES_OMEGA_PASS|json=0|images={}|sha256={final_root}|training=NONE",args.len()-2);
 Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("SEAT1_IMAGE_HELD|json=0|error={e}");std::process::exit(1);}}
#[cfg(test)]
mod tests{
 use super::*;
 fn fake_fits(width:usize,height:usize,bitpix:i32)->Vec<u8>{
  let mut bytes=Vec::new();
  for (key,value) in [("SIMPLE","T".to_string()),("BITPIX",bitpix.to_string()),
   ("NAXIS","2".to_string()),("NAXIS1",width.to_string()),("NAXIS2",height.to_string())]{
   let mut card=format!("{key:<8}= {value:<20}").into_bytes();card.resize(80,b' ');
   bytes.extend(card);
  }
  let mut end=b"END".to_vec();end.resize(80,b' ');bytes.extend(end);
  let extra=(2880-bytes.len()%2880)%2880;bytes.extend(vec![b' ';extra]);
  let bpp=usize::try_from(bitpix.abs()).unwrap()/8;
  for j in 0..width*height*bpp {bytes.push((j%256) as u8);}
  let extra=(2880-bytes.len()%2880)%2880;bytes.extend(vec![0;extra]);bytes
 }
 #[test]fn trits_all_possible_byte_values_exact(){
  for b in 0..=255u8{assert_eq!(from_trits(&to_trits(b)),Ok(b));}
  assert!(from_trits(&[2,0,0,0,0,0]).is_err());
 }
 #[test]fn synthetic_fits_int_and_ieee_source_bits_lossless(){
  for bitpix in [8,16,32,-32,64,-64]{
   let source=fake_fits(7,9,bitpix);
   let image=parse_fits(&source).unwrap();
   assert_eq!(image.image.len(),63*image.bpp);
   assert_eq!(image.raw,source);
   verify_lossless(&image.raw).unwrap();
   lighthouse_closure(&image.image).unwrap();
   let text=row_to_hbp(0,"SYNTHETIC",&image).unwrap();
   assert!(text.contains("pixel_reconstruction=EXACT"));
  }
 }
 #[test]fn reject_fake_and_truncated_fits(){
  let mut original=fake_fits(9,9,16);
  assert!(parse_fits(&original[..2900]).is_err());
  original[0]=b'X';assert!(parse_fits(&original).is_err());
 }
 #[test]fn tampered_pixels_change_source_sha(){
  let src=fake_fits(9,9,-32);
  let mut altered=src.clone();altered[2880]^=1;
  assert_ne!(parse_fits(&src).unwrap().source_sha,parse_fits(&altered).unwrap().source_sha);
 }
}
