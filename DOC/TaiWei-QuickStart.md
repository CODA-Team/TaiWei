> **official-2d 分支：** 默认 2D 入口为根目录 `make`，使用官方 ORFS 及其固定工具版本。构建和设计配置请先阅读 [README 的 2D 入口](../README.md#official-2d-分支默认入口)。以下内容为研究版 3D 流程说明。

# TaiWei

**TaiWei** is an open-source end-to-end 3D IC physical design platform that supports research exploration, fair benchmarking and industrial prototyping. It provides a unified RTL-to-GDS 3D reference flow powered by open-source engines, while enabling seamless integration with commercial toolchains and AI-driven autotuning for efficient and scalable optimization.


🔗 **Repository:** [https://github.com/CODA-Team/TaiWei](https://github.com/CODA-Team/TaiWei)

---

## 🚀 Quick Start

### 1. Clone with Submodules

TaiWei relies on several sub-repositories. Ensure you use the `--recurse-submodules` flag:

```bash
git clone --recurse-submodules https://github.com/CODA-Team/TaiWei.git
cd TaiWei

```

### 2. Build the Open-Source Toolchain

Navigate to the research folder to set up the OpenROAD-based environment:

```bash
cd ORFS-Research
sudo ./setup.sh
./build_openroad.sh --local

```

### 3. Run a 3D Flow

Execute the main entry point to run a sample experiment (e.g., the GCD case using the open-source flow). 
You can also inspect the script to see the underlying `make` commands used by the flow.

```bash
cd ../TaiWei-Pin-3D
source env.sh
bash experiment_scripts/gcd.sh

```

> **Output:** All results, including logs and design data, are generated under the `WORK_DIR/` directory.

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

* **`ord`**: Fully open-source (OpenROAD-based). **Recommended** for most researchers.
* **`cds`**: Cadence-based commercial flow.
* **`mixed`**: A hybrid flow combining open-source and commercial toolchains.

**Examples:**

```bash
# Run open-source flow
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
* Cadence Tools (required for the `cds` flow)

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

