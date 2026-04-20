# 🔬 Automated Defect Detection — Industrial Quality Control POC

> **Équipe :** Mathis MARSAULT, Axel BONNEAU, Louis MAILLET  
> **École :** ESAIP — École Supérieure Angevine en Informatique et Productique  
> **Date :** Avril 2026

---

## 📋 Executive Summary

Dans un contexte industriel où la compétitivité repose sur la réduction des rebuts et la garantie d'une qualité irréprochable, l'inspection manuelle montre ses limites (fatigue, lenteur, subjectivité).

Ce projet présente un **Proof of Concept (POC)** visant à automatiser le contrôle qualité via des algorithmes de **Computer Vision State-of-the-Art**. L'architecture modulaire et non-supervisée apprend la *"perfection"* d'une pièce et identifie toute déviation mathématique.

**Résultats clés :** AUROC > 0.99 sur les surfaces complexes (Leather, Hazelnut, Bottle), avec des temps d'inférence < 50ms sur GPU.

---

## 🧠 Architecture Technique

### Paradigme : Apprentissage Non-Supervisé de la Normalité

En milieu industriel, les pièces défectueuses sont rares — entraîner un modèle de classification classique serait inefficace et biaisé. Notre approche :

1. **Memory Bank** — Extraction de l'empreinte mathématique des pièces **parfaites** uniquement (train set).
2. **Détection d'Anomalie** — Toute nouvelle pièce s'éloignant de cette norme est classée comme anomalie.

### Implémentation SOTA — PatchCore avec Wide-ResNet-50

| Composant | Détail |
|---|---|
| **Backbone** | Wide-ResNet-50 (pré-entraîné ImageNet) |
| **Extraction** | Layer 2 (micro-rayures, haute fréquence) + Layer 3 (défauts structurels) |
| **Analyse** | Découpage en micro-patches — si **une seule zone** est anormale, la pièce est rejetée |
| **Moteur KNN** | Remplacé par `torch.cdist` — calcul matriciel full-GPU |
| **Inférence** | **< 50ms** par pièce |

### Modularité — 15 Modèles Distincts

Un modèle (Memory Bank) par ligne de production, plutôt qu'un modèle unique, pour :

- **Scalabilité** — Nouvelle ligne = 100 pièces saines à scanner, sans ré-entraînement
- **Performance** — Pas de *"Catastrophic Forgetting"* entre cuir, câbles et composants électroniques
- **Edge Deployment** — Quelques Mo par modèle, chargement instantané sur la caméra de ligne

---

## 📊 Résultats — AUROC par Ligne de Production

| Ligne | Complexité | AUROC | Ligne | Complexité | AUROC |
|---|---|---|---|---|---|
| **Leather** | Texture organique | **0.9997** ✅ | Cable | Géométrie filaire | 0.9365 |
| **Hazelnut** | Organique 3D | **0.9986** ✅ | Tile | Motif régulier | 0.9242 |
| **Bottle** | Plastique/Reflets | **0.9968** ✅ | Zipper | Tissu & Métal | 0.9183 |
| **Carpet** | Texture tissée | **0.9920** ✅ | Capsule | Pièce asymétrique | 0.9178 |
| **Toothbrush** | Plastique moulé | **0.9917** ✅ | Screw | Métal usiné fin | 0.9129 |
| **Wood** | Texture organique | **0.9886** ✅ | Transistor | Électronique | 0.8888 |
| **MetalNut** | Pièce usinée | **0.9765** ✅ | Pill | Petite taille | 0.8704 |
| Grid | Structure répétitive | 0.7385 ⚠️ | | | |

> **Évaluation codée from-scratch** pour respecter l'intégrité du challenge (zéro code d'évaluation tiers).

### Analyse Critique des Contre-Performances

- **Grid (0.73)** — Downscaling à 224×224 : un défaut de 2mm devient sous-pixellique et disparaît.
- **Screw** — Le seuil dynamique (95ème percentile) laisse passer des micro-défauts fins.
- **Transistor / Pill** — Résolution spatiale insuffisante pour les détails électroniques/pharmacie.

---

## 🗂️ Structure du Projet

```
Automated_Defect_Detection/
├── Automated_defect.ipynb   # Notebook principal — entraînement & évaluation
├── memory_bank/             # Memory Banks entraînées (modèles .pt, non versionnés)
│   ├── bottle_model.pt
│   ├── cable_model.pt
│   └── ...                  # 15 modèles au total (MVTec AD)
└── README.md
```

> ⚠️ **Les fichiers `.pt` (> 250 Mo chacun) ne sont pas versionnés sur GitHub.** Voir la section [Reproduire les Modèles](#-reproduire-les-modèles) pour les générer.

---

## 🚀 Reproduire les Modèles

### Prérequis

- Python 3.9+
- PyTorch ≥ 2.0 (CUDA recommandé)
- Dataset MVTec AD (4.9 Go) — [Télécharger ici](https://www.mvtec.com/company/research/datasets/mvtec-ad)

### Installation

```bash
pip install torch torchvision tqdm scikit-learn matplotlib
```

### Entraînement

Ouvrir et exécuter le notebook `Automated_defect.ipynb` en suivant les cellules dans l'ordre :

1. **Cellules de configuration** — Définir les chemins vers le dataset MVTec AD
2. **Entraînement (Memory Bank)** — Extraction des features sur le train set (pièces saines uniquement)
3. **Évaluation AUROC** — Calcul des scores par catégorie sur le test set
4. **Visualisation** — Dashboard ROC Curves

---

## 🗺️ Roadmap d'Optimisation (V1.0 Production)

| Optimisation | Impact | Gain Estimé |
|---|---|---|
| **Sliding Window** | Scan en pleine résolution 4K (blocs 256×256) | Grid : 0.73 → **> 0.98** |
| **TensorRT** | Compilation C++ NVIDIA | Mémoire ÷4, inférence **< 10ms** |
| **Data Augmentation Latente** | Variations d'illumination synthétiques | Robustesse éclairage usine |

---

## 🏭 Intégration Industrielle & ROI

### Architecture Matérielle (Edge Computing — On-Premise)

| Composant | Matériel | Prix Estimatif (HT) |
|---|---|---|
| Vision | Caméra GigE 4K + Objectif + Éclairage LED Polarisant | ~1 200 € |
| Calcul | NVIDIA Jetson Orin NX (fanless, basse consommation) | ~1 200 € |
| Déploiement | Logiciel + Création Memory Bank (service) | ~2 500 € |
| **Total par ligne** | | **~4 900 €** |

### Retour sur Investissement

- Coût opérateur qualité 3×8 : **> 100 000 €/an**
- Coût d'un rappel de lot défectueux : **dizaines de milliers d'euros**
- **Amortissement estimé : < 2 mois** + traçabilité numérique horodatée

---

## 📄 Dataset

**MVTec AD** — [mvtec.com](https://www.mvtec.com/company/research/datasets/mvtec-ad)  
15 catégories d'objets et textures industrielles — 4.9 Go

```
@inproceedings{bergmann2019mvtec,
  title={MVTec AD -- A Comprehensive Real-World Dataset for Unsupervised Anomaly Detection},
  author={Bergmann, Paul and Fauser, Michael and Sattlegger, David and Steger, Carsten},
  booktitle={CVPR},
  year={2019}
}
```

---

## 👥 Auteurs

| Nom | École |
|---|---|
| Mathis MARSAULT | ESAIP |
| Axel BONNEAU | ESAIP |
| Louis MAILLET | ESAIP |

---

*Projet réalisé dans le cadre d'un POC industriel — ESAIP 2026*
