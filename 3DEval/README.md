# Taiwei-3D-Eval

Taiwei-3D-Eval is an end-to-end reproducible physical design (PD) flow for face-to-face 3D ICs,
which leverages Pin3D methodology and mature 2D physical design tools (ORFS and Cadence tools) for high-quality 3D IC implementation.
Our flow allows academic researchers to validate and compare their 3D point tools in a full flow context.


## [Quick Start](#quick-start)

### Supported Tools 
- Open-source physical design tools: [OpenROAD-flow-scripts](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts) (ORD)
  - Commit: e19b7a5176e45bae645ba2d5b46f4457e8913b1c
  - Other versions may work but have not been tested. If you encounter any issues, please open an issue in this repository.
- Commerical physical design tools: Cadence tool suites (CDS)
  - Innovus (v21.39)
  - Genus (v21.39)
  
### Environment setup
- Please update the working directory and ORFS directory in env.sh file.
  * `WORK_DIR`: Working directoy (your current path by default)
  * `ORFS_DIR`: Installation directory for OpenROAD-flow-scripts

### Example 1: Run the open-source flow for GCD design (3D stack setting:  ASAP7 + ASAP7)
```bash
# Run open-source flow for the AES design (3D stack setting:  ASAP7 + ASAP7)
python3 run_experiments.py --flow ord --tech asap7_3D --case gcd
```

### Example 2: Run the commerical flow for GCD design (3D stack setting:  ASAP7 + NanGate45)
```bash
# Run open-source flow for the AES design (3D stack setting:  ASAP7 + NanGate45)
python3 run_experiments.py --flow cds --tech asap7_nangate45_3D --case gcd 
```


## Table of Contents

