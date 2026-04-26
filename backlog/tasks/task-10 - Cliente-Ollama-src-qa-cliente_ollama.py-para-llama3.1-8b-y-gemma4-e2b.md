---
id: TASK-10
title: 'Cliente Ollama src/qa/cliente_ollama.py para llama3.1:8b y gemma4:e2b'
status: In Progress
assignee: []
created_date: '2026-04-26 20:15'
updated_date: '2026-04-26 21:38'
labels:
  - llm
dependencies:
  - TASK-2
references:
  - .cursor/skills/llm-backend/SKILL.md
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La inferencia se hace localmente con Ollama. La interfaz le ofrece al usuario elegir entre **`llama3.1:8b`** y **`gemma4:e2b`** (tags literales). Necesitamos un cliente HTTP minimalista que envíe el prompt y devuelva la respuesta del modelo, manejando errores comunes con mensajes claros.

## Objetivo

Implementar `src/qa/cliente_ollama.py` con una clase `ClienteOllama` desacoplada del pipeline (task-12) y de la UI (task-13).

## Diseño propuesto

```python
@dataclass
class ConfiguracionLlm:
    base_url: str = "http://localhost:11434"
    modelo: str = "llama3.1:8b"
    temperatura: float = 0.2
    num_ctx: int = 8192
    timeout_segundos: int = 180

class ModeloNoDisponibleError(RuntimeError): ...
class OllamaNoAccesibleError(RuntimeError): ...

class ClienteOllama:
    def __init__(self, configuracion: ConfiguracionLlm) -> None: ...

    def chat(self, mensajes: list[dict[str, str]]) -> str:
        '''Envia [{"role":"system",...},{"role":"user",...}] y devuelve la respuesta'''
        ...

    def listar_modelos_locales(self) -> list[str]: ...
```

## Detalles técnicos

### Endpoint principal

- `POST {base_url}/api/chat` con body:

  ```json
  {
    "model": "llama3.1:8b",
    "messages": [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."}
    ],
    "stream": false,
    "options": {
      "temperature": 0.2,
      "num_ctx": 8192
    }
  }
  ```

- Respuesta: `data["message"]["content"]`.

### Listado de modelos locales

- `GET {base_url}/api/tags` devuelve los modelos disponibles. Útil para que la UI valide antes de invocar.

### Manejo de errores

- **Conexión rechazada / timeout en /api/tags**: lanzar `OllamaNoAccesibleError` con mensaje:
  > "No se puede conectar a Ollama en `{base_url}`. Verifica que `ollama serve` esté corriendo."
- **Modelo no disponible** (status 404 con mensaje "model 'X' not found"): lanzar `ModeloNoDisponibleError` con mensaje:
  > "El modelo `{modelo}` no está instalado en Ollama. Ejecuta: `ollama pull {modelo}`"
- **Errores 5xx**: 1 reintento con backoff de 2s, luego propagar.

### Configuración

- Lectura de `OLLAMA_BASE_URL` y `MODELO_LLM_DEFECTO` desde `.env` (con `python-dotenv` o `os.environ`).
- `num_ctx=8192` permite inyectar archivos `.md` largos. Documentar como límite del MVP: si una página supera 8K tokens, podría truncarse del lado del modelo.

### Modelos soportados explícitamente

- **`llama3.1:8b`**: instalado por defecto en muchas guías de Ollama.
- **`gemma4:e2b`**: tag literal solicitado por el cliente. Si no existe en el registro de Ollama, el error será claro y la UI lo mostrará.

## Identificadores ASCII

- `ClienteOllama`, `ConfiguracionLlm`, `ModeloNoDisponibleError`, `OllamaNoAccesibleError`, `chat`, `listar_modelos_locales`.

## Dependencias a agregar

```bash
uv add requests python-dotenv
```

(o `httpx` si el equipo lo prefiere; `requests` ya viene de task-4).

## Tests

- Unit tests con `responses` o `requests-mock` para simular: respuesta válida, modelo no disponible, conexión rechazada.
- Test de integración (skippeable con marker `@pytest.mark.integration_ollama`) que llama un modelo real (default `llama3.1:8b`) si Ollama está accesible.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ClienteOllama.chat(mensajes) devuelve la respuesta de texto del modelo cuando Ollama está accesible
- [ ] #2 Si Ollama no responde en base_url, se lanza OllamaNoAccesibleError con mensaje en español indicando 'ollama serve'
- [ ] #3 Si el modelo no existe, se lanza ModeloNoDisponibleError con mensaje en español indicando 'ollama pull <modelo>'
- [ ] #4 listar_modelos_locales() devuelve una lista de strings con los tags instalados
- [ ] #5 Configuración lee OLLAMA_BASE_URL y MODELO_LLM_DEFECTO de variables de entorno con defaults sensatos
- [ ] #6 Tests unitarios con mocks pasan (sin requerir Ollama corriendo)
- [ ] #7 Test de integración existe y se skippea limpiamente cuando Ollama no está accesible
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Confirmar/agregar deps: uv add python-dotenv
2) Crear src/qa/cliente_ollama.py con dataclass ConfiguracionLlm y excepciones
3) Implementar chat() llamando POST /api/chat
4) Implementar listar_modelos_locales() llamando GET /api/tags
5) Mapear errores HTTP a excepciones específicas con mensajes en español
6) Tests unitarios con responses/requests-mock
7) Test de integración skippeable con pytest marker
8) Smoke test manual con llama3.1:8b si está instalado
<!-- SECTION:PLAN:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 uv add requests python-dotenv ejecutado (si no estaban)
- [ ] #2 El cliente NO menciona temperaturas, system prompts o pipelines de RAG: solo es un transport HTTP
- [ ] #3 Errores documentados con docstring que muestra el mensaje exacto
<!-- DOD:END -->
