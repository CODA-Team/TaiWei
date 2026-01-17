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

set m4_pitch [expr {$core_width / 1.8}]
if {$m4_pitch > 56.0} {
    set m4_pitch 56.0
}
set m4_pitch [expr {round($m4_pitch / $mfg_grid) * $mfg_grid}]

set m7_pitch [expr {$core_height / 1.8}]
if {$m7_pitch > 30.0} {
    set m7_pitch 30.0
}
set m7_pitch [expr {round($m7_pitch / $mfg_grid) * $mfg_grid}]

puts "INFO: Dynamic PDN Pitch -> M4: $m4_pitch, M7: $m7_pitch"

####################################
# standard cell grid
####################################
define_pdn_grid -name {grid} -voltage_domains {CORE}

# M1 使用固定的 follow-pin 策略
add_pdn_stripe -grid {grid} -layer {metal1} -width {0.17} -pitch {2.4} -offset {0} -followpins

# M4 和 M7 使用动态计算的 pitch
add_pdn_stripe -grid {grid} -layer {metal4} -width {0.48} -pitch $m4_pitch -offset {2}
add_pdn_stripe -grid {grid} -layer {metal7} -width {1.40} -pitch $m7_pitch -offset {2}

# 连接各层
add_pdn_connect -grid {grid} -layers {metal1 metal4}
add_pdn_connect -grid {grid} -layers {metal4 metal7}
####################################
# macro grids
####################################
####################################
# grid for: CORE_macro_grid_1
####################################
# define_pdn_grid -name {CORE_macro_grid_1} -voltage_domains {CORE} -macro -orient {R0 R180 MX MY} -halo {2.0 2.0 2.0 2.0} -cells {.*} -grid_over_pg_pins
# add_pdn_stripe -grid {CORE_macro_grid_1} -layer {metal16} -width {0.93} -pitch {10.0} -offset {2} -followpins
# add_pdn_stripe -grid {CORE_macro_grid_1} -layer {metal15} -width {0.93} -pitch {10.0} -offset {2} -followpins
# add_pdn_connect -grid {CORE_macro_grid_1} -layers {metal17 metal16}
# add_pdn_connect -grid {CORE_macro_grid_1} -layers {metal16 metal15}
# add_pdn_connect -grid {CORE_macro_grid_1} -layers {metal15 metal14}
# ####################################
# # grid for: CORE_macro_grid_2
# ####################################
# define_pdn_grid -name {CORE_macro_grid_2} -voltage_domains {CORE} -macro -orient {R90 R270 MXR90 MYR90} -halo {2.0 2.0 2.0 2.0} -cells {.*} -grid_over_pg_pins
# add_pdn_stripe -grid {CORE_macro_grid_2} -layer {metal6} -width {0.93} -pitch {40.0} -offset {2} -followpins
# add_pdn_connect -grid {CORE_macro_grid_2} -layers {metal4 metal6}
# add_pdn_connect -grid {CORE_macro_grid_2} -layers {metal6 metal7}