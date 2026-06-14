<div align="center">



<p align="center">
  <img src="fig/headline.png" alt="Exploration of the boundaries of detection capability for IRSTD">
</p>

</div>

## 🔗 Quick Link
Try our:

🗂️[HIT-EWIRSTD](https://pan.baidu.com/s/19FWo0dn7FMTA0YJ7FJ3L0g?pwd=3q97)
Dataset
<p align="left">
  <img src="fig/dataset.pdf" alt="Dataset">
</p>

🧰[Statistical-Toolbox-for-SNR-and-TSNR-of-Motion-IRSTD](https://github.com/MYQHY/Statistical-Toolbox-for-SNR-and-TSNR-of-Motion-IRSTD)

## 🔥 Overview

<p align="center">
  <img src="assets/teaser.png" width="92%">
</p>

**YourProjectName** is a robust and efficient framework for **[your task, e.g., RGB-Event spacecraft pose estimation / remote sensing object detection / infrared small target detection]**.

It is designed to address the following challenges:

- 🌗 **Extreme illumination variation**
- 🛰️ **Complex space / remote sensing scenarios**
- 🎯 **Small, weak, or non-cooperative targets**
- 🔄 **Cross-domain generalization**
- ⚡ **Efficient deployment on edge devices**

---

## 📢 News

- **2026-06-10**: 🚀 Project page is online.


---

## ✨ Highlights

### 🌗 Innovative ideas inspired by event sensors

<img src="fig/abstract.pdf" width="50%">

### 🧠 Break through the existing upper limit of extremely weak target detection capability

### 🧩 Broader applicability

### ⚡ Efficient and Reproducible



## 🎬 Demo

<table>
  <tr>
    <td align="center" width="33%">
      <img src="fig/NUDT-MIRSDT-Sequence2_mask_visualization.gif" width="100%">
      <br>
      <b>NUDT-MIRSDT</b>
    </td>
    <td align="center" width="33%">
      <img src="fig/NUDT-MIRSDT-HiNo-Sequence6_mask_visualization.gif" width="100%">
      <br>
      <b>NUDT-MIRSDT-HiNo(Invisible to the naked eye)</b>
    </td>
    <td align="center" width="33%">
      <img src="fig/HIT_EWIRSTD-Sequence55_mask_visualization.gif" width="100%">
      <br>
      <b>HIT_EWIRSTD(Invisible to the naked eye)</b>
    </td>
  </tr>
</table>



## 🏆 Main Results

### Comparison with State-of-the-Art Methods

| Method | Venue | Modality | Backbone | Metric-1 ↑ | Metric-2 ↑ | Metric-3 ↓ | Params ↓ | FPS ↑ |
|---|---|---|---|---:|---:|---:|---:|---:|
| Method A | CVPR 2023 | RGB | ResNet-50 | 75.2 | 68.1 | 12.4 | 45.3M | 32.1 |
| Method B | ICCV 2023 | RGB | Swin-T | 77.6 | 70.3 | 10.8 | 48.7M | 25.6 |
| Method C | TGRS 2024 | Event | ConvNeXt | 78.4 | 71.5 | 9.7 | 52.1M | 28.3 |
| Method D | TIP 2024 | RGB + Event | Swin-T | 80.2 | 73.9 | 8.5 | 56.4M | 22.7 |
| **Ours** | **This Work** | **RGB + Event** | **Ours** | **84.7** | **78.5** | **5.9** | **39.8M** | **41.6** |

> **↑** means higher is better. **↓** means lower is better.  
> The best results are shown in **bold**.


## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourname/yourrepo.git
cd yourrepo
```

### 2. Create environment

```bash
conda create -n yourproject python=3.8 -y
conda activate yourproject
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Optional: install CUDA extensions

```bash
cd ops
python setup.py build develop
cd ..
```


## 🚀 Quick Start

### Inference on a single sample

```bash
python tools/infer.py \
    --config configs/ours.yaml \
    --checkpoint checkpoints/ours_best.pth \
    --input demo/sample
```

### Inference on a sequence

```bash
python tools/infer_sequence.py \
    --config configs/ours.yaml \
    --checkpoint checkpoints/ours_best.pth \
    --input demo/sequence_001 \
    --save-dir outputs/sequence_001
```

### Visualize results

```bash
python tools/visualize.py \
    --input outputs/sequence_001 \
    --save-video outputs/demo.mp4
```

---

## 🏋️ Training

### Train on a single GPU

```bash
python tools/train.py \
    --config configs/ours.yaml \
    --work-dir work_dirs/ours
```

### Train on multiple GPUs

```bash
bash scripts/dist_train.sh configs/ours.yaml 4
```

### Resume training

```bash
python tools/train.py \
    --config configs/ours.yaml \
    --work-dir work_dirs/ours \
    --resume checkpoints/latest.pth
```

---

## 📏 Evaluation

### Evaluate pretrained model

```bash
python tools/test.py \
    --config configs/ours.yaml \
    --checkpoint checkpoints/ours_best.pth
```

### Evaluate and save predictions

```bash
python tools/test.py \
    --config configs/ours.yaml \
    --checkpoint checkpoints/ours_best.pth \
    --save-predictions outputs/predictions
```

---

## 📦 Model Zoo

| Model | Dataset | Input Size | Metric-1 ↑ | Metric-2 ↑ | Metric-3 ↓ | Download |
|---|---|---:|---:|---:|---:|---|
| Ours-Tiny | Dataset-A | 256×256 | 80.1 | 73.4 | 8.2 | [Download](https://github.com/yourname/yourrepo/releases) |
| Ours-Base | Dataset-A | 512×512 | 84.7 | 78.5 | 5.9 | [Download](https://github.com/yourname/yourrepo/releases) |
| Ours-Large | Dataset-A + Dataset-B | 512×512 | 86.3 | 80.4 | 5.1 | [Download](https://github.com/yourname/yourrepo/releases) |

---


## 📮 Contact

For questions, discussions, or collaborations, please contact:

```text
24B921001@stu.hit.edu.cn
```

You may also open an issue in this repository.

---

<div align="center">

## Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/MYQHY">
        <img src="https://github.com/MYQHY.png" width="100px" alt="MYQHY"/>
        <br />
        <sub><b>MYQHY</b></sub>
      </a>
      <br />
      <sub>myqq038@gmail.com</sub>
    </td>
    <td align="center">
      <a href="https://github.com/stampliu">
        <img src="https://github.com/stampliu.png" width="100px" alt="stampliu"/>
        <br />
        <sub><b>stampliu</b></sub>
      </a>
      <br />
      <sub>liuyuxi@connect.hku.hk</sub>
    </td>
        <td align="center">
      <a href="https://github.com/violetmx">
        <img src="https://github.com/violetmx.png" width="100px" alt="MYQHY"/>
        <br />
        <sub><b>violetmx</b></sub>
      </a>
      <br />
      <sub>ll693@outlook.com</sub>
    </td>
  </tr>
</table>



### ⭐ Star this repository if you find it helpful!


</div>

