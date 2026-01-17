####################################
# global connections
####################################
add_global_connection -net {VDD} -inst_pattern {.*} -pin_pattern {^VDD$} -power
add_global_connection -net {VDD} -inst_pattern {.*} -pin_pattern {^VDDPE$}
add_global_connection -net {VDD} -inst_pattern {.*} -pin_pattern {^VDDCE$}
add_global_connection -net {VSS} -inst_pattern {.*} -pin_pattern {^VSS$} -ground
add_global_connection -net {VSS} -inst_pattern {.*} -pin_pattern {^VSSE$}
global_connect

####################################
# voltage domains
####################################
set_voltage_domain -name {CORE} -power {VDD} -ground {VSS}

####################################
# Dynamic Pitch Calculation
####################################

set core_area_bbox   [[odb::get_block] getCoreArea]

set core_llx [$core_area_bbox xMin]
set core_lly [$core_area_bbox yMin]
set core_urx [$core_area_bbox xMax]
set core_ury [$core_area_bbox yMax]

set core_width  [ord::dbu_to_microns [expr $core_urx - $core_llx]]
set core_height [ord::dbu_to_microns [expr $core_ury - $core_lly]]

puts "INFO: Core Area Width: $core_width, Height: $core_height"

set mfg_grid 0.005

set m4_pitch [expr {$core_width / 1.1}]
if {$m4_pitch > 20.16} {
    set m4_pitch 20.16
}
set m4_pitch [expr {round($m4_pitch / $mfg_grid) * $mfg_grid}]

set m7_pitch [expr {$core_height / 1.1}]
if {$m7_pitch > 40} {
    set m7_pitch 40
}
set m7_pitch [expr {round($m7_pitch / $mfg_grid) * $mfg_grid}]

puts "INFO: Dynamic PDN Pitch -> M4: $m4_pitch, M7: $m7_pitch"

####################################
# standard cell grid
####################################
define_pdn_grid -name {grid} -voltage_domains {CORE}

# M1 使用固定的 follow-pin 策略
add_pdn_stripe -grid {grid} -layer {M1} -width {0.17} -pitch {2.8} -offset {0} -followpins
add_pdn_stripe -grid {grid} -layer {M1_m} -width {0.17} -pitch {2.8} -offset {0}

add_pdn_stripe -grid {grid} -layer {M4_m} -width {0.84} -pitch $m4_pitch -offset {2}
add_pdn_stripe -grid {grid} -layer {M4} -width {0.84} -pitch $m4_pitch -offset {2} 

add_pdn_stripe -grid {grid} -layer {M7} -width {2.4} -pitch $m7_pitch -offset {2}
add_pdn_stripe -grid {grid} -layer {M7_m} -width {2.4} -pitch $m7_pitch -offset {2}

add_pdn_stripe -grid {grid} -layer {M10} -width {3.2} -pitch 32.0 -offset {2} 

# 连接各层
add_pdn_connect -grid {grid} -layers {M1 M4}
add_pdn_connect -grid {grid} -layers {M4 M7}
add_pdn_connect -grid {grid} -layers {M1_m M4_m}
add_pdn_connect -grid {grid} -layers {M4_m M7_m}

