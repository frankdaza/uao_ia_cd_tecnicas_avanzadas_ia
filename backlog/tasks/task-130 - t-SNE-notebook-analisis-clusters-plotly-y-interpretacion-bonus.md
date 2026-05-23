---
id: TASK-130
title: 't-SNE notebook analisis clusters plotly y interpretacion bonus'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
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
modified_files:
  - proyecto-3/analisis_tsne/notebooks/analisis_tsne.ipynb
  - proyecto-3/analisis_tsne/output/tsne_2d.png
  - proyecto-3/analisis_tsne/output/tsne_3d.html
priority: medium
ordinal: 1300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**Bonus M3:** notebook con t-SNE (y opcional UMAP), clustering KMeans, visualización Plotly 2D/3D e interpretación escrita de ≥3 clusters temáticos (medicación, alarma, agradecimientos).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Notebook ejecuta de extremo a extremo tras tasks 128-129 (con datos de demo)
- [ ] #2 Exporta `tsne_2d.png` y `tsne_3d.html` en `output/`
- [ ] #3 Perplexity adaptativa entre 5 y 30 según tamaño de muestra
- [ ] #4 **Negativo:** &lt;3 sesiones → notebook advierte y omite t-SNE (no falla opaco)
- [ ] #5 Sección markdown interpreta ≥3 clusters con ejemplos de frases (sin PHI)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Crear notebook: carga vectores, TSNE, KMeans k=3..5 (silhouette opcional).
2. Plotly interactivo + export estático.
3. Redactar interpretación en celdas markdown.
4. Validar con datos sintéticos si falta tráfico real.
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

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Outputs generados o documentado cómo regenerarlos
- [ ] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
