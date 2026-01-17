# ============================================================
# This script was written and developed by Zhiyu Zheng at Fudan University; however, the underlying
# commands and reports are copyrighted by Cadence. We thank Cadence for
# granting permission to share our research to help promote and foster the next
# generation of innovators.
# extract_report.tcl — Unified reporting (Cadence Innovus)
#   extract_report -postRoute -outdir <DIR> \
#                   [-write_csv <csvpath>] [-write_summary <txtpath>]
#
# Metrics:
#   timing/power/area/wl/cong + drc/fep + hb_via_count
#   connectivity (verifyConnectivity): IMPVFC-92/94/total
#   ERC (electrical) via report_constraint: max_tran/max_cap/max_fanout
# ============================================================

proc _open_any {path} {
  if {![file exists $path]} { return "" }
  set fp [open $path r]
  if {[string match *.gz $path]} { zlib push gunzip $fp }
  return $fp
}

proc _ensure_dir {d} { if {![file exists $d]} { file mkdir $d } }

# --------------------------
# Timing / Power / Area / WL
# --------------------------
proc extract_from_timing_rpt {timing_rpt} {
  set wns ""; set tns ""; set hc ""; set vc ""; set flag 0
  set fp [_open_any $timing_rpt]
  if {$fp eq ""} {
    # Try removing .gz extension or adding it if missing
    set fp [_open_any [file rootname $timing_rpt]]
    if {$fp eq ""} { return [list $wns $tns $hc $vc] }
  }
  while {[gets $fp line] >= 0} {
    if {$flag == 0} { set words [split $line "|"] } else { set words [split $line] }
    if {[llength $words] < 2} { continue }
    if {[string map {" " ""} [lindex $words 1]] eq "WNS(ns):"} {
      set wns [string map {" " ""} [lindex $words 2]]
    } elseif {[string map {" " ""} [lindex $words 1]] eq "TNS(ns):"} {
      set tns [string map {" " ""} [lindex $words 2]]
      set flag 1
    } elseif {[llength $words] == 7 && [lindex $words 0] eq "Routing"} {
      set hc [lindex $words 2]; set vc [lindex $words 5]; break
    }
  }
  close $fp
  return [list $wns $tns $hc $vc]
}

proc extract_from_power_rpt {power_rpt} {
  if {![file exists $power_rpt]} { return "" }
  set power ""
  set fp [open $power_rpt r]
  while {[gets $fp line] >= 0} {
    if {[llength $line] == 3 && [lindex $line 0] eq "Total"} {
      set power [lindex $line 2]; break
    }
  }
  close $fp
  return $power
}

proc extract_cell_area {} {
  # Use catch to prevent crash if dbget fails (e.g. no macros)
  set macro_area 0
  set std_cell_area 0
  catch {
    set macro_area [expr [join [dbget [dbget top.insts.cell.subClass block -p2 ].area ] +]]
  }
  catch {
    set std_cell_area [expr [join [dbget [dbget top.insts.cell.subClass block -v -p2 ].area ] +]]
  }
  if {$macro_area eq ""} { set macro_area 0 }
  if {$std_cell_area eq ""} { set std_cell_area 0 }
  return [list $macro_area $std_cell_area]
}

proc extract_wire_length {} {
  set val 0
  catch { set val [expr [join [dbget top.nets.wires.length] +]] }
  if {$val eq ""} { set val 0 }
  return $val
}

# --------------------------
# FEP
# --------------------------
proc extract_fep {report_file_path} {
  set paths [report_timing -check_type setup -begin_end_pair -collection]
  set ep2min [dict create]
  foreach_in_collection p $paths {
    set slack [get_property $p slack]
    if {$slack < 0} {
      set ep [get_object_name [get_property $p capturing_point]]
      if {![dict exists $ep2min $ep]} {
        dict set ep2min $ep $slack
      } else {
        set cur [dict get $ep2min $ep]
        if {$slack < $cur} { dict set ep2min $ep $slack }
      }
    }
  }
  set FEP_vios [dict size $ep2min]
  set FEP_TNS 0.0
  set FEP_WNS 0.0
  if {$FEP_vios > 0} {
    set FEP_WNS 1e9
    dict for {ep s} $ep2min {
      set FEP_TNS [expr {$FEP_TNS + $s}]
      set FEP_WNS [expr {min($FEP_WNS, $s)}]
    }
  }
  set fid [open $report_file_path w]
  puts $fid "Total FEP Violations: $FEP_vios"
  puts $fid "Total FEP TNS: $FEP_TNS"
  puts $fid "Total FEP WNS: $FEP_WNS"
  close $fid
  return $FEP_vios
}

