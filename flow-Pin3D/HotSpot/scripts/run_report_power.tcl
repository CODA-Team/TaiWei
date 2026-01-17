# ============================================================
# run_report_power.tcl
#   - Run in OpenSTA to:
#       * read Liberty / netlist / SDC / SPEF
#       * compute per-grid total power from report_power
#       * normalize power for HotSpot
#       * optionally scale total power to target (for HotSpot)
#       * write HotSpot-compatible .ptrace
#
# Required env vars:
#   LIB_FILES          : all .lib files (space-separated)
#   FINAL_V            : 6_final.v
#   FINAL_SDC          : 6_final.sdc
#   FINAL_SPEF         : 6_final.spef
#   DESIGN_NAME        : top module name, e.g., gcd
#   HOTSPOT_OUTPUT     : directory for Grid_()*.txt and .ptrace
#
# Optional env vars:
#   GRID_SIZE              : default 10
#   HOTSPOT_TARGET_POWER   : target total power in W (for normalization)
#   HOTSPOT_PTRACE_BASENAME: base name of output .ptrace (no suffix)
#                            e.g., "upper", "bottom", "gcc"
#                            Fallback order: HOTSPOT_PTRACE_BASENAME
#                                            -> DESIGN_NICKNAME
#                                            -> DESIGN_NAME
#
# NOTE on power scaling:
#   - We parse "report_units" inside this script.
#   - If power unit is 1pW  -> power_scale = 0.001 (i.e., /1000)
#   - If power unit is 1nW  -> power_scale = 1.0   (no change)
#   - Otherwise             -> power_scale = 1.0   (with a warning)
# ============================================================

# ---------- 0. Basic env check ----------
if {![info exists ::env(HOTSPOT_OUTPUT)]} {
  puts "ERROR: \[HOTSPOT\] env(HOTSPOT_OUTPUT) not set."
  exit 1
}
set output_dir $::env(HOTSPOT_OUTPUT)

set grid_size 10
if {[info exists ::env(GRID_SIZE)]} {
  set grid_size $::env(GRID_SIZE)
}

if {![info exists ::env(LIB_FILES)]} {
  puts "ERROR: \[HOTSPOT\] env(LIB_FILES) not set."
  exit 1
}
set lib_files [split $::env(LIB_FILES)]

foreach var {FINAL_V FINAL_SDC FINAL_SPEF DESIGN_NAME} {
  if {![info exists ::env($var)]} {
    puts "ERROR: \[HOTSPOT\] env($var) not set."
    exit 1
  }
}
set final_v    $::env(FINAL_V)
set final_sdc  $::env(FINAL_SDC)
set final_spef $::env(FINAL_SPEF)
set design     $::env(DESIGN_NAME)

# ---------- 0.1 Decide ptrace basename ----------
set ptrace_basename ""
if {[info exists ::env(HOTSPOT_PTRACE_BASENAME)] && $::env(HOTSPOT_PTRACE_BASENAME) ne ""} {
  set ptrace_basename $::env(HOTSPOT_PTRACE_BASENAME)
} elseif {[info exists ::env(DESIGN_NICKNAME)] && $::env(DESIGN_NICKNAME) ne ""} {
  set ptrace_basename $::env(DESIGN_NICKNAME)
} else {
  set ptrace_basename $design
}
puts "INFO: \[HOTSPOT\] ptrace basename = $ptrace_basename"
puts "INFO: \[HOTSPOT\] grid_size       = $grid_size"
puts "INFO: \[HOTSPOT\] output_dir      = $output_dir"

# ---------- 1. Load design ----------
puts "INFO: \[HOTSPOT\] Loading Liberty files..."
foreach lib_file $lib_files {
  if {$lib_file eq ""} {
    continue
  }
  if {![file exists $lib_file]} {
    puts "WARN: \[HOTSPOT\] Liberty not found: $lib_file"
    continue
  }
  puts "INFO: \[HOTSPOT\] read_liberty $lib_file"
  read_liberty $lib_file
}

# Debug: print loaded library objects
foreach lib [get_libs *] {
  puts "LIB OBJECT: $lib"
  puts "  name      = [get_property $lib name]"
  puts "  full_name = [get_property $lib full_name]"
  puts "  file      = [get_property $lib filename]"
  puts ""
}

puts "INFO: \[HOTSPOT\] read_verilog $final_v"
read_verilog $final_v

puts "INFO: \[HOTSPOT\] link_design $design"
link_design $design

puts "INFO: \[HOTSPOT\] read_sdc $final_sdc"
read_sdc $final_sdc

puts "INFO: \[HOTSPOT\] read_spef $final_spef"
read_spef $final_spef

# Basic activity for early-stage power estimation
catch { set_power_activity -input -activity 0.1 }
catch { set_power_activity -input_port reset -activity 0.0 }

# ---------- 2. Power unit & scale setup ----------
# 默认：不缩放
set power_scale 1.0
set power_unit  "W"

report_units

