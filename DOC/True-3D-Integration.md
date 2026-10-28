# TaiWei True-3D Flow Integration

## Overview

This repository integrates 3D Synthesis, True-3D Detailed
Placement, and True-3D CTS into the TaiWei flow. Each point tool has a matching
adapter and explicit Make target in `TaiWei-Pin-3D`, allowing the corresponding
TaiWei stage to be selected without changing the default stage.

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

## Clone

Once the integration branches have been published, clone the integration
branch with its pinned submodules. During local review, use the existing checkout:

```bash
git clone --branch integration/2610 --recurse-submodules https://github.com/CODA-Team/TaiWei.git
cd TaiWei
```

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

A baseline open-source GCD run can then be launched with:

```bash
python3 run_experiments.py --flow ord --tech asap7_3D --case gcd
```

Generated logs, intermediate databases, reports, and results are written below
`logs/`, `objects/`, `reports/`, and `results/`. These directories are ignored
by Git.

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

Continue with `ord-route` and `ord-final` using the same configuration and
variant.