# --------------------------
# DRC
# --------------------------
proc extract_drc {drc_rpt} {
  verify_drc -exclude_pg_net -limit 100000 -report $drc_rpt
  set v ""
  set fp [open $drc_rpt r]
  while {[gets $fp line] >= 0} {
    if {[string match "  Total Violations : * Viols." $line]} {
      regexp {Total Violations : (\d+) Viols.} $line _ v
      set v [string trim $v]
      break
    }
  }
  close $fp
  if {$v eq ""} { set v 0 }
  return $v
}

# --------------------------
# HB via count (hb_layer cutLayer.name)
# --------------------------
proc count_hb_viaInst {cutlayer} {
  set sig [dbGet -e -u -p3 top.nets.vias.via.cutLayer.name $cutlayer]
  if {$sig eq "" || $sig eq "0x0"} { set sig {} }
  set pg {}
  if {![catch {dbGet -e -u -p3 top.pgNets.vias.via.cutLayer.name $cutlayer} pg_res]} {
    set pg $pg_res
    if {$pg eq "" || $pg eq "0x0"} { set pg {} }
  }
  set all [concat $sig $pg]
  if {$all eq ""} { return 0 }
  return [llength [lsort -unique $all]]
}

# ============================================================
# Helpers: run command and capture report
# ============================================================
proc _write_failed_report {rpt err} {
  set fh [open $rpt w]
  puts $fh "REPORT_FAILED: $err"
  close $fh
}

proc _capture_cmd_to_file {rpt script_body} {
  # Try redirect (preferred), fallback to stdout capture.
  if {![catch {
    if {[llength [info commands redirect]] > 0} {
      # Innovus usually supports: redirect -file <rpt> { ... }
      redirect -file $rpt $script_body
    } else {
      # Fallback: hope command returns a string
      set txt [uplevel 1 $script_body]
      set fh [open $rpt w]
      puts $fh $txt
      close $fh
    }
  } err]} {
    return 1
  }
  _write_failed_report $rpt $err
  return 0
}

# ============================================================
# Connectivity summary (verifyConnectivity)
# ============================================================
proc _parse_verifyConnectivity {rpt} {
  set c92 0
  set c94 0
  set total ""
  if {![file exists $rpt]} { return [list $c92 $c94 0] }
  set fp [open $rpt r]
  while {[gets $fp line] >= 0} {
    if {[regexp {^\s*([0-9]+)\s+Problem\(s\)\s+\((IMPVFC-92)\):} $line _ cnt _c]} {
      set c92 [expr {int($cnt)}]
      continue
    }
    if {[regexp {^\s*([0-9]+)\s+Problem\(s\)\s+\((IMPVFC-94)\):} $line _ cnt _c]} {
      set c94 [expr {int($cnt)}]
      continue
    }
    if {$total eq "" && [regexp {^\s*([0-9]+)\s+total\s+info\(s\)\s+created\.} $line _ cnt3]} {
      set total [expr {int($cnt3)}]
      continue
    }
  }
  close $fp
  if {$total eq ""} {
    set total [expr {$c92 + $c94}]
  }
  return [list $c92 $c94 $total]
}

proc run_connectivity_report {rpt} {
  if {![catch {verifyConnectivity -report $rpt} err]} {
    return 1
  }
  _write_failed_report $rpt $err
  return 0
}

# ============================================================
# ERC (Electrical Rule Check) via report_constraint (Innovus)
# ============================================================
proc run_erc_report_check_types {rpt} {
  # Innovus equivalent: report_constraint
  # Checking for Transition (Slew), Capacitance, and Fanout
  set body { 
    report_constraint -all_violators -max_transition -max_capacitance -max_fanout 
  }
  return [_capture_cmd_to_file $rpt $body]
}

