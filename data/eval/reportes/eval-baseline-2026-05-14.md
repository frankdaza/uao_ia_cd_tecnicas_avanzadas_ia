# Evaluacion RAG — baseline

- **Timestamp (UTC)**: 2026-05-14 21:54:25Z
- **Entradas golden**: 34

## Contexto de ejecucion (reproducibilidad)

- **Coleccion Qdrant**: `corpus_fvl_eval_hf_baseline`
- **Proveedor embeddings**: `huggingface` / modelo `sentence-transformers/all-MiniLM-L6-v2` / dims `384`
- **RAG_SCORE_MINIMO** (evaluacion): `0.0`
- **RAG_TOP_K** (constructor recuperador): `5`

> Re-ejecutar con los mismos valores de entorno y la misma ingesta en Qdrant para comparar deltas entre tareas (TASK-68 en adelante).

## Notas de configuracion

- (sin notas adicionales)

## Versiones (referencia)

```
llama-index-core                   0.14.21
llama-index-embeddings-huggingface 0.7.0
llama-index-embeddings-openai      0.6.0
llama-index-instrumentation        0.5.0
llama-index-vector-stores-qdrant   0.10.1
llama-index-workflows              2.20.0
qdrant-client                      1.18.0
sentence-transformers              5.4.1
```

## Tabla agregada (promedio, solo factual)

| metrica | valor |
| --- | --- |
| `hit@10` | 0.3333 |
| `hit@8` | 0.3846 |
| `mrr` | 0.1710 |
| `ndcg@10` | 0.1667 |
| `ndcg@8` | 0.2606 |
| `precision@10` | 0.0333 |
| `precision@8` | 0.0481 |
| `recall@10` | 0.3333 |
| `recall@8` | 0.3846 |

## Tabla por consulta

