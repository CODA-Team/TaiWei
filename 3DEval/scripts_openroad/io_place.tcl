source $::env(OPENROAD_SCRIPTS_DIR)/util.tcl

# IO layers must be provided by the flow (e.g., "metal2" for H, "metal3" for V).
if {![info exists ::env(IO_PLACER_H)] || ![info exists ::env(IO_PLACER_V)]} {
  error "IO_PLACER_H / IO_PLACER_V must be set (e.g., set ::env(IO_PLACER_H) metal2; set ::env(IO_PLACER_V) metal3)."
}
set LAYER_H $::env(IO_PLACER_H)
set LAYER_V $::env(IO_PLACER_V)

# =====================================
# 1) Utility: die bbox & DBU conversion
# =====================================
proc get_die_bbox {} {
    return [ord::get_die_area]
}

proc get_db_units_per_micron {} {
    return [[odb::get_block] getDbUnitsPerMicron]
}
# DBU per micron
set DBU_PER_UM [get_db_units_per_micron]

# Round um -> DBU safely
proc um_to_dbu_round {val_um dbu_per_um} {
  return [expr {round ($val_um * $dbu_per_um * 1000) / 1000.0 }]
}

# ==========================================
# 2) Collect & sanitize top-level IO port set
# ==========================================
proc has_bits {base all_list} {
  foreach q $all_list { if {[string match "${base}\[*]" $q]} { return 1 } }
  return 0
}
proc sanitize_ports {ports all_ports} {
  set keep {}; array set seen {}
  foreach p $ports {
    # Skip power/ground variants
    if {[regexp -nocase {^(VDD|VSS|VDDA|VSSA|VCCD|VSSD|PWR|GND)} $p]} { continue }
    # Keep unique vector bits; skip scalar base if it has bits
    if {[regexp {\[[0-9]+\]} $p]} {
      if {![info exists seen($p)]} { set seen($p) 1; lappend keep $p }
      continue
    }
    if {[has_bits $p $all_ports]} { continue }
    if {![info exists seen($p)]} { set seen($p) 1; lappend keep $p }
  }
  return [lsort -dictionary -unique $keep]
}

set ins_raw  [lsort -dictionary [all_inputs]]
set outs_raw [lsort -dictionary [all_outputs]]
set all_raw  [concat $ins_raw $outs_raw]
set pins_all [sanitize_ports $all_raw $all_raw]
set N [llength $pins_all]

puts [format "IO-INFO: total ports=%d, kept=%d" [llength $all_raw] $N]

# ===============================
# 3) Geometry & perimeter in um
# ===============================
lassign [get_die_bbox] LX LY UX UY
set W_dbu [expr {$UX - $LX}]
set H_dbu [expr {$UY - $LY}]
if {$W_dbu <= 0 || $H_dbu <= 0} { error "Invalid die size: W=$W_dbu H=$H_dbu (DBU)" }

set W_um     [expr {double($W_dbu)/$DBU_PER_UM}]
set H_um     [expr {double($H_dbu)/$DBU_PER_UM}]
set PERIM_um [expr {2.0*($W_um + $H_um)}]

# =======================================================
# 4) Derive corner_avoidance / min_distance (in microns)
# =======================================================
# Start with 2% of the short side; clamp into [0, 2%*short]
set short_um     [expr {min($W_um, $H_um)}]
set ca_um       [expr {0.02*$short_um}]

# Effective usable perimeter after skipping four corners (two ends per side)
proc eff_perim {perim ca} { return [expr {$perim - 8.0*$ca}] }
set L_eff [eff_perim $PERIM_um $ca_um]

# Guarantee feasibility by relaxing corner_avoidance if needed
if {$L_eff <= 0.0} {
  set ca_um 0.0
  set L_eff [eff_perim $PERIM_um $ca_um]
}

# Uniform target pitch and a small slack (80%) for min_distance
set pitch_um     [expr {$L_eff / double($N)}]
set min_dist_um  [expr {max(0.0, 0.7*$pitch_um)}]

# (Optional) enforce a technology floor for gap, e.g., 0.2um if desired
set MIN_ABS_GAP_UM 0.0
if {$min_dist_um < $MIN_ABS_GAP_UM} { set min_dist_um $MIN_ABS_GAP_UM }

puts [format "IO-INFO(um): N=%d, W=%.6f H=%.6f Perim=%.6f L_eff=%.6f  corner_avoid=%.6f  min_distance=%.6f" \
              $N $W_um $H_um $PERIM_um $L_eff $ca_um $min_dist_um]

# ===========================================
# 5) Convert arguments to DBU for place_pins
# ===========================================
set ca_dbu       [um_to_dbu_round $ca_um       $DBU_PER_UM]
set min_dist_dbu [um_to_dbu_round $min_dist_um $DBU_PER_UM]

if {$ca_dbu < 0} { set ca_dbu 0 }

puts [format "IO-INFO(DBU): DBU_PER_UM=%f  corner_avoid=%f  min_distance=%f" \
              $DBU_PER_UM $ca_dbu $min_dist_dbu]

# ===================================
# 6) Invoke place_pins (DBU arguments)
# ===================================
clear_io_pin_constraints
# Tip: If you need to lock/fix specific pins, add set_io_pin_constraint before place_pins.
# Example:

log_cmd place_pins \
  -hor_layers $LAYER_H \
  -ver_layers $LAYER_V \
  -min_distance $min_dist_dbu \
  -corner_avoidance $ca_dbu \
  -annealing

puts "FINAL: IO pins placed with perimeter-based DBU parameters. "
