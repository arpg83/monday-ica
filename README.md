# monday-integration-ICA
Simple FastAPI Server for ICA Integration with Monday

https://developer.monday.com/apps/docs/mondaycom-mcp-integration

https://developer.monday.com/api-reference/reference/about-the-api-reference


Documentacion de API rest Monday:

Creación
1. **Crear tablero** (`/monday/board/create`): Este endpoint permite crear un nuevo tablero en Monday.com. Los parámetros de entrada incluyen el nombre del tablero y su clase (publico o privado). Se devuelve el ID del tablero creado.
2. **Crear grupo** (`/monday/board_group/create`): Este endpoint crea un nuevo grupo dentro de un tablero de Monday.com. Los parámetros de entrada son el ID del tablero y el nombre del grupo. Se devuelve el ID del grupo creado.
3. **Crear tarea/subtarea** (`/monday/item/create`): Este endpoint crea una nueva tarea o subtarea en un tablero de Monday.com. Los parámetros de entrada incluyen el nombre de la tarea, el ID del tablero y el grupo, y los valores de las columnas. Se devuelve el ID de la tarea creada.
4. **Crear subtarea** (`/monday/subitem/create`): Este endpoint crea una nueva subtarea dentro de una tarea de Monday.com. Los parámetros de entrada incluyen el nombre de la subtarea, el ID de la tarea padre y los valores de las columnas. Se devuelve el ID de la subtarea creada.
5. **Crear actualización/comentario** (`/monday/comment/update`): Este endpoint crea una actualización o comentario en una tarea de Monday.com. Los parámetros de entrada son el ID de la tarea y el texto de la actualización. Se devuelve la información de la actualización creada.
6. **Crear documento** (`/monday/doc/create`): Este endpoint crea un nuevo documento en Monday.com. Los parámetros de entrada incluyen el título del documento, el ID del espacio de trabajo (opcional), el ID del tablero (opcional), el tipo de documento y los valores de las columnas. Se devuelve la URL del documento creado.
7. **Crear documento por espacio de trabajo** (`/monday/doc/create/by_workspace`): Este endpoint crea un nuevo documento en un espacio de trabajo de Monday.com. Los parámetros de entrada incluyen el título del documento, el ID del espacio de trabajo y el tipo de documento. Se devuelve la URL del documento creado.
8. **Crear documento por tablero y columna** (`/monday/doc/create/by_item_column`): Este endpoint crea un nuevo documento en un tablero de Monday.com. Los parámetros de entrada incluyen el título del documento, el ID de la columna y el ID de la tarea. Se devuelve la URL del documento creado.
9. **Crear columna** (`/monday/columns/create`): Este endpoint crea una nueva columna en un tablero de Monday.com. Los parámetros de entrada incluyen el ID del tablero, el título de la columna, el tipo y los valores predeterminados. Se devuelve el ID de la columna creada.

Lectura

1. **Listar tableros** (`/monday/boards/list`): Este endpoint lista todos los tableros disponibles en Monday.com. Los parámetros de entrada incluyen el límite y la página para la paginación. Se devuelve una lista de tableros.
2. **Listar grupos de un tablero** (`/monday/board_groups/get`): Este endpoint lista todos los grupos de un tablero de Monday.com. Los parámetros de entrada son el ID del tablero. Se devuelve una lista de grupos.
3. **Listar tareas en grupos** (`/monday/item_in_group/list`): Este endpoint lista todas las tareas y subtareas en los grupos de un tablero de Monday.com. Los parámetros de entrada incluyen el ID del tablero y los IDs de los grupos. Se devuelve una lista de tareas y subtareas.
4. **Listar subtareas en tareas** (`/monday/subitem_in_item/list`): Este endpoint lista todas las subtareas de una tarea de Monday.com. Los parámetros de entrada son el ID de la tarea. Se devuelve una lista de subtareas.
5. **Listar actualizaciones de una tarea** (`/monday/item/get_item_updates`): Este endpoint lista las actualizaciones o comentarios de una tarea de Monday.com. Los parámetros de entrada son el ID de la tarea y el límite. Se devuelve una lista de actualizaciones.
6. **Listar documentos** (`/monday/docs/list`): Este endpoint lista todos los documentos en Monday.com. Los parámetros de entrada incluyen una lista de IDs de documentos y el límite. Se devuelve una lista de documentos.
7. **Listar usuarios** (`/monday/users/list`): Este endpoint lista todos los usuarios de Monday.com. Se devuelve una lista de usuarios.
8. **Listar espacios de trabajo** (`/monday/workspaces/list`): Este endpoint lista todos los espacios de trabajo de Monday.com. Se devuelve una lista de espacios de trabajo.
9. **Listar columnas de un tablero** (`/monday/columns/get`): Este endpoint lista todas las columnas de un tablero de Monday.com. Los parámetros de entrada son el ID del tablero. Se devuelve una lista de columnas.
10. **Obtener tarea por ID** (`/monday/item/get_item_by_id`): Este endpoint recupera tareas por sus IDs. Los parámetros de entrada son una lista de IDs de tareas. Se devuelve una lista de tareas con sus detalles.

Actualización

1. **Actualizar columnas de tarea/subtarea** (`/monday/item/update`): Este endpoint actualiza los valores de las columnas de una tarea o subtarea de Monday.com. Los parámetros de entrada incluyen el ID del tablero, el ID de la tarea, y los valores de las columnas. Se devuelve la información de la tarea actualizada.
2. **Mover tarea a grupo** (`/monday/item/move_item_to_group`): Este endpoint mueve una tarea a otro grupo dentro de un tablero de Monday.com. Los parámetros de entrada son el ID de la tarea y el ID del nuevo grupo. Se devuelve el ID de la tarea movida.
3. **Archivar tarea** (`/monday/archive/item`): Este endpoint archiva una tarea de Monday.com. Los parámetros de entrada son el ID de la tarea. Se devuelve la información de la tarea archivada.

Eliminación

1. **Eliminar grupo** (`/monday/group/delete`): Este endpoint elimina un grupo de un tablero de Monday.com. Los parámetros de entrada son el ID del tablero y el ID del grupo. Se devuelve la información de la acción realizada.
2. **Eliminar tarea** (`/monday/item/delete`): Este endpoint elimina una tarea de Monday.com. Los parámetros de entrada son el ID de la tarea. Se devuelve la información de la acción realizada.
3. **Eliminar columna** (`/monday/column/delete`): Este endpoint elimina una columna de un tablero de Monday.com. Los parámetros de entrada son el ID del tablero y el ID de la columna. Se devuelve la información de la acción realizada.

Otros

1. **Obtener tareas de un tablero** (`/monday/board/fetch_items_by_board_id`): Este endpoint lista todas las tareas, subtareas y grupos de un tablero de Monday.com. Los parámetros de entrada son el ID del tablero. Se devuelve una lista de grupos, tareas y subtareas.
2. **Procesar estado de archivo Excel** (`/monday/estado_proceso_excel`): Este endpoint dev