# 用 OpenSTA 的 with_output_to_variable 把 report_units 输出抓到变量里
set units_text ""
if {[catch {with_output_to_variable units_text { report_units }} msg]} {
  puts "WARN: \[HOTSPOT\] Failed to capture report_units; using default power_scale = $power_scale."
} else {
  # 从输出中找包含 power 的那一行
  set power_line ""
  foreach line [split $units_text "\n"] {
    set t [string trim $line]
    # 兼容 "power 1pW" 或 "Power : 1 mW" 之类格式
    if {[regexp -nocase {^power} $t]} {
      set power_line $t
      break
    }
  }

  if {$power_line ne ""} {
    # 提取出数值和单位，例如:
    #   "power 1pW"           -> val=1,  unit=pW
    #   "Power : 1 mW"        -> val=1,  unit=mW
    if {[regexp -nocase {power\s*:?[\s]*([0-9.eE+\-]+)\s*([a-zA-Z]+)} $power_line -> val unit]} {
      set power_unit $unit

      # 你的规则：
      #   pW -> 除以 1000
      #   nW -> 不变
      #   其他单位 -> 也不缩放（按原值）
      switch -nocase -- $unit {
        "pw" {
          set power_scale 1.0
          puts "INFO: \[HOTSPOT\] Detected power unit '$unit'; applying scale /1.0 (power_scale=$power_scale)."
        }
        "nw" {
          set power_scale 1.0
          puts "INFO: \[HOTSPOT\] Detected power unit '$unit'; applying scale *1.0 power_scale=$power_scale."
        }
        default {
          set power_scale 1.0
          puts "WARN: \[HOTSPOT\] Power unit '$unit' not handled specially; keeping power_scale=$power_scale."
        }
      }
    } else {
      puts "WARN: \[HOTSPOT\] Could not parse power line '$power_line'; using default power_scale = $power_scale."
    }
  } else {
    puts "WARN: \[HOTSPOT\] No 'power' line found in report_units; using default power_scale = $power_scale."
  }
}

puts "INFO: \[HOTSPOT\] Final power_unit = $power_unit"
puts "INFO: \[HOTSPOT\] Final power_scale = $power_scale"

# ---------- 3. Helper procs ----------
proc read_file_as_string {filename} {
  set fd [open $filename r]
  set content [read $fd]
  close $fd
  return $content
}

# Sum last numeric column of each valid line in report_power output
proc sum_total_power_from_report {filename} {
  set total 0.0
  if {![file exists $filename]} {
    return $total
  }
  set fd [open $filename r]
  while {[gets $fd line] >= 0} {
    # Skip blank lines and separators
    if {![regexp {\S} $line]} {
      continue
    }
    if {[string match "*----*" $line] || [string match "*====*" $line]} {
      continue
    }
    set cols [split $line]
    set nums {}
    foreach c $cols {
      if {[regexp {^[-+]?[0-9]+(\.[0-9]*)?([eE][-+]?[0-9]+)?$} $c]} {
        lappend nums $c
      }
    }
    if {[llength $nums] == 0} {
      continue
    }
    set last [lindex $nums end]
    set total [expr {$total + double($last)}]
  }
  close $fd
  return $total
}

# ---------- 4. Loop all grids ----------
set ptrace_filename [file join $output_dir "${ptrace_basename}.ptrace"]
set ptrace_file [open $ptrace_filename "w"]

set grid_names {}
set total_powers {}
set total_power 0.0

for {set i 0} {$i < $grid_size} {incr i} {
  for {set j 0} {$j < $grid_size} {incr j} {
    set grid_file [file join $output_dir "Grid_($i, $j).txt"]
    set grid_name "Grid_${i}_${j}"
    set raw 0.0

    if {[file exists $grid_file]} {
      set insts [string trim [read_file_as_string $grid_file]]
      file delete $grid_file

      if {$insts ne ""} {
        set rpt [file join $output_dir "rpt_($i,$j).txt"]
        report_power -instances $insts > $rpt
        set raw [sum_total_power_from_report $rpt]
        file delete $rpt
      }
    }

    # Apply power_scale (pW /1000, nW unchanged, others as-is)
    set Pw [expr {$raw * $power_scale}]
    puts "INFO: \[HOTSPOT\] $grid_name: raw=$raw, scaled=$Pw"
    lappend grid_names $grid_name
    lappend total_powers $Pw
    set total_power [expr {$total_power + $Pw}]
  }
}
# error
puts "INFO: \[HOTSPOT\] Total power (before global scaling): $total_power (scaled unit)"

# ---------- 5. Optional global normalization ----------
set scale_factor 1.0
if {[info exists ::env(HOTSPOT_TARGET_POWER)]} {
  set P_target [expr {double($::env(HOTSPOT_TARGET_POWER))}]
  if {$total_power > 0.0} {
    set scale_factor [expr {$P_target / $total_power}]
  }
  puts "INFO: \[HOTSPOT\] Target total power = $P_target W"
}
puts "INFO: \[HOTSPOT\] Applying global scale_factor = $scale_factor"

# ---------- 6. Write .ptrace ----------
set grid_line [join $grid_names " "]
set pw_line {}
foreach p $total_powers {
  lappend pw_line [expr {$p * $scale_factor}]
}
set pw_line [join $pw_line " "]

puts $ptrace_file $grid_line
puts $ptrace_file $pw_line
close $ptrace_file

puts "INFO: \[HOTSPOT\] Final total power (after scaling) = [expr {$total_power * $scale_factor}] (scaled unit)"
puts "INFO: \[HOTSPOT\] Wrote ptrace to $ptrace_filename"

exit
