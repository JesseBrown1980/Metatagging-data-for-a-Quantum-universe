//! Milky Way context, not an invented observed photon or a simulated galaxy.
//! Rust 1.81 integer-only. All approximations explicitly marked as model inputs.
//! The photos provide measured Proper Motion; this is an independent bounding
//! calculation for the Galactic center (Sagittarius A*) and total MW potential.
#![forbid(unsafe_code)]
use asolaria_tribit::Zero;
use std::{env,fs,path::PathBuf};

// Approximate / deliberately conservative input constants, not fitted here:
const GM_SUN_SI:u128=132_712_440_018_000_000_000;
const SGR_A_SUN_MASSES:u128=4_300_000;
const PC_METERS:u128=30_856_775_814_913_673;
const GALACTIC_CENTER_DISTANCE_PC:u128=8_200;
const PROXIMA_DISTANCE_MILLI_PC:u128=1_300;
const LOCAL_CIRCULAR_V_M_S:u128=220_000;
const OBS_BASELINE_SECONDS:u128=662_709_600; // 21 Julian years.
const MICRO_ARCSEC_PER_RADIAN:u128=206_264_806_247;
const NANO_ARCSEC_PER_RADIAN:u128=206_264_806_247_096;

#[derive(Debug)]
struct Bound {
    radius_m:u128, distance_proxima_m:u128,
    gc_a_1e18:u128, galaxy_a_1e18:u128,
    sagittarius_a_shift_m:u128,galaxy_shift_m:u128,
    sagittarius_a_nas:u128,galaxy_nas:u128,
}
fn model()->Bound {
    let radius_m=GALACTIC_CENTER_DISTANCE_PC*PC_METERS;
    let distance_proxima_m=PROXIMA_DISTANCE_MILLI_PC*PC_METERS/1000;
    let mu=GM_SUN_SI*SGR_A_SUN_MASSES;
    // Carefully ordered divisions to avoid 128-bit overflow.
    // Truncation adds <= 1 unit to displayed roundoff, not hidden physics.
    let gc_a_1e18=(mu/radius_m)*1_000_000_000_000_000_000/radius_m;
    let galaxy_a_1e18=(LOCAL_CIRCULAR_V_M_S*LOCAL_CIRCULAR_V_M_S)
        *1_000_000_000_000_000_000/radius_m;
    let square=OBS_BASELINE_SECONDS*OBS_BASELINE_SECONDS;
    let sagittarius_a_shift_m=gc_a_1e18*square/(2*1_000_000_000_000_000_000);
    let galaxy_shift_m=galaxy_a_1e18*square/(2*1_000_000_000_000_000_000);
    let sagittarius_a_nas=sagittarius_a_shift_m*NANO_ARCSEC_PER_RADIAN/distance_proxima_m;
    let galaxy_nas=galaxy_shift_m*NANO_ARCSEC_PER_RADIAN/distance_proxima_m;
    Bound {radius_m,distance_proxima_m,gc_a_1e18,galaxy_a_1e18,
        sagittarius_a_shift_m,galaxy_shift_m,sagittarius_a_nas,galaxy_nas}
}
fn output() -> Result<String,String> {
    let b=model();
    for n in 0..3u8 {
        let z=Zero::from_digit(n);
        if z.rotate().rotate().rotate()!=z{return Err("ASOLARIA_TERNARY_R3_HELD".into());}
    }
    if b.sagittarius_a_shift_m==0||b.galaxy_shift_m<=b.sagittarius_a_shift_m{
        return Err("INCORRECT_GRAVITY_SCALING_HELD".into());
    }
    let mut text=String::new();
    text.push_str("HBP1|schema=ASOLARIA-SEAT1-GALACTIC-CENTER-CONTEXT-V1|json=0|rust=1.81|float_used=0|state=BOUNDED_MODEL\n");
    text.push_str("FRAME|json=0|source_photographs=REAL_1976_1997_DSS_AND_1996_2012_HST|motion_measurement=SEPARATE_OBSERVATION|galactic_center=SGR_A_STAR|frame=SOLAR_NEIGHBORHOOD\n");
    text.push_str(&format!("BH_INPUT|json=0|sgr_a_mass_solar_approx={SGR_A_SUN_MASSES}|distance_to_galactic_center_pc_approx={GALACTIC_CENTER_DISTANCE_PC}|galactic_radius_m={}|gm_sun_m3_s2={GM_SUN_SI}|method=POINT_MASS_NEWTONIAN_COMPARISON_ONLY\n",b.radius_m));
    text.push_str(&format!("GALAXY_INPUT|json=0|assumed_circular_speed_m_s={LOCAL_CIRCULAR_V_M_S}|distance_to_proxima_m_approx={}|observation_baseline_seconds={OBS_BASELINE_SECONDS}|rotation_curve=APPROXIMATE_NOT_FITTED\n",b.distance_proxima_m));
    text.push_str(&format!("BOUND|json=0|component=SGR_A_STAR|a_m_s2_times_1e18={}|absolute_shift_m_over_21yr={}|absolute_shift_nanoarcsec={}|shared_solar_acceleration_subtraction=NOT_MODELED|claim=ORDER_OF_MAGNITUDE_BOUND\n",b.gc_a_1e18,b.sagittarius_a_shift_m,b.sagittarius_a_nas));
    text.push_str(&format!("BOUND|json=0|component=WHOLE_GALAXY_POTENTIAL|a_m_s2_times_1e18={}|absolute_shift_m_over_21yr={}|absolute_shift_nanoarcsec={}|shared_solar_acceleration_subtraction=NOT_MODELED|claim=ORDER_OF_MAGNITUDE_BOUND\n",b.galaxy_a_1e18,b.galaxy_shift_m,b.galaxy_nas));
    text.push_str(&format!("COMPARE|json=0|measured_star_motion_arcsec_1976_1997_approx=81|sgr_a_angular_bound_nanoarcsec={}|galactic_angular_bound_nanoarcsec={}|relative_differential_effect=SMALLER_THAN_ABSOLUTE_UNIFORM_ACCELERATION_BOUND|precision=APPROXIMATE\n",b.sagittarius_a_nas,b.galaxy_nas));
    text.push_str("INTERPRETATION|json=0|sgr_a_is_part_of_galactic_gravity=TRUE|sgr_a_alone_cannot_explain_local_star_motion=TRUE|milky_way_extended_mass=IMPORTANT|solar_motion_parallax_instrument_WCS=SEPARATE_FACTORS|future_10_billion_year_jumps_need_DYNAMIC_GALACTIC_POTENTIAL_AND_STELLAR_ORBITS|matrix_skip_only_when_TRANSITION_LAW_VALID\n");
    text.push_str("FALSIFIER|json=0|new_planet_detected=NO|new_stellar_photon_frequency_measured=NO|micro_arcsecond_accurate_photographic_centroid=NO|sgr_a_direct_acceleration_measured_by_DSS=NO|ternary_R3_identity=PASS\n");
    Ok(text)
}
fn main(){
    let path=env::args().nth(1).unwrap_or_else(||"GALACTIC-CONTEXT.hbp".to_owned());
    let result=output().and_then(|text|{
        fs::write(PathBuf::from(path),&text).map_err(|e|e.to_string())?;
        print!("{text}");
        Ok(())
    });
    if let Err(e)=result{eprintln!("GALACTIC_HELD|json=0|reason={e}");std::process::exit(1);}
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn physical_scales_integer(){
        let v=model();
        assert!((8_000..10_000).contains(&v.gc_a_1e18));
        assert!((180_000_000..210_000_000).contains(&v.galaxy_a_1e18));
        assert!((1_800..2_200).contains(&v.sagittarius_a_shift_m));
        assert!((8..15).contains(&v.sagittarius_a_nas));
        assert!((150_000..250_000).contains(&v.galaxy_nas));
    }
    #[test] fn output_uses_hbp_and_no_json(){
        let c=output().unwrap();
        assert!(c.starts_with("HBP1|schema="));
        assert!(c.contains("galactic_center=SGR_A_STAR"));
        assert!(c.contains("matrix_skip_only_when_TRANSITION_LAW_VALID"));
        assert!(!c.starts_with('{'));
    }
}