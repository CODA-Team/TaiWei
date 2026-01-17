read_db $env(RESULTS_DIR)/2_2_floorplan_io.odb

set all_libs [concat $env(LIB_FILES)]
foreach lib_file $all_libs {
    read_liberty $lib_file
}

triton_part_design -solution_file $env(RESULTS_DIR)/partition.txt

