---
id: TASK-130
title: t-SNE notebook analisis clusters plotly y interpretacion bonus
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-24 16:47'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - t-sne
milestone: m-1
dependencies:
  - TASK-129
references:
  - proyecto-3/analisis_tsne/notebooks/analisis_tsne.ipynb
  - proyecto-3/analisis_tsne/README.md
  - proyecto-3/src/openfang/reduccion_tsne.py
modified_files:
  - proyecto-3/analisis_tsne/notebooks/analisis_tsne.ipynb
  - proyecto-3/src/openfang/reduccion_tsne.py
  - proyecto-3/tests/analisis_tsne/test_reduccion_tsne.py
  - proyecto-3/tests/fixtures/tsne_vectores_demo.npy
  - proyecto-3/tests/fixtures/tsne_metadatos_demo.parquet
  - proyecto-3/analisis_tsne/README.md
  - proyecto-3/pyproject.toml
  - proyecto-3/analisis_tsne/output/tsne_2d.png
  - proyecto-3/analisis_tsne/output/tsne_3d.html
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**Bonus M3:** notebook con t-SNE (y opcional UMAP), clustering KMeans, visualización Plotly 2D/3D e interpretación escrita de ≥3 clusters temáticos (medicación, alarma, agradecimientos).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Notebook ejecuta de extremo a extremo tras tasks 128-129 (con datos reales o fixture demo)
- [x] #2 Exporta `tsne_2d.png` y `tsne_3d.html` en `output/`
- [x] #3 Perplejidad adaptativa objetivo [5, 30]; si sklearn exige `perplexity < n`, usar `min(30, max(5, n-1), n-1)` (con n=3 → 2)
- [x] #4 **Negativo:** &lt;3 **sesiones únicas** (`session_id` en metadatos) → advierte y omite t-SNE sobre datos reales (no falla opaco)
- [x] #5 Sección markdown interpreta ≥3 clusters con ejemplos de frases (sin PHI)
- [x] #6 Lógica en `src/openfang/reduccion_tsne.py`; tests sin red en `tests/analisis_tsne/test_reduccion_tsne.py`
- [x] #7 Si datos reales insuficientes, notebook puede cargar `tests/fixtures/tsne_*_demo` para gráficos de sustentación
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Módulo `reduccion_tsne.py`: perplejidad, KMeans k=3..5 (silhouette), t-SNE 2D/3D, export Plotly (`kaleido`).
2. Notebook: carga artefactos, guard sesiones, fallback demo, interpretación markdown.
3. Fixtures demo sin PHI; tests pytest.
4. README sección Notebook.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
```python
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
import plotly.express as px

perplexity = min(30, max(5, len(X) - 1))
coords = TSNE(n_components=2, perplexity=perplexity, random_state=42).fit_transform(X)
etiquetas = KMeans(n_clusters=3, random_state=42).fit_predict(X)
fig = px.scatter(x=coords[:, 0], y=coords[:, 1], color=etiquetas.astype(str))
fig.write_html("analisis_tsne/output/tsne_3d.html")  # o 2d segun celda
```
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementado bonus t-SNE: modulo reduccion_tsne.py, notebook analisis_tsne.ipynb, fixtures demo, 36 tests analisis_tsne verdes, kaleido en pyproject, README actualizado. Sin archivar.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Outputs generados o documentado cómo regenerarlos
- [x] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