*   [Design Enablement](#design-enablement)
*   [Our Method](#our-method)

  *   [ORFS-Research Pin-3D Flow Overview](#orfs-research-pin-3d-flow-overview)
  *   [3D PDK Mapping (F2F with HBTs)](#3d-pdk-mapping-f2f-with-hbts)
  *   [2D Synthesis](#2d-synthesis)
  *   [2D and 3D Floorplan](#2d-and-3d-floorplan)
  *   [3D Placement & Optimization](#3d-placement--optimization)
  *   [3D Clock Tree Synthesis & Legalization](#3d-clock-tree-synthesis--legalization)
  *   [3D Routing](#3d-routing)
  *   [Extraction & Metrics](#extraction--metrics)

  *   [Prerequisites](#prerequisites)
  *   [One-line End-to-End Runs](#one-line-end-to-end-runs)
  *   [Stage-by-Stage (Make targets)](#stage-by-stage-make-targets)
*   [Outputs](#outputs)
*   [References](#references)
*   [Appendix](#Appendix)

  *   [Experimental Tables and Plots](#Experimental-Tables-and-Plots)

## Design Enablement

We provide a minimal, research‑ready enablement to run a **2D‑tools–driven Pin‑3D flow** on both OpenROAD (ORFS) and Cadence. You may plug in your own PDKs, libraries, and RC models (respecting licenses). A typical setup includes: 2D and 3D PDK files, PDN strategies, and timing/RC libraries.

|                          | OpenROAD (ORFS) & Innovus (Cadence)          |
| :----------------------- | :------------------------------------------- |
| Physical library         | 2D & 3D LEF / tech LEF (REAL and COVER)      |
| Liberty timing           | `.lib` (one or more corners)                 |
| PDN strategy             | `.tcl` (ORFS and Cadence)                    |
| RC lookup (for precise)  | `.rules`, `.tch` (QRC)                       |
| Parasitic extraction     | OpenRCX / Quantus (QRC)                      |

> Notes: (i) 3D F2F vertical interconnect (HBTs) is modeled via library pins/macros and/or pseudo‑layers; (ii) Our 2D and 3D PDK are takern and generated from [[nangate45]https://github.com/ieee-ceda-datc/ORFS-Research/tree/main/flow/platforms/nangate45].


> **Note on Hybrid Flows**
>
> For experimental runs that combine OpenROAD and Cadence tools, you can set `FLOW_VARIANT=hybrid`. The flow stages can be customized in `config.mk`. Please be aware that this feature is still under development. For implementation details, refer to the example scripts in `test/` and the design configurations in `designs/`.

## Our Method

### ORFS-Research Pin-3D Flow Overview

Our flow targets **Face‑to‑Face (F2F) 3D ICs with Hybrid Bonding Terminals (HBTs)**. We deliberately **reuse proven 2D capabilities** and add just enough cross‑die abstractions and constraints so new 3D research modules can be **inserted, replaced, or ablated** with minimal friction.

<p align="center">
  <img alt="COP3D_FLOW" height="400" src="./README.assets/COP3D_FLOW.png">
</p>

High‑level stages and the **actual make targets** used in this repo are:

1.  **Per‑die 2D Synthesis** → gate‑level netlists
    *Targets:* `ord-synth` / `cds-synth` (with `config2d.mk`).
2.  **2D → 3D Floorplanning & Tiering** → floorplan/IO, tier partition, 3D view generation, PDN skeleton
    *Targets:* `ord-preplace`, `ord-tier-partition`, `ord-pre`, `ord-3d-pdn` / `cds-preplace`, `cds-tier-partition`, `cds-pre`, `cds-3d-pdn`.
3.  **3D‑aware Placement** → init + alternating upper/bottom refinements with bottom/upper fixed and transparent
    *Targets:* `ord-place-init`, `ord-place-upper`, `ord-place-bottom`, `ord-pre-cts` (loop); Cadence: `cds-place-init`, `cds-place-upper`, `cds-place-bottom`, `cds-place-finish`.
4.  **Optimization & Legalization** → Optimize and Legalize bottom/upper with upper/bottom fixed and transparent
    *Targets:* `ord-legalize-bottom`, `ord-legalize-upper` / `cds-legalize-bottom`, `cds-legalize-upper`
5.  **CTS** → bottom die CTS with upper fixed and transparent
    *Targets:* `ord-cts` / `cds-cts`.
6.  **3D Routing** → global+detail routing and get routing aware HBT positions
    *Targets:* `ord-route` / `cds-route`.
7.  **Reporting & (Optional) Signoff Hooks** → final summaries, optional HotSpot (currently not enable for spef not done)
    *Targets:* `ord-finish` (currently using cds-final for unified metrics and validation), `ord-hotspot` / `cds-final`, `cds-hotspot`.

> **Research hooks.** Swap in partitioners, placement objectives, or CTS policies by editing TCLs in `scripts_openroad/` or `scripts_cadence/` and the per‑stage configs under `designs/`.

### 3D PDK Mapping (F2F with HBTs)

<p align="center">
  <img alt="Results_aes" height="400" src="./README.assets/PDK_Preparation.png">
</p>

*   **Layer stacks**: treat each die’s stack as a conventional 2D PDK and define a bonding interface between the top metals.
*   **HBT representation**: either (a) explicit HBT pins/macros in LEF/DEF, and/or (b) pseudo‑via layers with spacing/pitch rules (currently using (b)).
*   **Cover LEFs for alternation**: we provide *cover* LEF variants to simplify alternating placement:
  *   `config_bottom_cover.mk` → uses **bottom.cover** LEF (bottom fixed; place **upper**)
  *   `config_upper_cover.mk` → uses **upper.cover** LEF (upper fixed; place **bottom**)
*   **RC templates**: per‑unit R/C for HBTs and inter‑die segments are merged into SPEF during PEX (OpenRCX/Quantus, currently not enable, using lef RC).
*   **Constraint symmetry**: maintain consistent names/locations across dies for cross‑die ports and nets (SDC/DEF/TCL) to stabilize legalization and routing.

### 2D Synthesis

*   **OpenROAD**: `ord-synth` (Yosys/ABC via ORFS) per die.
*   **Cadence**: `cds-synth` (Genus) per die.
  **Inputs:** RTL, `.lib`, SDC.
  **Key artifacts:** `results/.../1_synth.v`, `1_synth.sdc` for later stages.

### 2D and 3D Floorplan

<p align="center">
  <img alt="Results_aes" height="400" src="./README.assets/Floorplan.png">
</p>

*   **2D pre‑place** (`ord-preplace` / `cds-preplace`, with `config2d.mk`): core/row/site, IO placement; prepares for partitioning.
*   **Tier partition** (`ord-tier-partition` / `cds-tier-partition` or `cds-docker-partition`): OpenROAD TritonPart splits the design; outputs `partition.txt` and copies 2D artifacts into `<platform>_3D/`.
*   **3D view generation** (`ord-pre` / `cds-pre`, with `config.mk`): produces `${DESIGN_NAME}_3D.fp.def` and `.v` aligned with the partition.
*   **3D PDN** (`ord-3d-pdn` / `cds-3d-pdn`): builds per‑die grids and updates floorplan artifacts.
  *Artifacts promoted/canonicalized:* `2_6_floorplan_pdn.def → 2_floorplan.def`, corresponding `.v`/`.sdc`.

### 3D Placement & Optimization

<p align="center">
  <img alt="Results_aes" height="400" src="./README.assets/Pin_3D_Placement.png">
</p>

*   **Init**: `ord-place-init` / `cds-place-init` seeds placement and applies cross‑die constraints.
*   **Alternating refinement**: loop `ord-place-upper` (with `config_bottom_cover.mk`) and `ord-place-bottom` (with `config_upper_cover.mk`) for `iteration` times to reduce cross‑die HPWL and improve timing under HBT legality.
*   **Cadence finish**: `cds-place-finish` snapshots `3_place.{def,v,sdc}` for Legalization.

### 3D Optimization & Legalization

*   **Split legalization**: `ord-legalize-upper` and `ord-legalize-bottom` run optimization & legalizations die by die.
  *Cadence analogue:* `cds-legalize-upper` and `cds-legalize-bottom`.

### 3D Clock Tree Synthesis

<p align="center">
  <img alt="CTS_ORD_gcd" height="300" src="./README.assets/CTS_ORD_gcd.png">
  <img alt="CTS_CDS_gcd" height="300" src="./README.assets/CTS_CDS_gcd.png">
</p>


*   **CTS**: `ord-cts` / `cds-cts` builds bottom die trees with alignment constraints.

### 3D Routing

<p align="center">
  <img alt="Results_aes" height="400" src="./README.assets/Routing_View.png">
</p>

*   **OpenROAD**: `global_route.tcl` then `detail_route.tcl` (`ord-route`), yielding `5_2_route.odb` → promoted to `5_route.odb`; SDC propagated to `5_route.sdc`.
*   **Cadence**: `cds-3d_route.tcl` via `cds-route`.
*   **Abstractions**: HBTs modeled as pins/macros or constrained pseudo‑layers with min‑pitch/spacing and antenna/DRC checks where applicable.

### Extraction & Metrics

*   **PEX (optional; platform‑dependent)**: OpenRCX (OpenROAD) or Quantus (Cadence) can generate per‑die SPEF with verticals merged; coupling‑on/off variants supported for experiments.
*   **Final reporting**: `ord-finish` runs `final_report.tcl` (and optional `generate_fig.tcl`) to collate timing/power/HPWL/congestion/clock; Cadence uses `cds-final` to produce comparable reports. Currently we only enables Cadence final for unified metrics and validation.
*   **Thermal (optional)**: `ord-hotspot` / `cds-hotspot` provides a reproducible HotSpot harness; outputs are copied to `results/.../hotspot_outputs/`.

## Quick Start







### Prerequisites

*   **Toolchains**: This project supports two toolchains.
  *   **OpenROAD**: We recommend our [ORFS-Research](https://github.com/ieee-ceda-datc/ORFS-Research) fork of [OpenROAD-flow-scripts](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts).
  *   **Cadence**: A valid license for Genus and Innovus is required.
*   **PDK and Libraries**:
  *   A Process Design Kit (PDK) and standard cell libraries are necessary. We provide a demo platform based on NanGate45 (`platforms/NanGate45_3D`).
  *   You can integrate your own platform by adding it to the `platforms/` directory and updating the configuration files.
*   **Environment Setup**:
  *   For local OpenROAD builds, source the `env.sh` script to set the `OPENROAD_EXE` variable.
  *   For the Cadence flow, ensure that its tool executables are in your system's `PATH`.
*   **Container for Partitioning (Optional)**:
  *   If you run the Cadence flow without a local OpenROAD installation, a container with OpenROAD is needed to execute the open-source TritonPart partitioner. This is done via the `cds-docker-partition` `make` target.

### Stage-by-Stage (Make targets)

> The rows below mirror your **actual bash pipelines** (`test/aes/ord/run.sh` and `test/aes/cds/run.sh`). Targets that consume specific configs are annotated.

| Stage                   | OpenROAD target            | Cadence target             | Notes                                                        |
| :---------------------- | :------------------------- | :------------------------- | :----------------------------------------------------------- |
| **Clean**               | `clean_all`                | `clean_all`                | Remove `results/ reports/ logs/ objects/`.                   |
| **2D Synthesis**        | `ord-synth`                | `cds-synth`                | RTL → gate with 2D PDK. *(Uses `config2d.mk`)*               |
| **2D Pre‑place**        | `ord-preplace`             | `cds-preplace`             | Floorplan/IO staging for partitioning. *(Uses `config2d.mk`)* |
| **Tier Partition**      | `ord-tier-partition`       | `cds-tier-partition`       | Split into upper/bottom tiers. *(Uses `config2d.mk`)*        |
| **3D Prep (views)**     | `ord-pre`                  | `cds-pre`                  | Generate 3D views / import partition artifacts. *(Uses `config.mk`)* |
| **3D PDN**              | `ord-3d-pdn`               | `cds-3d-pdn`               | Unified PDN. *(Uses `config.mk`)*                            |
| **Place Init**          | `ord-place-init`           | `cds-place-init`           | Initialize cross‑tier placement. *(Uses `config.mk`)*        |
| **Place — Upper Tier**  | `ord-place-upper`          | `cds-place-upper`          | Alternate with bottom for `iteration` loops. *(Uses `config_bottom_cover.mk`)* |
| **Place — Bottom Tier** | `ord-place-bottom`         | `cds-place-bottom`         | Alternating cross‑tier refinement. *(Uses `config_upper_cover.mk`)* |
| **Place Finish**        | `ord-pre_cts`              | `cds-place-finish`         | Refinement. *(Uses `config.mk`)*                             |
| **Legalize — Upper**    | `ord-legalize-upper`       | `cds-legalize-upper`       | Legalize upper tier. *(Uses `config_bottom_cover.mk`)*       |
| **Legalize — Bottom**   | `ord-legalize-bottom`      | `cds-legalize-bottom`      | Legalize bottom tier and merge. *(Uses `config_upper_cover.mk`)* |
| **CTS**                 | `ord-cts`                  | `cds-cts`                  | Clock trees per die with cross‑die alignment. *(Uses `config.mk`)* |
| **Route (3D)**          | `ord-route`                | `cds-route`                | Detailed routing and create HBT vias. (Uses `config.mk`)*    |
| **Final / Reports**     | `ord-final`                | `cds-final`                | Report collation. *(Uses `config.mk`)*                       |
| **Thermal / Hotspot**   | `ord-hotspot`              |                            | Reuses OpenROAD HotSpot harness.                             |

## Outputs

After runs, you will typically see:

```
results/    # DEF/ODB/LEF/SPEF/GDS, etc.
reports/    # timing/power/HPWL/congestion/clock, etc.
logs/       # tool logs (OpenROAD/Cadence), final summary, plots
objects/    # intermediate DBs and caches
```

## References

[1] S. Jadhav. 2025. "Architecture of 3 Dimensional Integrated Circuits." 3D ICs. Accessed: Aug. 14, 2025. [Online]. Available: [https://medium.com/3d-ics/architecture-of-3-dimensional-integrated-circuits-602f5d9a7b58](https://medium.com/3d-ics/architecture-of-3-dimensional-integrated-circuits-602f5d9a7b58)

[2] G. Murali, S. M. Shaji, A. Agnesina, G. Luo, and S. K. Lim. 2022. "ART-3D: Analytical 3D Placement with Reinforced Parameter Tuning for Monolithic 3D ICs." In *Proceedings of the 2022 International Symposium on Physical Design* (ISPD '22). ACM, Virtual Event, Canada, 97–104. [https://doi.org/10.1145/3505170.3506725](https://doi.org/10.1145/3505170.3506725).

[3] Y. Zhao, L. Zou, and B. Yu. 2025. "Invited: Physical Design for Advanced 3D ICs: Challenges and Solutions." In *Proceedings of the 2025 International Symposium on Physical Design* (ISPD '25). ACM, Austin, TX, USA, 209–216. [https://doi.org/10.1145/3698364.3709127](https://doi.org/10.1145/3698364.3709127).

[4] L. Bamberg, A. Garcia-Ortiz, L. Zhu, S. Pentapati, D. E. Shim, and S. K. Lim. 2020. "Macro-3D: A Physical Design Methodology for Face-to-Face-Stacked Heterogeneous 3D ICs." In *2020 Design, Automation & Test in Europe Conference & Exhibition* (DATE). IEEE, Grenoble, France, 37–42. [https://doi.org/10.23919/DATE48585.2020.9116297](https://doi.org/10.23919/DATE48585.2020.9116297).

[5] Y. Shi, A. (others). 2025. "Open3DBench: Open-Source Benchmark for 3D-IC Backend Implementation and PPA Evaluation." *arXiv preprint* arXiv:2503.12946 (Mar. 17, 2025). [https://doi.org/10.48550/arXiv.2503.12946](https://doi.org/10.48550/arXiv.2503.12946).

[6] S. S. K. Pentapati, K. Chang, V. Gerousis, R. Sengupta, and S. K. Lim. 2020. "Pin-3D: a physical synthesis and post-layout optimization flow for heterogeneous monolithic 3D ICs." In *Proceedings of the 39th International Conference on Computer-Aided Design* (ICCAD '20). ACM, Virtual Event, USA, 1–9. [https://doi.org/10.1145/3400302.3415720](https://doi.org/10.1145/3400302.3415720).

[7] H. Park, B. W. Ku, K. Chang, D. E. Shim, and S. K. Lim. 2021. "Pseudo-3D Physical Design Flow for Monolithic 3D ICs: Comparisons and Enhancements." *ACM Transactions on Design Automation of Electronic Systems* 26, 5 (Sept. 2021), 1–25. [https://doi.org/10.1145/3453480](https://doi.org/10.1145/3453480).

[8] S. Liu, J. (others). 2024. "Routing-aware Legal Hybrid Bonding Terminal Assignment for 3D Face-to-Face Stacked ICs." In *Proceedings of the 2024 International Symposium on Physical Design* (ISPD '24). ACM, Taipei, Taiwan, 75–82. [https://doi.org/10.1145/3626184.3633322](https://doi.org/10.1145/3626184.3633322).

[9] S. Panth, K. Samadi, Y. Du, and S. K. Lim. 2017. "Shrunk-2-D: A Physical Design Methodology to Build Commercial-Quality Monolithic 3-D ICs." *IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems* 36, 10 (Oct. 2017), 1716–1724. [https://doi.org/10.1109/TCAD.2017.2648839](https://doi.org/10.1109/TCAD.2017.2648839).

[10] P. Vanna-Iampikul, C. Shao, Y.-C. Lu, S. Pentapati, and S. K. Lim. 2021. "Snap-3D: A Constrained Placement-Driven Physical Design Methodology for Face-to-Face-Bonded 3D ICs." In *Proceedings of the 2021 International Symposium on Physical Design* (ISPD '21). ACM, Virtual Event, USA, 39–46. [https://doi.org/10.1145/3439706.3447049](https://doi.org/10.1145/3439706.3447049).

[11] D. Kim, M. Kim, J. Hur, J. Lee, J. Cho, and S. Kang. 2024. "TA3D: Timing-Aware 3D IC Partitioning and Placement by Optimizing the Critical Path." In *Proceedings of the 2024 ACM/IEEE International Symposium on Machine Learning for CAD* (MLCAD '24). ACM, Salt Lake City, UT, USA, 1–7. [https://doi.org/10.1145/3670474.3685957](https://doi.org/10.1145/3670474.3685957).

[12] X. Zhao, J. (others). 2025. "Toward Advancing 3D-ICs Physical Design: Challenges and Opportunities." In *Proceedings of the 30th Asia and South Pacific Design Automation Conference* (ASP-DAC '25). ACM, Tokyo, Japan, 294–301. [https://doi.org/10.1145/3658617.3703135](https://doi.org/10.1145/3658617.3703135).

[13] *Innovus User Guide*. Cadence Design Systems, Inc.

[14] *Innovus Text Command Reference*. Cadence Design Systems, Inc.

<a id="Appendix"></a>

## Appendix

### PDK Preparation

PDK preparation is a key step for 3D IC design flow. The 3D PDK must be simple enough to support robust flows and, at the same time, expressive enough to expose meaningful differences when evaluating new tools and algorithms.

<p align="center">
  <img alt="ASAP7_3D_PDK" width="600" src="./README.assets/ASAP7_3D_PDK.png">
  <br>
  <em>Figure: Metal stack, PDN strategy, tier strategy in the 3D ASAP7 PDK.</em>
</p>

The figure above shows the metal stack, power delivery network (PDN) strategy and tier strategy for our 3D ASAP7 PDK, which is derived from the 3D ASAP7 PDK. Starting from this 2D base, we construct a homogeneous 3D PDK by replicating the 2D metal stack and design rules for each tier, and by adding an additional normal cut layer for vertical connections that represent HBTs between tiers. Our 3D PDN strategy applies the 2D PDN structure symmetrically to both the top and bottom tiers. This approach is motivated by the nature of F2F integration, where each die is fabricated independently before bonding. This necessitates a separate power supply for each tier. This requirement is particularly important for heterogeneous designs, where the standard-cell libraries on each tier may have distinct power voltage requirements.

<p align="center">
  <img alt="SITE1" height="200" src="./README.assets/SITE1.pdf" style="margin-right: 10px;">
  <img alt="SITE2" height="200" src="./README.assets/SITE2.pdf">
  <br>
  <em>Figure: Rebuild rows for heterogeneous legalization.</em>
</p>

For standard-cell and library creation, we adopt the strategy shown above. We construct the 3D standard-cell libraries by duplicating a 2D cell library onto each tier, thereby creating a homogeneous 3D cell set. For each logical cell, we generate separate LEF views for the bottom and top tiers. In addition, we create LEF variants with the **COVER** attribute for both tiers. These **COVER** views provide a **transparent** physical abstraction that preserves footprint and blockage information while decoupling detailed device behavior. This strategy allows us to reuse existing 2D tools for floorplanning, PDN planning, and routing, while still modeling the 3D structure and interactions needed for Pin-3D experiments.

For **homogeneous designs**, both tiers use the same standard-cell library, which simplifies the setup. We create tier-specific libraries by duplicating the 2D LEF and LIB files and adding distinct suffixes **_bottom** and **_upper** to distinguish cells on each tier. Because the cell footprints and timing characteristics are identical across tiers, the design can be synthesized once using a single library. The resulting netlist is then partitioned, and cells are mapped to their respective tiers. This approach allows for shared row structures and a unified timing analysis during placement and optimization.

For **heterogeneous designs**, where each tier uses a different standard-cell library, two key challenges arise: (1) how to synthesize a single design that targets multiple distinct PDKs, and (2) how to ensure legal placement and optimization on each tier. Our solution for (1) is to synthesize the design against a common **logical library** that contains only the cells shared between the two tier-specific libraries. During the floorplanning stage, these logical cells are then mapped to their corresponding physical cell masters on the appropriate tier. Any tier-specific pins that are not part of the common logical cell abstraction are defined as internal pins in the logical library, effectively hiding them from the synthesis tool to ensure a valid, unified netlist. And for (2), we implement a **tier strategy** during placement and optimization. When optimizing one tier, we load the **COVER** view of the other tier to fix its instances, and we configure the environment to only allow cells from the active tier. This ensures that each tier is optimized using its own physical library, while still maintaining the overall 3D design integrity.

Using this PDK preparation strategy, we can effectively set up both homogeneous and heterogeneous Pin-3D flows that leverage existing 2D tools while accurately modeling the unique aspects of 3D integration.

### Physical Design Flow Details

This subsection describes the implementation of each stage in the flow. We detail the key procedures, file dependencies, and design decisions that enable robust 3D physical design within a standard 2D toolchain.

**Stage 1: Synthesis and 2D abstraction**

In our flow, the logic synthesis stage employs Yosys or commercial tool based on a 2D standard-cell library. This stage reads RTL sources and generates a flat gate-level netlist along with timing constraints. We adopt a flat netlist structure rather than hierarchical modules because, in the subsequent floorplanning and partitioning stages, we use TritonPart for timing-driven bipartitioning, and cells within a logical module might be assigned to different tiers.

For homogeneous designs, since the upper and lower tiers utilize the same process node, there are no logical cell equivalence issues. We directly use the standard 2D Process Design Kit (PDK) for logic synthesis. In the subsequent partitioning stage, cells can be assigned to the upper or lower tier without conflict.

For heterogeneous designs, we adopt a unified synthesis strategy to handle different process nodes. We synthesize based on a simplified but logically complete 2D logical library. This library contains the intersection of available cells in the target technologies, provides multiple sizing options, and establishes a one-to-one mapping of master cells and pins between different processes. For cells that are logically equivalent but have different ports, we convert the extra pins in the physical library into internal pins within the logical library. Consequently, the synthesis tool ignores these pins during mapping, ensuring the generated netlist is logically equivalent. This approach guarantees that the design achieves equivalent logical functions while allowing cells to be flexibly moved between tiers. The resulting netlist remains technology-neutral regarding the final 3D stacking, and the specific mapping to tier-dependent physical libraries occurs only after the partitioning stage. This ensures a valid and unified netlist that can be partitioned by TritonPart without requiring early commitment to specific tier technologies.

Key artifacts from this stage include the synthesized Verilog netlist, SDC constraints, and a cell mapping specification. This specification defines how the logical cells in the 2D PDK map to tier-specific physical masters and pin names.

**Stage 2: 2D Floorplan, Tier Partitioning, and 3D Floorplan Construction**

This stage transforms the logical netlist into a physically partitioned 3D design, encompassing both spatial planning and critical power distribution. The process begins with the creation of an initial 2D floorplan, where die dimensions are derived from core utilization and aspect ratio, and primary I/O pins are placed along the boundary. Subsequently, the 2D floorplan and netlist are passed to TritonPart for timing-driven bipartitioning.

To optimize partition quality, we employ a parameter sweeping strategy controlled by the environment variables `PAR_BAL_LO`, `PAR_BAL_HI`, and `PAR_BAL_ITERATION`. Specifically, we uniformly sample target balance constraints from the interval in the range `[PAR_BAL_LO, PAR_BAL_HI]` over `PAR_BAL_ITERATION` iterations. For heterogeneous designs, we typically assign larger balance factors to accommodate the disparity in average cell sizes between tiers. This adjustment ensures that the final utilization on each tier converges toward the target utilization.

<p align="center">
  <img alt="UBfactorvsCrossTierNetSize" height="300" src="./README.assets/UBfactorvsCrossTierNetSize.png">
  <br>
  <em>Figure: Impact of balance constraint on cross-tier net count.</em>
</p>

For each sampled constraint, TritonPart generates a candidate solution; the solution yielding the minimum cutsize is then selected (see Figure above). This final partition assigns every standard cell instance to either the top or bottom tier, thereby establishing the foundation for 3D implementation. The resulting cutsize serves as an early indicator of cross-tier connectivity, which directly impacts timing metrics and routing complexity. However, the final count of Hybrid Bonding Terminals (HBTs) is not determined at this stage, as subsequent optimization and clock tree synthesis steps may introduce additional cross-tier connections.

Using the resulting partition file, a conversion script translates the unified 2D design into tier-aware 3D views. This translation involves updating instance master names to their tier-specific physical counterparts (e.g., renaming a logical `AND2_X1` to `AND2_X1_bottom` or `AND2x2_ASAP7_75t_R_upper`) and remapping logical pin names to logical pin for heterogeneous designs. Furthermore, physical pins absent in the logical abstraction, such as scan-enable pins, are automatically tied off to constant values.

With tier-specific views ready, the 3D floorplan is finalized by constructing independent PDNs for each tier. Symmetrical power grids are built separately using lower metal layers (e.g., `M1--M9`) for the bottom tier and upper metal layers (e.g., `M9_m--M1_m`) for the top tier, ensuring no unintended vertical shorts occur. Finally, a controlled vertical connection is established at designated Hybrid Bonding Terminal locations to bridge the isolated grids, completing the 3D PDN.

<p align="center">
  <img alt="Bot_PDN" width="45%" src="./README.assets/Bot_PDN.png">
  <img alt="Top_PDN" width="45%" src="./README.assets/Top_PDN.png">
  <br>
  <img alt="BottomCell" width="45%" src="./README.assets/BottomCell.png">
  <img alt="TopCell" width="45%" src="./README.assets/TopCell.png">
  <br>
  <em>Figure: Heterogeneous PDN grid and cell placement.</em>
</p>

**Stage 3: Iterative 3D placement**

Placement begins with an initial global placement step. Although the upper and bottom tiers use different LEF and LIB files, all cells are defined with the **CORE** attribute. Consequently, the 2D placer treats all cells as movable and accounts for them in the density calculation. This generates a starting layout without specific timing or congestion optimization, providing a neutral baseline that does not favor either tier.

We then refine the placement through an iterative, die-by-die process using a specific tier strategy. In each iteration, we fix the placement of one tier while optimizing the other. Specifically, we load the **COVER** views for the inactive tier, lock all instances on that tier, and configure the environment for the active tier. This configuration involves setting constraints to prevent the use of cells from the inactive tier, updating placement rows to match the active tier's specifications, and assigning the correct tie and filler cells.

Once the environment is set, we run global placement in timing-driven and routability-driven modes. We configure the tool to refine the existing layout rather than starting from scratch. After each pass, we swap the active and inactive tiers and repeat the process. In our flow, a single round of die-by-die iterative optimization is typically sufficient.

Following this iterative refinement, we perform detailed placement and optimization for each tier individually. We again apply the tier strategy to fix the inactive tier while enabling standard 2D optimization settings for the active tier. This allows the tool to insert buffers for timing optimization, manage tie-cell fanout, and finally run detailed placement to legalize cell positions and further improve layout quality.

**Stage 4: 3D clock tree synthesis**

We perform clock tree synthesis (CTS) on the bottom tier while keeping the top tier fixed. We apply the tier strategy to optimize the bottom tier, using sink clustering and designated buffer cells to build the clock tree. Cells on the upper tier that require a clock signal obtain it from buffers located on the bottom tier. After synthesis, for the OpenROAD flow, we run an additional detailed placement step to legalize any newly inserted buffers.

<p align="center">
  <img alt="CLK_Net" width="45%" src="./README.assets/CLK_Net.png">
  <img alt="Route" width="45%" src="./README.assets/Route.png">
  <br>
  <img alt="HBT" width="45%" src="./README.assets/HBT.png">
  <img alt="Final" width="45%" src="./README.assets/Final.png">
  <br>
  <em>Figure: Clock Tree, Routing Signal Nets, HBT assignment, and Final Layout.</em>
</p>

Clock signals for the top tier are handled as standard signal nets that connect to the bottom-tier clock tree through inter-tier vias. This method leverages our unified 2D representation, where vertical connections are modeled as standard vias on a dedicated cut layer. This allows the tool to route clock signals across tiers without requiring special 3D-specific handling.

**Stage 5: 3D routing and post-route optimization**

Global and detailed routing are performed using standard 2D routing engines. Our unified technology representation models hybrid bonding terminals as special via layers within the technology file. For instance, a specific cut layer is defined to bridge the top metal of the bottom tier and the bottom metal of the upper tier. When the router connects a net across tiers, it automatically inserts this inter-tier via without requiring specialized 3D commands.

Following routing, we perform parasitic extraction to capture the resistance and capacitance of the routed interconnects. Since our unified technology LEF inherently contains 3D information, it characterizes all metal layers and via types, including inter-tier connections. This allows the extraction tool to generate SPEF files that accurately reflect the 3D structure, which are then used for final timing analysis and verification.

**Stage 6: Metrics collection and reporting**

We collect Quality of Results (QoR) metrics at multiple checkpoints throughout the flow. For OpenROAD, we use the reporting commands integrated into ORFS-Research. These commands log runtime, memory usage, wirelength, congestion maps, timing slack, and Design Rule Violations (DRVs) counts in a structured JSON format that follows the METRICS2.1 convention.

For the commercial reference flow, we define a custom procedure to extract similar data. This procedure invokes standard timing, power, and verification commands, then parses the output reports to extract key metrics and write them to CSV files.

All metrics are version-controlled alongside the flow scripts and benchmark inputs. This enables reproducible evaluation and allows for long-term tracking of improvements in tools and algorithms.

### Experimental Tables and Plots



We welcome suggestions for improvements or contributions of better materials to this repository.

Please contact us via email or through GitHub issues and pull requests; our contact information is listed below. Finally, please read the header notices in all TCL scripts that invoke commercial EDA tools. We thank Cadence and Synopsys for allowing us to share, in this academic context, excerpts of their copyrighted intellectual property for researchers’ use.

## Contacts

*   **Zhiang Wang** — [zhiangwang@fudan.edu.cn](mailto:zhiangwang@fudan.edu.cn)
*   **Zhiyu Zheng** — [zyzheng24@m.fudan.edu.cn](mailto:zyzheng24@m.fudan.edu.cn)
*   **Keren Zhu** — [krzhu@fudan.edu.cn](mailto:krzhu@fudan.edu.cn)
*   **Yuhao Ren** — [yhren24@m.fudan.edu.cn](mailto:yhren24@m.fudan.edu.cn)