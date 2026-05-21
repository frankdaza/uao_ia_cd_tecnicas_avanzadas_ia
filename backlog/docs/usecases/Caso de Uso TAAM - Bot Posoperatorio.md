# **Bot de la FVL para el seguimiento postoperatorio**

# **Actores**

1. Pacientes.  
2. Cirujanos.  
3. Asistentes.  
4. Administrador del sistema.  
5. Bot Lili.

# **Casos de uso**

| Actor | Caso de Uso  | Descripción |
| ----- | ----- | ----- |
| Administrador del Sistema | Registrar procedimiento | Registrar nuevo procedimiento con su respectivo documento (PDF) de recomendaciones generales. |
|  | Gestionar usuarios | Gestión administrativa de usuario (diferentes actores) |
| Asistente | Registrar procedimiento quirúrgica | Registrar la información de un procedimiento quirúrgico realizado a un paciente con los siguientes datos: ID paciente, nombre del paciente, tipo de procedimiento, ID cirujano, recomendaciones específicas (opcional) |
| Cirujano/Asistente | Realizar seguimientos de las interacciones registradas por el Bot con los pacientes | Poder visualizar y analizar la información enviada por los pacientes al Bot y hacer un doble check del triage realizado por el Bot. |
| Bot Lili | Recordatorios de Citas | Revisará las citas agendadas de los pacientes y enviará recordatorios de citas por medio de emails/mensajes de Telegram. |
| Bot Lili | Recordatorio de procedimientos postoperatorio | Revisar por cada paciente las recomendaciones indicadas en sus documentos postoperatorios, como horarios y cantidades de medicamentos diarios, terapias, entre otros. |
| Bot Lili | Requerir evidencias postoperatorio | Si el seguimiento del protocolo del postoperatorio lo indica, el bot debe pedirle al paciente evidencias de la toma de medicamentos u otros temas relacionados. Las evidencias serán enviadas por medio de audios, textos, fotos o vídeos. |
| Paciente | Chat con Bot Lili | El paciente podrá interactuar por medio de un chat con el Bot Lili sobre algún tema o duda médica en particular relacionada a su cirugía y postoperatorio. El Bot analizará esta información y consultará en la base de datos vectorial una posible respuesta; si de pronto no obtuviera la información necesaria, deberá realizar un paso extra para enviar la consulta/duda al médico y/o asistente asignado al paciente. |
| Cirujano/Asistente | Consultar información del Chat con Bot Lili | Revisar las conversaciones realizadas entre los pacientes y el Bot Lili y, dado el caso, poder intervenir en ellas. |