proc _parse_erc_check_types {rpt} {
  # returns: (max_slew, max_cap, max_fanout, total)
  set ms 0
  set mc 0
  set mf 0
  
  if {![file exists $rpt]} { return [list 0 0 0 0] }
  
  set fp [open $rpt r]
  set mode "none" 
  
  while {[gets $fp line] >= 0} {
    set l [string trim $line]
    if {$l eq ""} { continue }
    
    # Log format: "Check type : max_transition"
    if {[regexp -nocase {Check\s*type\s*:\s*max_transition} $l] || [regexp -nocase {Max.*Transition.*Violations} $l]} {
      set mode "slew"
      continue
    } elseif {[regexp -nocase {Check\s*type\s*:\s*max_capacitance} $l] || [regexp -nocase {Max.*Capacitance.*Violations} $l]} {
      set mode "cap"
      continue
    } elseif {[regexp -nocase {Check\s*type\s*:\s*max_fanout} $l] || [regexp -nocase {Max.*Fanout.*Violations} $l]} {
      set mode "fanout"
      continue
    }
    
    if {[string match "*No Violations found*" $l]} { continue }

    if {[string match "-*" $l] || [string match "+*" $l]} { continue }
    
    # Log example: "| Pin Name | Required | ..."
    if {[string first "Pin Name" $l] != -1 || \
        [string first "Required" $l] != -1 || \
        [string first "Slack" $l] != -1} {
      continue
    }

    # --- 3. Count Violations ---
    switch -- $mode {
      "slew"   { incr ms }
      "cap"    { incr mc }
      "fanout" { incr mf }
    }
  }
  close $fp
  
  set total [expr {$ms + $mc + $mf}]
  return [list $ms $mc $mf $total]
}

# ============================================================
# Internal worker (no cd): run timeDesign + collect all reports into outdir
# ============================================================
proc _extract_postRoute {outdir} {
  set stage "Final"
  _ensure_dir $outdir
  
  # timingReports under outdir
  set tr_out [file join $outdir timingReports]
  _ensure_dir $tr_out
  
  # 1) Timing
  timeDesign -postRoute -prefix ${stage} -outDir $tr_out
  
  # 2) Power
  set power_rpt [file join $outdir power_${stage}.rpt]
  report_power > $power_rpt
  
  # 3) Parse timing summary (prefer .gz)
  set tpath_gz [file join $tr_out ${stage}.summary.gz]
  set tpath    [file join $tr_out ${stage}.summary]
  set timing_path [expr {[file exists $tpath_gz] ? $tpath_gz : $tpath}]
  set rpt1  [extract_from_timing_rpt $timing_path]
  set rpt2  [extract_from_power_rpt  $power_rpt]
  set rpt3  [extract_cell_area]
  set rpt4  [extract_wire_length]
  
  # 4) DRC & FEP
  set drc_v [extract_drc [file join $outdir drc.rpt]]
  set fep_v [extract_fep [file join $outdir fep.rpt]]
  
  # 5) HB via count
  set hb_via_cnt [count_hb_viaInst "hb_layer"]
  
  # 6) Connectivity (NOT electrical ERC; keep separate)
  set conn_rpt [file join $outdir erc_connectivity.rpt]
  run_connectivity_report $conn_rpt
  lassign [_parse_verifyConnectivity $conn_rpt] conn92 conn94 conn_total
  
  # 7) Electrical ERC (report_constraint)
  set erc_rpt [file join $outdir erc_check_types.rpt]
  run_erc_report_check_types $erc_rpt
  lassign [_parse_erc_check_types $erc_rpt] erc_ms erc_mc erc_mf erc_total
  
  # 8) Assemble CSV
  set core_area 0
  catch { set core_area [dbget top.fplan.coreBox_area] }
  
  set std_area  [lindex $rpt3 1]
  set mac_area  [lindex $rpt3 0]
  set wns       [lindex $rpt1 0]
  set tns       [lindex $rpt1 1]
  set hc        [lindex $rpt1 2]
  set vc        [lindex $rpt1 3]
  
  # Safety for missing timing values
  if {$wns eq ""} { set wns 0 }
  if {$tns eq ""} { set tns 0 }
  
  return "$stage,$core_area,$std_area,$mac_area,$rpt2,$rpt4,$wns,$tns,$hc,$vc,$drc_v,$fep_v,$hb_via_cnt,$conn92,$conn94,$conn_total,$erc_ms,$erc_mc,$erc_mf,$erc_total"
}

