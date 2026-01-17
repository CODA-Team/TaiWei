# load read design and perform placement
set all_lefs [concat $env(TECH_LEF) $env(SC_LEF) $env(ADDITIONAL_LEFS)]
foreach lef_file $all_lefs {
    read_lef $lef_file
}
set all_libs [concat $env(LIB_FILES)]
foreach lib_file $all_libs {
    read_liberty $lib_file
}

# read_verilog $env(RESULTS_DIR)/$env(DESIGN_DIMENSION).gp.v
# link_design $env(DESIGN_NAME)
# puts "Reading DEF file: $env(RESULTS_DIR)/$env(DEF_VERSION)_$env(DESIGN_DIMENSION).gp.def"
# read_def -floorplan_initialize $env(RESULTS_DIR)/$env(DEF_VERSION)_$env(DESIGN_DIMENSION).gp.def
# source $env(PLATFORM_HOME)/$env(PLATFORM)/setRC.tcl

read_def $env(RESULTS_DIR)/$env(DEF_VERSION)_$env(DESIGN_DIMENSION).gp.def

if {[info exist ::env(PLACE_DENSITY_LB_ADDON)]} {
    puts "PLACE_DENSITY_LB_ADDON is set: $::env(PLACE_DENSITY_LB_ADDON)"
    set place_density_lb [gpl::get_global_placement_uniform_density \
        -pad_left $::env(CELL_PAD_IN_SITES_GLOBAL_PLACEMENT) \
        -pad_right $::env(CELL_PAD_IN_SITES_GLOBAL_PLACEMENT)]
    puts "Calculated place_density_lb: $place_density_lb"
    set place_density [expr $place_density_lb + ((1.0 - $place_density_lb) * $::env(PLACE_DENSITY_LB_ADDON)) + 0.01]
    puts "Calculated place_density: $place_density"
} else {
    set place_density $::env(PLACE_DENSITY)
    puts "PLACE_DENSITY_LB_ADDON not set, using PLACE_DENSITY: $place_density"
}

set global_placement_args ""
puts "Running global placement with density: $place_density"
global_placement -density $place_density \
        -skip_initial_place \
        -pad_left $::env(CELL_PAD_IN_SITES_GLOBAL_PLACEMENT) \
        -pad_right $::env(CELL_PAD_IN_SITES_GLOBAL_PLACEMENT) \
        {*}$global_placement_args

write_def $env(RESULTS_DIR)/$env(DEF_VERSION)_$env(DESIGN_DIMENSION).gp.def
# write_verilog $env(RESULTS_DIR)/$env(DESIGN_DIMENSION).gp.v

save_image -resolution 0.1 $::env(RESULTS_DIR)/place_bottom.webp 