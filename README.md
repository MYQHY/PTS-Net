<div align="center">

<img src="assets/banner.png" width="100%">


<p align="center">
  <img src="fig/headline.png" alt="Exploration of the boundaries of detection capability for IRSTD">
</p>

</div>

## 🔗 Quick Jump
Try our:

🗂️[HIT-EWIRSTD](https://pan.baidu.com/s/19FWo0dn7FMTA0YJ7FJ3L0g?pwd=3q97)
Dataset
<p align="left">
  <img src="fig/dataset.png" alt="Dataset">
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

> This repository provides the official PyTorch implementation, pretrained models, evaluation scripts, visualization tools, and reproducible experimental protocols.

---

## 📢 News

- **2026-06-10**: 🚀 Project page is online.


---

## ✨ Highlights

<table>
<tr>
<td width="50%">
  

### 🌗 Innovative ideas inspired by event sensors

</td>
<td width="50%">

<img src="fig/abstract.png" width="100%">

</td>
</tr>

<tr>
<td width="50%">
  
### 🧠 Break through the existing upper limit of extremely weak target detection capability

</td>

<td width="50%">
<img src="assets/highlight_framework.png" width="100%">

</td>
</tr>

<tr>
<td width="50%">

### ⚡ Efficient and Reproducible

The complete pipeline supports training, evaluation, inference, visualization, and model deployment with clear configuration files.

</td>
<td width="50%">

<img src="assets/highlight_efficiency.png" width="100%">

</td>
</tr>
</table>

---

## 🧩 Method

<p align="center">
  <img src="assets/pipeline.png" width="95%">
</p>

The overall framework consists of three key components:

### 1. Feature Extraction Backbone

We adopt a strong multi-scale backbone to extract hierarchical visual representations from input data.

### 2. Task-Aware Feature Fusion

The proposed fusion module adaptively combines complementary information while suppressing noisy or unreliable features.

### 3. Prediction Head

The prediction head estimates the final task-specific output, such as object location, segmentation mask, keypoints, pose parameters, or classification scores.

---

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
      <b>NUDT-MIRSDT-HiNo</b>
    </td>
    <td align="center" width="33%">
      <img src="fig/HIT_EWIRSTD-Sequence55_mask_visualization.gif" width="100%">
      <br>
      <b>HIT_EWIRSTD</b>
    </td>
  </tr>
</table>

---

## 📊 Qualitative Results

<table>
<tr>
<td align="center"><b>Input</b></td>
<td align="center"><b>Baseline</b></td>
<td align="center"><b>Ours</b></td>
<td align="center"><b>Ground Truth</b></td>
</tr>

<tr>
<td><img src="assets/qualitative/input_1.png" width="100%"></td>
<td><img src="assets/qualitative/baseline_1.png" width="100%"></td>
<td><img src="assets/qualitative/ours_1.png" width="100%"></td>
<td><img src="assets/qualitative/gt_1.png" width="100%"></td>
</tr>

<tr>
<td><img src="assets/qualitative/input_2.png" width="100%"></td>
<td><img src="assets/qualitative/baseline_2.png" width="100%"></td>
<td><img src="assets/qualitative/ours_2.png" width="100%"></td>
<td><img src="assets/qualitative/gt_2.png" width="100%"></td>
</tr>
</table>

---

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

---

## 📈 Performance Visualization

<p align="center">
  <img src="assets/performance_bar.png" width="78%">
</p>

<p align="center">
  <b>Performance comparison with representative state-of-the-art methods.</b>
</p>

---

## 🔬 Ablation Study

| Variant | Module A | Module B | Module C | Metric-1 ↑ | Metric-2 ↑ | Metric-3 ↓ |
|---|:---:|:---:|:---:|---:|---:|---:|
| Baseline | ✗ | ✗ | ✗ | 76.2 | 69.4 | 11.8 |
| + Module A | ✓ | ✗ | ✗ | 79.1 | 72.3 | 9.6 |
| + Module A + B | ✓ | ✓ | ✗ | 81.5 | 75.1 | 7.4 |
| **Full Model** | ✓ | ✓ | ✓ | **84.7** | **78.5** | **5.9** |

<p align="center">
  <img src="assets/ablation.png" width="82%">
</p>

---

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

---

## 📁 Dataset Preparation

Please organize the dataset as follows:

```text
datasets/
├── DatasetName/
│   ├── train/
│   │   ├── images/
│   │   ├── events/
│   │   ├── labels/
│   │   └── annotations.json
│   ├── val/
│   │   ├── images/
│   │   ├── events/
│   │   ├── labels/
│   │   └── annotations.json
│   └── test/
│       ├── images/
│       ├── events/
│       ├── labels/
│       └── annotations.json
```

You can modify the dataset path in:

```bash
configs/dataset.yaml
```

---

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

## 🗂️ Repository Structure

```text
YourProjectName/
├── assets/                  # Figures, demos, and README images
├── configs/                 # Configuration files
├── datasets/                # Dataset preparation and dataloaders
├── models/                  # Model architectures
│   ├── backbones/
│   ├── necks/
│   ├── heads/
│   └── modules/
├── tools/                   # Training, testing, inference scripts
├── scripts/                 # Shell scripts
├── docs/                    # Detailed documentation
├── demo/                    # Demo samples
├── checkpoints/             # Pretrained models
├── outputs/                 # Visualization and prediction outputs
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🧪 Reproducibility Checklist

- [x] Training code
- [x] Evaluation code
- [x] Inference code
- [x] Visualization script
- [x] Configuration files
- [x] Pretrained models
- [x] Dataset preparation instructions
- [x] Random seed control
- [x] Main experimental logs
- [x] Ablation study settings

---

## 🛠️ Configuration

Most experimental settings can be modified in:

```bash
configs/ours.yaml
```

Example:

```yaml
model:
  name: YourProjectName
  backbone: resnet50
  input_modality: rgb_event
  num_classes: 1

dataset:
  name: DatasetName
  root: datasets/DatasetName
  input_size: [512, 512]

training:
  epochs: 100
  batch_size: 8
  optimizer: AdamW
  learning_rate: 0.0001
  weight_decay: 0.0005

evaluation:
  metrics:
    - metric_1
    - metric_2
    - metric_3
```

---

## 🌈 Visualization Tools

Generate qualitative comparison figures:

```bash
python tools/visualize_comparison.py \
    --config configs/ours.yaml \
    --checkpoint checkpoints/ours_best.pth \
    --input demo/sample \
    --save-dir outputs/visualization
```

Generate feature maps:

```bash
python tools/visualize_features.py \
    --config configs/ours.yaml \
    --checkpoint checkpoints/ours_best.pth \
    --input demo/sample \
    --layer model.backbone.stage3
```

Generate attention maps:

```bash
python tools/visualize_attention.py \
    --config configs/ours.yaml \
    --checkpoint checkpoints/ours_best.pth \
    --input demo/sample
```

---

## 📌 TODO

- [x] Release inference code
- [x] Release training code
- [x] Release pretrained models
- [x] Release visualization tools
- [ ] Release extended benchmark results
- [ ] Release deployment version
- [ ] Release TensorRT acceleration code

---

## ❓ FAQ

<details>
<summary><b>Q1: How can I reproduce the main results?</b></summary>

Please download the pretrained model from the Model Zoo and run:

```bash
python tools/test.py \
    --config configs/ours.yaml \
    --checkpoint checkpoints/ours_best.pth
```

</details>

<details>
<summary><b>Q2: How should I prepare my own dataset?</b></summary>

Please follow the dataset structure in the Dataset Preparation section. You may also implement a custom dataset class in:

```text
datasets/custom_dataset.py
```

</details>

<details>
<summary><b>Q3: Can this method be deployed on edge devices?</b></summary>

Yes. We provide a lightweight version and deployment scripts. Please refer to:

```text
docs/deployment.md
```

</details>

---

## 📚 Citation

If you find this project useful, please consider citing our paper:

```bibtex
@article{yourname2026yourproject,
  title={Your Paper Title},
  author={Author A and Author B and Author C and Author D},
  journal={IEEE Transactions on XXX},
  year={2026},
  volume={xx},
  number={xx},
  pages={xx--xx},
  doi={xx.xxxx/xxxxx}
}
```

For conference papers:

```bibtex
@inproceedings{yourname2026yourproject,
  title={Your Paper Title},
  author={Author A and Author B and Author C and Author D},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  year={2026},
  pages={xx--xx}
}
```

---

## 🙏 Acknowledgement

This repository is built upon several excellent open-source projects. We sincerely thank the authors for their valuable contributions.

- [PyTorch](https://pytorch.org/)
- [OpenMMLab](https://openmmlab.com/)
- [timm](https://github.com/huggingface/pytorch-image-models)
- [Papers with Code](https://paperswithcode.com/)

---

## 📮 Contact

For questions, discussions, or collaborations, please contact:

```text
Your Name
your_email@example.com
Your Institution
```

You may also open an issue in this repository.

---

<div align="center">

### ⭐ Star this repository if you find it helpful!

<img src="assets/footer.png" width="90%">

</div>
