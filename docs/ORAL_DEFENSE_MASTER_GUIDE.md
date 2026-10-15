# VisionGuard AI — Oral Defense Master Guide

> Internal preparation guide for **DES SOLUC INTELIGENTES [LAB 3]**  
> Team: **Mathis M. / Louis / Julien**

This guide is intentionally written in French for team preparation while keeping the exact English technical vocabulary used in the repository and interface.

---

## 1. Projet en une phrase

**VisionGuard AI est un prototype de contrôle qualité industriel assisté par IA qui apprend à quoi ressemble une pièce normale, détecte des déviations visuelles, les localise avec une heatmap, puis laisse la décision finale à un opérateur humain.**

La phrase anglaise la plus sûre à l'oral :

> “VisionGuard AI is a human-centered industrial anomaly-detection prototype. The model provides anomaly evidence, while the final quality decision remains under human responsibility.”

---

## 2. Problème traité

L'inspection visuelle industrielle peut être répétitive, coûteuse et difficile lorsque les défauts sont rares, subtils ou variables.

Le projet vise donc à assister un opérateur qualité dans une décision :

- pièce visuellement conforme ;
- anomalie potentielle ;
- besoin d'escalade ou d'une inspection humaine supplémentaire.

Le système ne prétend pas remplacer un contrôleur qualité.

---

## 3. Pourquoi anomaly detection plutôt qu'une classification classique

Une classification supervisée classique demanderait de nombreux exemples étiquetés pour chaque type de défaut.

Dans l'industrie :

- les pièces normales sont nombreuses ;
- certains défauts sont rares ;
- de nouveaux défauts peuvent apparaître ;
- il est difficile de constituer un jeu équilibré couvrant tous les cas.

Notre approche est donc **normal-only** : la memory bank est construite uniquement à partir des images `train/good`.

Formulation orale :

> “We selected anomaly detection because normal production data is much easier to collect than exhaustive labeled examples of every possible defect.”

---

## 4. Dataset

Nous utilisons trois catégories sélectionnées du benchmark **MVTec AD** :

- Bottle ;
- Metal Nut ;
- Screw.

Les images originales ne sont pas stockées dans Git.

Pour chaque catégorie :

```text
category/
├── train/
│   └── good/
└── test/
    ├── good/
    └── defect_type_1/
       defect_type_2/
       ...
```

Le dossier `train/good` sert à construire la référence normale.

---

## 5. Pipeline du modèle déployé

Le modèle vérifié est **Patch-HOG kNN**.

Pipeline :

```text
RGB image
   ↓
grayscale
   ↓
resize 256 × 256
   ↓
8 × 8 grid = 64 local patches
   ↓
HOG + local texture statistics
   ↓
comparison with normal memory bank
   ↓
64 local nearest-neighbour distances
   ↓
mean of the 3 highest local anomaly scores
   ↓
global anomaly score
   ↓
category-specific threshold
   ↓
NORMAL / ANOMALY
```

---

## 6. HOG expliqué simplement

HOG signifie **Histogram of Oriented Gradients**.

L'idée n'est pas de mémoriser les pixels exactement. HOG décrit surtout les structures locales :

- contours ;
- directions des gradients ;
- formes ;
- texture locale.

Dans chaque patch, notre code calcule le descripteur HOG avec :

- 9 orientations ;
- cellules 8 × 8 ;
- blocs 2 × 2 ;
- normalisation L2-Hys.

Nous ajoutons aussi quatre statistiques :

- intensité moyenne ;
- écart-type ;
- gradient absolu moyen en X ;
- gradient absolu moyen en Y.

Cela produit une représentation locale plus informative qu'un simple histogramme global.

---

## 7. Memory bank

La memory bank contient les grilles de features calculées sur les images normales.

Pour une nouvelle image, chaque patch est comparé aux patches normaux de la même position dans toutes les images de référence.

La distance minimale est conservée :

> plus le patch ressemble à au moins une configuration normale connue, plus son score est faible.

Une distance élevée indique une région inhabituelle.

---

## 8. Pourquoi kNN / nearest neighbour

Il n'y a pas de réseau à entraîner dans le modèle déployé.

Le détecteur fait essentiellement :

```text
new patch
   ↓
distance to normal references
   ↓
nearest normal example
   ↓
minimum distance
```

C'est transparent, reproductible et adapté à un prototype CPU/local.

---

## 9. Pourquoi le score global utilise les 3 patches les plus anormaux