# ---- Public entrypoint ----
proc extract_report {args} {
  set mode ""; set outdir "."; set write_csv ""; set write_sum ""
  set i 0
  while {$i < [llength $args]} {
    set a [lindex $args $i]
    switch -- $a {
      -postRoute      { set mode "postRoute" }
      -outdir         { incr i; set outdir    [lindex $args $i] }
      -write_csv      { incr i; set write_csv [lindex $args $i] }
      -write_summary  { incr i; set write_sum [lindex $args $i] }
      default         { error "extract_report: unknown option '$a'" }
    }
    incr i
  }
  
  if {$mode eq ""} { error "extract_report: specify -postRoute" }
  
  set csv_line ""
  if {$mode eq "postRoute"} {
    set csv_line [_extract_postRoute $outdir]
  }
  
  if {$write_csv ne ""} {
    set fid [open $write_csv w]
    puts $fid "stage,core_area,std_cell_area,macro_area,total_power,wire_length,wns,tns,h_cong,v_cong,drc_violations,fep_violations,hb_via_count,connectivity_improvfc92,connectivity_improvfc94,connectivity_total,erc_max_slew,erc_max_cap,erc_max_fanout,erc_total_elec"
    puts $fid $csv_line
    close $fid
  }
  
  if {$write_sum ne ""} {
    set fh [open $write_sum w]
    puts $fh "=== Cadence Pin3DFlow – Final Metrics (postRoute) ==="
    puts $fh "Out dir     : $outdir"
    if {$write_csv ne ""} { puts $fh "CSV         : $write_csv" }
    puts $fh ""
    set f [split $csv_line ","]
    puts $fh [format "%-26s %s" "Core Area"              [lindex $f 1]]
    puts $fh [format "%-26s %s" "StdCell Area"           [lindex $f 2]]
    puts $fh [format "%-26s %s" "Macro Area"             [lindex $f 3]]
    puts $fh [format "%-26s %s" "Total Power"            [lindex $f 4]]
    puts $fh [format "%-26s %s" "Wire Length"            [lindex $f 5]]
    puts $fh [format "%-26s %s" "WNS (ns)"               [lindex $f 6]]
    puts $fh [format "%-26s %s" "TNS (ns)"               [lindex $f 7]]
    puts $fh [format "%-26s %s" "H Congestion"           [lindex $f 8]]
    puts $fh [format "%-26s %s" "V Congestion"           [lindex $f 9]]
    puts $fh [format "%-26s %s" "DRC Violations"         [lindex $f 10]]
    puts $fh [format "%-26s %s" "FEP Violations"         [lindex $f 11]]
    puts $fh [format "%-26s %s" "HB VIA Count"           [lindex $f 12]]
    puts $fh ""
    puts $fh "=== Connectivity (verifyConnectivity) ==="
    puts $fh [format "%-26s %s" "IMPVFC-92 (Disconnected)" [lindex $f 13]]
    puts $fh [format "%-26s %s" "IMPVFC-94 (Dangling)"     [lindex $f 14]]
    puts $fh [format "%-26s %s" "Total (info created)"     [lindex $f 15]]
    puts $fh ""
    puts $fh "=== ERC (Electrical: report_constraint) ==="
    puts $fh [format "%-26s %s" "Max Slew Violations"      [lindex $f 16]]
    puts $fh [format "%-26s %s" "Max Cap Violations"       [lindex $f 17]]
    puts $fh [format "%-26s %s" "Max Fanout Violations"    [lindex $f 18]]
    puts $fh [format "%-26s %s" "ERC Total (sum)"          [lindex $f 19]]
    close $fh
  }
  return $csv_line
}