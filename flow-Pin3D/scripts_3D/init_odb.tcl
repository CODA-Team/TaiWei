set def_version $env(DEF_VERSION)

set all_lefs [concat $env(TECH_LEF) $env(SC_LEF) $env(ADDITIONAL_LEFS)]
foreach lef_file $all_lefs {
    read_lef $lef_file
}
read_def ./designs/$env(PLATFORM)/$env(DESIGN_NICKNAME)/${def_version}_$env(DESIGN_DIMENSION).gp.def
write_db $env(RESULTS_DIR)/$env(DESIGN_DIMENSION)_out.odb