Un défaut peut être très local.

Si nous faisions la moyenne des 64 patches, une petite anomalie pourrait être diluée par de nombreuses zones normales.

Nous trions donc les scores locaux et calculons la moyenne des trois plus élevés.

Avantage :

- sensibilité à une anomalie localisée ;
- plus stable qu'un simple maximum unique, qui pourrait être trop sensible au bruit.

---

## 10. Heatmap

Les 64 scores locaux sont normalisés puis redimensionnés à la taille de l'image.

Une colormap est appliquée et mélangée à l'image originale.

Important :

> la heatmap est une visualisation du score local du modèle, pas une segmentation ground-truth du défaut.

---

## 11. Threshold

Le score d'anomalie n'est pas une probabilité.

Exemple :

`score = 1.8` ne signifie pas “80 % de chance que la pièce soit défectueuse”.

Il s'agit d'une distance/anomaly score.

Chaque catégorie possède son seuil :

| Category | Threshold |
|---|---:|
| Bottle | 1.452671 |
| Metal Nut | 1.572177 |
| Screw | 1.526895 |

Règle :

- score <= threshold → NORMAL ;
- score > threshold → ANOMALY.

---

## 12. Comment les thresholds ont été sélectionnés

Nous ne sélectionnons jamais un seuil sur le final test.

Pour chaque type de défaut du test original :

- 40 % des images → validation ;
- 60 % → final test ;
- seed = 42.

Le seuil est sélectionné sur validation avec le **Youden J statistic** :

```text
J = TPR - FPR
```

On choisit le seuil de la ROC curve qui maximise ce compromis.

Puis le seuil est gelé avant le final test.

C'est ce qui évite de régler le système directement sur les résultats finaux.

---

## 13. Pourquoi le protocole est appelé “project-specific”

MVTec AD ne fournit pas dans notre utilisation une validation séparée prête à l'emploi pour calibrer le threshold.

Nous avons donc créé notre propre holdout validation/final-test.

Il faut être totalement transparent :

> “This is a project-specific holdout protocol. We do not claim that these numbers correspond to the untouched official MVTec benchmark protocol.”

---

## 14. Baseline

La baseline est un **RGB histogram nearest-centroid**.

Étapes :

1. histogramme de 16 bins pour R, G, B ;
2. concaténation ;
3. normalisation ;
4. calcul du centroïde moyen des images normales ;
5. distance de la nouvelle image au centroïde.

Cette baseline est volontairement simple.

Elle sert à prouver que notre modèle sélectionné est meilleur qu'une solution naïve.

---

## 15. Résultats finaux

| Category | Model | AUROC | AP | Accuracy | F1 |
|---|---|---:|---:|---:|---:|
| Bottle | RGB baseline | 0.6535 | 0.8876 | 0.6600 | 0.7848 |
| Bottle | Patch-HOG | 1.0000 | 1.0000 | 0.9200 | 0.9444 |
| Metal Nut | RGB baseline | 0.4341 | 0.7947 | 0.5217 | 0.6292 |
| Metal Nut | Patch-HOG | 0.9135 | 0.9798 | 0.8116 | 0.8762 |
| Screw | RGB baseline | 0.0028 | 0.5315 | 0.2604 | 0.0000 |
| Screw | Patch-HOG | 0.6406 | 0.8061 | 0.6042 | 0.6935 |

Conclusion :

- Bottle : très fort ;
- Metal Nut : bon mais imparfait ;
- Screw : cas difficile / stress test.

---

## 16. Métriques à connaître

### Confusion matrix

- TP : anomalie réellement présente et détectée ;
- TN : pièce normale correctement classée ;
- FP : pièce normale signalée comme anomalie ;
- FN : anomalie non détectée.

Dans un contexte industriel, les FN peuvent être particulièrement critiques car une pièce défectueuse peut passer.

### Accuracy

Part des prédictions correctes.

Limite : peut être trompeuse si les classes sont déséquilibrées.

### Precision

Parmi les pièces signalées anomalous, combien sont réellement anormales.

### Recall / TPR

Parmi les anomalies réelles, combien sont détectées.

### F1

Moyenne harmonique Precision / Recall.

### AUROC

Mesure la capacité du score à classer les anomalies au-dessus des normales pour tous les seuils.

### Average Precision

Résume la courbe Precision-Recall et est utile lorsque les classes sont déséquilibrées.

---

## 17. Analyse d'erreurs

