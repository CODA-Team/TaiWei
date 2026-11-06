# TaiWei

**TaiWei** is an open-source end-to-end 3D IC physical design platform that supports research exploration, fair benchmarking and industrial prototyping. It provides a unified RTL-to-GDS 3D reference flow powered by open-source engines, while enabling seamless integration with commercial toolchains and AI-driven autotuning for efficient and scalable optimization.


🔗 **Repository:** [https://github.com/CODA-Team/TaiWei](https://github.com/CODA-Team/TaiWei)

---

## 🚀 Quick Start

### 1. Use the native-3d checkout

Use the prepared `native-3d` checkout with its pinned submodules. This branch
selects 3D-Syn, TDP and 3DCTS automatically for OpenROAD runs. The branches are
currently local; see [the integration guide](True-3D-Integration.md).

### 2. Build the Open-Source Toolchain

Navigate to the research folder to set up the OpenROAD-based environment:

```bash
cd ORFS-Research
sudo ./setup.sh
./build_openroad.sh --local

```

### 3. Run a 3D Flow

Execute the main entry point to run a sample experiment (e.g., the GCD case using the native OpenROAD flow).
You can also inspect the script to see the underlying `make` commands used by the flow.

```bash
cd ../TaiWei-Pin-3D
source env.sh
bash test/asap7_3D/gcd/ord/run.sh

```

> **Output:** All results, including logs and design data, are generated under `TaiWei-Pin-3D/{logs,objects,reports,results}/<platform>/<design>/<variant>/`.

---

## 📂 Repository Structure

TaiWei is a **meta-repository**. All components are pinned via Git submodules to ensure perfect reproducibility.

| Directory | Description |
| --- | --- |
| **`ORFS-Research`** | Open-source engines and the underlying flow infrastructure. |
| **`TaiWei-Pin-3D`** | **Main entry point**: The end-to-end 3D RTL-to-GDS flow. |
| **`TaiWei-flow-Agent`** | Optional AI/LLM-based autotuning framework. |

---

## 🛠️ Supported Flows

Users can choose between different toolchains depending on their local environment:

* **`ord`**: Native OpenROAD physical flow with 3D-Syn, TDP and 3DCTS. Genus is required for synthesis.
* **`cds`**: Cadence-based commercial flow.
* **`mixed`**: A hybrid flow combining open-source and commercial toolchains.

**Examples:**

```bash
# Run native OpenROAD flow (Genus required for 3D-Syn)
python3 run_experiments.py --flow ord --tech asap7_3D --case gcd

# Run commercial flow
python3 run_experiments.py --flow cds --tech asap7_nangate45_3D --case gcd

```

---

## 📊 Core Features

### 🔄 Reproducibility

To ensure fair comparison and artifact verification, every run exports:

* **Logs & Stage Checkpoints**: Full history of the design process.
* **Design Data**: DEF, DB and GDS outputs.
* **Standardized Metrics**: Key performance indicators (PPA) for benchmarking.

### 🤖 Optional AI Autotuning

The `TaiWei-flow-Agent` provides an LLM-based agent for:
* Automatic parameter search
* Multi-run design space exploration
* LLM-assisted tuning for optimized results.

---

## 📋 Requirements

* **Required:** Linux (Ubuntu recommended)
* Git >= 2.20
* Python >= 3.8


* **Optional:** Docker / Apptainer (for containerized execution)
* Cadence Genus (required for the native `ord` 3D-Syn frontend); Innovus for the `cds` flow and Cadence evaluation

---

## 📖 Documentation

* **Build Guide:** [`ORFS-Research/README.md`](https://github.com/ieee-ceda-datc/ORFS-Research/blob/master/README.md)
* **Flow Usage:** [`TaiWei-Pin-3D/README.md`](https://github.com/CODA-Team/TaiWei-Pin-3D/blob/main/README.md)
* **Agent Usage:** [`TaiWei-flow-Agent/README.md`](https://github.com/CODA-Team/TaiWei-flow-Agent/blob/main/README.md)


## References ##
To reference Taiwei, please cite:

L. Jiang,  A. B. Kahng, **Z. Wang** (corresponding author) and Z. Zheng, "Invited: Toward Sustainable and Transparent Benchmarking for Academic Physical Design Research",
to appear in Proc. ACM Intl. Symp. on Physical Design, 2026. (Invited Paper)


## Acknowledgments ##
The work of Liwen Jiang, Zhiang Wang and Zhiyu Zheng is supported partly by AI for Science Program, Shanghai Municipal Commission of Economy and Informatization (2025-GZL-RGZN-BTBX-02038), and partly by Fudan Kunpeng\&Ascend Center of Cultivation. Experimental studies are performed at the Fudan Kunpeng\&Ascend Center of Cultivation, Fudan University. 

