# TaiWei True-3D Flow Integration

## Overview

This repository integrates 3D Synthesis, True-3D Detailed
Placement, and True-3D CTS into the TaiWei flow. Each point tool has a matching
adapter and Make target in `TaiWei-Pin-3D`. On `native-3d`, the default
OpenROAD launcher selects all three integrations automatically. Global
placement still uses the existing tier-by-tier preparation before TDP.

## Integration Layout

```text
TaiWei/
├── ORFS-Research/
│   └── tools/
│       ├── yosys-research/
│       │   └── passes/3dsyn/
│       └── OpenROAD/
│           └── src/
│               ├── 3ddp/
│               └── 3dcts/
└── TaiWei-Pin-3D/
    ├── scripts_3dsyn/
    ├── scripts_3ddp/
    ├── scripts_3dcts/
    └── Makefile
```

`ORFS-Research` contains the point-tool implementations and the OpenROAD/Yosys
toolchain. The matching `scripts_*` directories in `TaiWei-Pin-3D` provide the
flow adapters, input/output validation, and standard TaiWei handoffs. Detailed
configuration and stage contracts are documented in each adapter directory.

## Branches

The `native-3d` checkout is based on the pinned `integration/2610` versions.
The TaiWei, TaiWei-Pin-3D, ORFS-Research, OpenROAD-Research and yosys-research
repositories each have a local `native-3d` branch. The parallel `pesudo-3d`
branches preserve the original integration flow. These local branches need
to be published before they can be cloned by name from the remote servers.

## Build OpenROAD and Yosys

Install the ORFS dependencies, then build the OpenROAD and Yosys sources stored
in the pinned submodules. The build defaults to `tools/yosys-research`,
which contains the integrated 3D-Syn passes.

```bash
cd ORFS-Research
./build_openroad.sh --local --threads 16
```

The default installation is written below:

```text
ORFS-Research/tools/install/OpenROAD
ORFS-Research/tools/install/yosys
```

Use another positive value for `--threads` as appropriate for the build host.
Do not use `--latest`, `--or_branch`, or `--or_repo` in this source checkout:
those options can replace the pinned OpenROAD version and bypass the
integrated changes.

## Initialize and Run TaiWei

`TaiWei-Pin-3D/env.sh` currently derives `FLOW_HOME` from the current working
directory. Always enter the flow directory before sourcing it:

```bash
cd ../TaiWei-Pin-3D
source ./env.sh
```

The default native GCD run can then be launched with (Genus is required):

```bash
python3 run_experiments.py --flow ord --tech asap7_3D --case gcd
```

Generated logs, intermediate databases, reports, and results are written below
`logs/`, `objects/`, `reports/`, and `results/`. These directories are ignored
by Git.

## Default stage sequence

The normal `run_experiments.py --flow ord` command, per-case `run.sh` wrappers
and `test/openroad/ORD_3D_NEW_FLOW.sh` run:

1. `cds-coarse-synth` → `ord-coarse-partition` → `cds-per-tier-synth` →
   `ord-3dsyn-handoff`, using `config2d.mk` and the 3D variant output paths.
2. `ord-3d-floorplan` and the existing IO, split-net, macro, PDN and global
   placement stages, using `config.mk`.
3. `ord-gp2lg` → `ord-detail-place-3d` → `ord-cts-3d` →
   `ord-route-3d-cts` → `ord-final`.

The synthesis handoff produces `<design>_3D.fp.v/.def`. Running `ord-pre`
afterwards would overwrite it using the coarse-partition netlist. 3DCTS
publishes the complete `4_cts.*` handoff, including clock-cell legalization,
so no legacy `ord-cts-post` call follows it.

For Make-level operation, `ord-3d-synth` runs the frontend with `config2d.mk`;
`ord-3d-flow` continues its handoff with `config.mk`:

```bash
make DESIGN_CONFIG=designs/asap7_3D/gcd/config2d.mk FLOW_VARIANT=native ord-3d-synth
make DESIGN_CONFIG=designs/asap7_3D/gcd/config.mk FLOW_VARIANT=native ord-3d-flow
```

Resume without cleaning completed stages using the native target name:

```bash
START_FROM=ord-detail-place-3d FLOW_VARIANT=native \
bash test/asap7_3D/gcd/ord/run.sh
```

`START_FROM=ord-3d-floorplan` reuses an existing 3D-Syn handoff. Legacy
`SKIP_2D_PART` and `REUSE_2DPART_FROM_VARIANT` controls are rejected on this
branch. Stage failures stop the pipeline before downstream tools run.

## Point-Tool Entry Examples

All commands below are run from `TaiWei-Pin-3D` after sourcing `env.sh`. A
stage must use the same `DESIGN_CONFIG` and `FLOW_VARIANT` as its upstream
handoff.

### 3D Synthesis

Run the complete 3D Synthesis frontend with the OpenROAD physical backend:

```bash
SYN3D_BACKEND=ord \
./scripts_3dsyn/run_3d_syn.sh asap7_3D gcd 3dsyn_gcd
```

Cadence Genus must be available even when `SYN3D_BACKEND=ord`.

### True-3D Detailed Placement

After `ord-gp2lg` has produced the legalizer input handoff, run:

```bash
make DESIGN_CONFIG=designs/asap7_3D/gcd/config.mk \
     FLOW_VARIANT=3ddp_gcd \
     ord-detail-place-3d
```

### True-3D CTS

After placement has produced `3_place.def`, `3_place.v`, and `3_place.sdc`,
run:

```bash
make DESIGN_CONFIG=designs/asap7_3D/gcd/config.mk \
     FLOW_VARIANT=3dcts_gcd \
     ord-cts-3d
```

Continue with `ord-route-3d-cts` and `ord-final` using the same configuration and
variant.