### Bottle

Final test :

- TP 34
- TN 12
- FP 0
- FN 4

Les erreurs restantes sont surtout des contaminations subtiles sous le threshold.

### Metal Nut

- TP 46
- TN 10
- FP 3
- FN 10

Les défauts principalement chromatiques sont plus difficiles car le modèle déployé passe en grayscale.

### Screw

- TP 43
- TN 15
- FP 10
- FN 28

Screw est difficile à cause de :

- orientation ;
- pose ;
- géométrie étroite ;
- petites rayures ;
- défauts localisés de thread/head.

---

## 18. Expérience d'alignement Screw

Nous avons testé :

1. Otsu segmentation ;
2. détection du contour principal ;
3. PCA sur le contour ;
4. estimation de l'axe principal ;
5. rotation ;
6. crop ;
7. flip pour mettre la tête du même côté ;
8. grille Patch-HOG alignée.

Résultat :

- AUROC 0.6406 → 0.6670 ;
- AP 0.8061 → 0.8567.

Mais :

- FN augmente à 36 ;
- F1 tombe à 0.625.

Nous avons donc refusé de promouvoir ce modèle.

Réponse orale importante :

> “We did not select a model only because AUROC increased. At the selected operating point, false negatives became worse, so the current deployment model remained preferable for our decision objective.”

---

## 19. Backend FastAPI

`webapp.py` est le point central du backend.

Endpoints importants :

- `GET /` — frontend ;
- `GET /api/health` — processus actif ;
- `GET /api/readiness` — modèles réellement prêts ;
- `GET /api/categories` — catégories/configuration ;
- `GET /api/model-info/{category}` — métadonnées modèle ;
- `POST /api/inspect` — inference ;
- `GET /api/inspections` — historique ;
- `GET /api/stats` — statistiques ;
- `GET /api/benchmarks` — résultats expérimentaux ;
- `POST /api/inspections/{id}/review` — décision humaine.

---

## 20. Liveness vs readiness

**Liveness** demande :

> est-ce que l'application fonctionne ?

**Readiness** demande :

> peut-elle réellement effectuer une inspection ?

Une API peut être alive alors qu'un fichier model est absent.

C'est pourquoi les deux sont séparés.

---

## 21. ModelRegistry

`src/model_registry.py` :

- lit `model_config.json` ;
- trouve le bon artefact par catégorie ;
- vérifie le threshold ;
- vérifie que le fichier existe ;
- calcule le SHA-256 ;
- charge le bon engine ;
- garde le detector en cache.

Le cache évite de recharger le modèle à chaque requête.

---

## 22. SHA-256 et versioning

Chaque artefact modèle possède un hash SHA-256.

Lors d'une inspection, ce hash est stocké dans SQLite.

Ainsi, si le modèle change plus tard, on peut toujours retrouver quel artefact exact a produit une ancienne décision.

C'est une forme simple de **model traceability**.

---

## 23. Traceabilité SQLite

La table `inspections` enregistre :

- UUID ;
- timestamp UTC ;
- catégorie ;
- engine ;
- hash modèle ;
- filename ;
- hash de l'image uploadée ;
- décision modèle ;
- score ;
- threshold ;
- latency ;
- décision opérateur ;
- date de review.

Les images brutes ne sont pas sauvegardées par défaut.

---

## 24. Pourquoi stocker le hash de l'image mais pas l'image

Objectifs :

- limiter la rétention de données ;
- éviter de stocker inutilement des images potentiellement sensibles ;
- conserver un identifiant cryptographique de l'entrée.

Le hash ne permet pas de reconstruire l'image.

---

## 25. Frontend

Le frontend est volontairement custom HTML/CSS/JavaScript.

Pages :

### Inspection
workflow opérateur.

### Performance
résultats réels depuis les JSON dans `artifacts/`.

### System
état du backend et des modèles.

Le frontend ne recalcule pas les métriques : `BenchmarkService` les lit depuis les artifacts.

---

## 26. Séparation Model Decision / Human Decision

C'est l'un des points les plus importants.

Exemple possible :

```text
model_decision = ANOMALY
operator_decision = ACCEPT
```

Le système permet cette divergence.

Pourquoi ?

Parce que l'IA est un système d'aide à la décision et non une autorité finale.

---

## 27. Contrôles de sécurité applicatifs

Le prototype inclut :

