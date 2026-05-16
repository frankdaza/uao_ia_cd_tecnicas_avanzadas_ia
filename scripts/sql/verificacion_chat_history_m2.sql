-- Verificación manual M2: memoria conversacional LangChain en PostgreSQL.
-- El historial del chat NO se lee desde Qdrant; Qdrant solo alimenta RAG en tiempo de inferencia.
--
-- session_id en chat_history es el UUID canónico (texto/UUID), alineado con
-- sesion_id_memoria_langchain(usuario.id) tras normalizar_session_id (ver src/agentes/reglas.py).
-- En localStorage suele guardarse "user:<uuid>"; en SQL use solo el UUID.
--
-- Sustituya <UUID_USUARIO> por el valor de usuario_id (tabla usuarios) de la sesión actual.

-- Resumen por sesión (últimas con más actividad)
SELECT session_id::text, COUNT(*) AS filas
FROM chat_history
GROUP BY session_id
ORDER BY filas DESC
LIMIT 25;

-- Mensajes de una sesión concreta (orden cronológico como el backend)
-- SELECT id, session_id::text, created_at, message
-- FROM chat_history
-- WHERE session_id = '<UUID_USUARIO>'::uuid
-- ORDER BY id;
