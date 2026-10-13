# TaiWei True-3D Flow Integration

## Overview

This repository integrates 3D Synthesis, D3D Partitioning, True-3D Detailed
Placement, and True-3D CTS into the TaiWei flow. Each point tool has a matching
adapter and explicit Make target in `TaiWei-Pin-3D`, allowing the corresponding
TaiWei stage to be selected without changing the default stage.

## Integration Layout

```text
TaiWei-Integration/
├── ORFS-Research/
│   └── tools/
│       ├── yosys/
│       │   └── passes/3dsyn/
│       ├── OpenROAD/
│       │   └── src/
│       │       ├── 3ddp/
│       │       └── 3dcts/
│       └── D3D-Partitioner/
└── TaiWei-Pin-3D/
    ├── scripts_3dsyn/
    ├── scripts_d3d_partition/
    ├── scripts_3ddp/
    ├── scripts_3dcts/
    └── Makefile
```

`ORFS-Research` contains the point-tool implementations and the OpenROAD/Yosys
toolchain. The matching `scripts_*` directories in `TaiWei-Pin-3D` provide the
flow adapters, input/output validation, and standard TaiWei handoffs. Detailed
configuration and stage contracts are documented in each adapter directory.

## Clone

Clone the repository normally. Do not use `--recurse-submodules`.

```bash
git clone <private-repository-url> TaiWei-Integration
cd TaiWei-Integration
```

## Build OpenROAD and Yosys

Install the ORFS dependencies, then build the OpenROAD and Yosys sources stored
in this repository. `--no_init` is required because the original ORFS
submodules are not used.

```bash
cd ORFS-Research
sudo ./setup.sh
./build_openroad.sh --local --no_init --threads 16
```

The default installation is written below:

```text
ORFS-Research/tools/install/OpenROAD
ORFS-Research/tools/install/yosys
```

Use another positive value for `--threads` as appropriate for the build host.
Do not use `--latest`, `--or_branch`, or `--or_repo` in this source checkout:
those options are intended for a nested OpenROAD Git repository and may bypass
the integrated source snapshot.

## Build the CPU D3D Partitioner

D3D Partitioner has an independent build and does not participate in
`build_openroad.sh`.

From `ORFS-Research`, run:

```bash
make -C tools/D3D-Partitioner/d3d-partition-driver setup JOBS=16
```

If no supported Conda executable is on `PATH`, specify it explicitly:

```bash
make -C tools/D3D-Partitioner/d3d-partition-driver setup \
  CONDA_EXE=/path/to/micromamba \
  JOBS=16
```

The default environment, build tree, and installation are isolated under:

```text
ORFS-Research/.conda/taiwei-d3d-cpu
ORFS-Research/tools/build/d3d-partitioner
ORFS-Research/tools/install/d3d-partitioner
```

The setup target performs its own installation check. It can also be repeated
explicitly with:

```bash
make -C tools/D3D-Partitioner/d3d-partition-driver check \
  ENV_PREFIX="$PWD/.conda/taiwei-d3d-cpu"
```

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

### D3D Partitioner

After the normal synthesis, floorplan, and IO stages have produced the
partition input handoff, run:

```bash
make DESIGN_CONFIG=designs/asap7_3D/gcd/config2d.mk \
     FLOW_VARIANT=d3d_gcd \
     ord-tier-partition-d3d
```

The stage publishes TaiWei's standard `partition.txt`; the original
`ord-tier-partition` target remains available for TritonPart.

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