- content-type allowlist PNG/JPEG/WEBP ;
- limite d'upload 12 MB ;
- gestion des images invalides ;
- aucun secret dans Git ;
- `.env` ignoré ;
- pas de stockage raw-image par défaut ;
- modèle obligatoire + threshold obligatoire avant inference.

Ce n'est pas suffisant pour une vraie usine mais c'est cohérent avec un prototype.

---

## 28. Docker / deployment

Le projet possède :

- Dockerfile ;
- docker-compose.yml ;
- healthcheck ;
- volume read-only pour les models ;
- volume persistant pour runtime.

Cela démontre une voie de déploiement reproductible/local.

Pour la soutenance, lancer directement avec Uvicorn est plus simple.

---

## 29. Tests et CI

GitHub Actions utilise Python 3.11 et exécute :

1. installation des requirements ;
2. `python -m compileall` ;
3. `pytest`.

Cela détecte les régressions élémentaires avant présentation.

---

## 30. Reproductibilité expérimentale

`scripts/bootstrap_demo.py` peut reconstruire :

- split ;
- memory bank ;
- calibration ;
- final evaluation ;
- `model_config.json`.

Cela permet à une personne techniquement compétente de refaire le pipeline à partir des trois catégories source.

---

## 31. Comment lancer l'outil le jour de l'oral

Ne réinstallez rien le jour même.

Avant le cours :

1. ordinateur chargé ;
2. repo déjà présent ;
3. `.venv` déjà créé ;
4. dependencies déjà installées ;
5. `model_config.json` à la racine ;
6. trois `.npz` dans `memory_bank/` ;
7. demo examples accessibles localement ;
8. navigateur déjà disponible hors ligne.

Dans VS Code PowerShell :

```powershell
cd "C:\DES SOLUC INT\Automated-Defect-Detection"
.\.venv\Scripts\Activate.ps1
python -m pytest -q
python app.py
```

Puis :

```text
http://127.0.0.1:8000
```

Vérifier l'onglet **System** :

```text
Healthy
3/3 ready
Local
Disabled image retention
```

---

## 32. Démo recommandée

1. ouvrir System quelques secondes pour montrer **3/3 ready** ;
2. Inspection → Bottle normal → NORMAL → ACCEPT ;
3. Bottle anomaly → ANOMALY → REJECT ;
4. montrer traceability/history ;
5. Performance → résultats Bottle/Metal Nut/Screw ;
6. expliquer Screw comme stress test ;
7. rappeler que le model output n'est pas une décision industrielle autonome.

---

## 33. Ce qu'il ne faut surtout pas dire

Ne pas dire :

- “The system is production-ready.”
- “The heatmap precisely segments the defect.”
- “The score is a probability.”
- “We trained on all defects.”
- “These are the official untouched MVTec benchmark scores.”
- “The model replaces the quality operator.”
- “Screw works very well.”

Dire plutôt :

- “industrialized academic prototype” ;
- “localized anomaly evidence” ;
- “anomaly distance score” ;
- “normal-only reference bank” ;
- “project-specific holdout protocol” ;
- “human decision support” ;
- “Screw is a deliberate stress-test category.”

---

# Questions probables et réponses

## Why did you choose anomaly detection?

Because normal production examples are easier to collect than exhaustive labeled examples of every possible defect. A normal-only detector can also flag visual deviations that do not belong to a predefined defect class.

## Why HOG?

HOG is lightweight, interpretable, CPU-friendly, and captures local edge/shape information. In our experiments it clearly outperformed a simple global RGB-histogram baseline while remaining easy to reproduce.

## Why not a CNN?

We implemented a deep-patch candidate, but we only report results that we actually executed and verified. The current verified deployable model is Patch-HOG kNN. A deeper representation remains future work.

## Is HOG really AI?

It is an intelligent anomaly-detection pipeline using feature extraction, reference learning from normal data, nearest-neighbour inference, calibrated decision thresholds, and an integrated decision-support system. It is not a neural network, but intelligent solutions are not limited to deep learning.

## What exactly is learned?

The system builds a normal reference memory bank from the local visual features of defect-free training images. There is no gradient-based training in the deployed Patch-HOG model.

## What is kNN here?

For every local feature in a new image, we search for the closest normal reference feature and use that nearest-neighbour distance as the local anomaly score.

## Why compare corresponding positions?

The objects are largely acquired under controlled conditions, so spatial position contains useful information. The limitation is that this increases pose sensitivity, especially for Screw.

## Why top 3 patches?