| qid | tipo | k | hit | precision | recall | mrr | ndcg | preview top archivos |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q001 | factual | 10 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/directorio-medico-carlos-alberto-cortes-barbosa.md, data/markdown/valledellili-org/dir...` |
| Q002 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/eventos-18o-edicion-referenciacion-institucional-acreditacion.md, data/markdown/valled...` |
| Q003 | factual | 10 | 1 | 0.1000 | 1.0000 | 0.3333 | 0.5000 | `data/markdown/valledellili-org/fvl-al-dia-cat-salud-publica-y-extension-social.md, data/markdown/valledellili-org/mis...` |
| Q004 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/mision-vision-valores-historia-2.md, data/markdown/valledellili-org/mision-vision-valo...` |
| Q005 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/gestion-de-calidad-en-la-fundacion-valle-del-lili.md, data/markdown/valledellili-org/e...` |
| Q006 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/asi-fue-nuestra-visita-como-hospital-padrino-a-la-poblacion-de-buga-en-el-valle-del-ca...` |
| Q007 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/impacto-social-semillero-de-nuevos-talentos-lilitalentos.md, data/markdown/valledellil...` |
| Q008 | factual | 8 | 1 | 0.1250 | 1.0000 | 0.1250 | 0.3155 | `data/markdown/valledellili-org/nuevo-transporte-para-usuarios-entre-sedes-principal-y-limonar.md, data/markdown/valle...` |
| Q009 | factual | 8 | 1 | 0.1250 | 1.0000 | 0.3333 | 0.5000 | `data/markdown/valledellili-org/sede-sede-principal.md, data/markdown/valledellili-org/sedes-sede-principal.md, data/m...` |
| Q010 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/fvl-al-dia-cat-enciclopedia-de-la-salud.md, data/markdown/valledellili-org/fvl-al-dia-...` |
| Q011 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/asi-fue-nuestra-visita-como-hospital-padrino-a-la-poblacion-de-buga-en-el-valle-del-ca...` |
| Q012 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/servicios-q-70cb01c7.md, data/markdown/valledellili-org/servicios-q-86f62be9.md, data/...` |
| Q013 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/servicios.md, data/markdown/valledellili-org/servicios-q-86f62be9.md, data/markdown/va...` |
| Q014 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/servicios-q-3ef665f6.md, data/markdown/valledellili-org/servicios.md, data/markdown/va...` |
| Q015 | factual | 8 | 1 | 0.1250 | 1.0000 | 1.0000 | 1.0000 | `data/markdown/valledellili-org/servicios-nefrologia-y-trasplante-renal.md, data/markdown/valledellili-org/servicios-n...` |
| Q016 | factual | 8 | 1 | 0.1250 | 1.0000 | 0.1667 | 0.3562 | `data/markdown/valledellili-org/programa-falla-cardiaca.md, data/markdown/valledellili-org/falla-cardiaca.md, data/mar...` |
| Q017 | factual | 8 | 1 | 0.1250 | 1.0000 | 0.5000 | 1.1309 | `data/markdown/valledellili-org/buscador-integral-q-ed4f9332.md, data/markdown/valledellili-org/servicios-hemato-oncol...` |
| Q018 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/politica-de-tratamiento-de-datos-personales.md, data/markdown/valledellili-org/impacto...` |
| Q019 | factual | 8 | 1 | 0.1250 | 1.0000 | 0.3333 | 0.8562 | `data/markdown/valledellili-org/servicios-anestesiologia-fundacion-valle-del-lili.md, data/markdown/valledellili-org/s...` |
| Q020 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/politica-de-tratamiento-de-datos-personales.md, data/markdown/valledellili-org/inaugur...` |
| Q021 | factual | 8 | 1 | 0.1250 | 1.0000 | 1.0000 | 1.0000 | `data/markdown/valledellili-org/liliconnect-nuevo-servicio-de-telemedicina.md, data/markdown/valledellili-org/servicio...` |
| Q022 | factual | 8 | 1 | 0.1250 | 1.0000 | 0.1667 | 0.3562 | `data/markdown/valledellili-org/acompanamiento-integral-en-nuestra-unidad-de-alta-complejidad-obstetrica-uaco.md, data...` |
| Q023 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/directorio-medico-alejandra-quintero-serrano.md, data/markdown/valledellili-org/servic...` |
| Q024 | factual | 8 | 1 | 0.1250 | 1.0000 | 0.5000 | 0.6309 | `data/markdown/valledellili-org/colico-del-lactante-2.md, data/markdown/valledellili-org/que-es-lactancia-materna.md, ...` |
| Q025 | factual | 8 | 1 | 0.1250 | 1.0000 | 0.5000 | 0.6309 | `data/markdown/valledellili-org/fvl-al-dia-cat-enciclopedia-de-la-salud.md, data/markdown/valledellili-org/hipertensio...` |
| Q026 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/servicios-medicina-familiar.md, data/markdown/valledellili-org/diabetes-pediatrica.md,...` |
| Q027 | factual | 10 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/servicios-clinica-de-anticoagulacion.md, data/markdown/valledellili-org/pacientes-inte...` |
| Q028 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/pacientes-internacionales-2.md, data/markdown/valledellili-org/pacientes-internacional...` |
| Q029 | factual | 8 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `data/markdown/valledellili-org/buscador-integral-q-6bab5b63.md, data/markdown/valledellili-org/programa-cuidados-pali...` |
| Q030 | conteo | 200 | N/A | N/A | N/A | N/A | N/A | — |
| Q031 | listado | 200 | N/A | N/A | N/A | N/A | N/A | — |
| Q032 | conteo | 200 | N/A | N/A | N/A | N/A | N/A | — |
| Q033 | listado | 20 | N/A | N/A | N/A | N/A | N/A | — |
| Q034 | conteo | 50 | N/A | N/A | N/A | N/A | N/A | — |

## Apendice: consultas factuales con hit@k = 0

- **Q001**: ¿Cuál es la misión y la visión de la Fundación Valle del Lili?
- **Q002**: ¿Qué valores corporativos menciona la fundación?
- **Q004**: ¿Qué dice el documento sobre gestión de calidad en la Fundación Valle del Lili?
- **Q005**: ¿Qué es la línea de transparencia y el sistema de gestión de riesgos?
- **Q006**: ¿Dónde queda la sede principal de la Fundación Valle del Lili?
- **Q007**: Información sobre la sede Alfaguara.
- **Q010**: ¿Qué se cuenta sobre la sede Av. Estación?
- **Q011**: ¿Qué es la UCIP en la Fundación Valle del Lili?
- **Q012**: ¿Qué cubre el servicio de gastroenterología pediátrica?
- **Q013**: ¿Qué ofrece oncología clínica?
- **Q014**: ¿Qué es la cardiología pediátrica en la fundación?
- **Q018**: ¿Qué es el programa de contacto canguro?
- **Q020**: ¿Qué es la unidad de trasplantes?
- **Q023**: ¿Qué es psiquiatría infantil y del adolescente?
- **Q026**: ¿Qué recomienda el documento sobre prevención y cuidados en diabetes?
- **Q027**: ¿Cómo solicito una cita médica?
- **Q028**: ¿Qué son las preadmisiones?
- **Q029**: ¿Qué debo saber sobre urgencias pediátricas?

## Apendice: consultas agregativas (no aplicables aun)

- **Q030** (conteo): pendiente TASK-70 / `listar_estructurado`.
- **Q031** (listado): pendiente TASK-70 / `listar_estructurado`.
- **Q032** (conteo): pendiente TASK-70 / `listar_estructurado`.
- **Q033** (listado): pendiente TASK-70 / `listar_estructurado`.
- **Q034** (conteo): pendiente TASK-70 / `listar_estructurado`.