A global average would dilute small defects. A single maximum is noisy. Averaging the three most anomalous local regions is a compromise between localization sensitivity and robustness.

## Is the heatmap a segmentation?

No. It is an interpolated visualization of patch anomaly scores. It helps the operator understand where the model sees deviation but it is not pixel-accurate defect segmentation.

## Why different thresholds?

The score distributions differ by object category, so one global threshold would be poorly calibrated.

## How was the threshold selected?

From the validation holdout using the Youden J statistic on the ROC curve, then frozen before final-test evaluation.

## Why 40/60?

We needed enough labeled examples for threshold calibration while preserving a larger independent final-test set. It is a project-specific design choice, not an official MVTec protocol.

## What is data leakage?

Using information from final-test data to tune preprocessing, threshold, model parameters, or selection. We separate validation from final test to reduce this risk.

## Why is Screw weak?

Pose/orientation variability can create large fixed-grid feature distances, while some thread/head defects remain very localized and subtle.

## Why keep a weak category?

Because it exposes real limitations and demonstrates critical analysis. Removing it would make the evaluation less informative.

## What did the alignment experiment teach you?

Ranking metrics improved, but the operating point produced more false negatives and lower F1. This showed that model selection must consider operational errors, not only AUROC.

## What matters more: FP or FN?

It depends on industrial cost. Often FN is more dangerous because a defective part may pass. In a real deployment, the threshold objective must be chosen with quality engineers based on cost/risk.

## What is AUROC?

The probability-oriented ranking measure that evaluates how well anomaly scores separate positive and negative examples over all thresholds.

## Why can AUROC be high but F1 lower?

AUROC evaluates ranking across thresholds. F1 evaluates one specific operating threshold. Good ranking does not guarantee the selected threshold has the best practical trade-off.

## Why use Average Precision?

It summarizes precision-recall behavior and is particularly informative when positive/negative classes are imbalanced.

## Why SQLite?

It is simple, local, serverless, reproducible, and sufficient for prototype traceability. A production system might use PostgreSQL or a MES/database service.

## Why FastAPI?

It provides a clean typed Python API, easy integration with the ML code, automatic error handling, and a clear separation between UI and inference logic.

## Why no raw image storage?

Data minimization. The system demonstrates traceability while avoiding unnecessary retention of potentially sensitive industrial imagery.

## What is the image SHA-256 used for?

It provides a stable fingerprint of the exact uploaded bytes without storing the image itself.

## What is the model SHA-256 used for?

It identifies the exact model artifact that produced an inspection result.

## What happens if a model file is missing?

The readiness state reflects that the category is not ready and inference returns a configuration error instead of silently running with an invalid setup.

## Liveness vs readiness?

Liveness = application process is alive. Readiness = application has the required model artifacts and thresholds to perform useful work.

## Is it production-ready?

No. It is an industrialized academic prototype. Real deployment needs authentication, TLS, industrial camera integration, PLC/MES integration, centralized monitoring, cybersecurity hardening, backup, drift monitoring, change control, and validation on real line data.

## How would you improve Metal Nut?

Use color-aware local features or a deep visual representation because grayscale HOG loses chromatic information.

## How would you improve Screw?

Canonical alignment, object segmentation, rotation-aware features, higher-resolution local processing, or deep pretrained representations.

## What would drift mean here?

A change in camera, lighting, product version, pose distribution, or manufacturing process that changes the input distribution and can reduce detector performance.

## How would you monitor drift?

Track score distributions, FP/FN rates from operator review, camera metadata, and periodic labeled quality checks; trigger re-validation when distributions move.

## How was generative AI used?

For architecture planning, code generation/refactoring, tests, documentation, risk analysis, and presentation preparation. The team remains responsible for execution, verification, understanding, and all reported experimental evidence.

---

# Final 30-second summary

> “VisionGuard AI is a local industrial anomaly-detection prototype based on a normal-only Patch-HOG memory bank. We compared it against a simple RGB histogram baseline, calibrated independent thresholds on a validation holdout, and evaluated the frozen configuration on a separate final-test holdout. The system integrates FastAPI, a custom operator interface, SQLite traceability, model artifact fingerprinting, human ACCEPT/REJECT/ESCALATE decisions, health/readiness checks, tests, CI and Docker. Bottle is our strongest category, Metal Nut is a realistic imperfect case, and Screw is deliberately retained as a stress test to expose limitations. The model supports the quality operator; it does not replace the human decision.”
