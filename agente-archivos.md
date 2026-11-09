# Clover con archivos restringidos

[Inicio](README.md) · [Instalación](instalacion-windows.md) · [Prompt de Pong](prompts/02-pong.md)

El chat convencional no puede guardar archivos. Para la prueba de Pong añadimos un servicio MCP local con cuatro herramientas. El modelo solicita acciones y el servicio decide qué rutas acepta; la restricción se aplica en el programa, no en una promesa escrita en el prompt.

## 1. Prepara primero el chat

Completa [la instalación](instalacion-windows.md), comprueba que responde y detén el servidor con Ctrl+C. Utilizaremos el mismo modelo y el mismo reparto de memoria. Python debe estar disponible con `python --version`.

## 2. Abre el modo de archivos

Haz doble clic en **Iniciar-archivos.cmd**. El lanzador crea una configuración MCP local con la ruta de tu Python y arranca directamente el servidor con el alias **Clover-Archivos-64K**. Las rutas se calculan desde la carpeta descargada; no hay que editar un INI ni copiar rutas personales.

El servicio crea la carpeta **CloverPong** dentro de esa carpeta. Es la única carpeta de trabajo autorizada. Usa una copia de la guía en una carpeta local normal: se rechazan carpetas con enlaces o puntos de redirección en sus antecesores.

Abre **http://127.0.0.1:8080/** y crea un chat nuevo. Comprueba que aparece **Clover-Archivos-64K**. En el registro de arranque debe figurar el descubrimiento de cuatro herramientas:

```text
CloverPong_list_files
CloverPong_read_file
CloverPong_write_file
CloverPong_edit_file
```

El arranque es directo, con un solo modelo. No se utiliza el panel router multimodelo: en la versión comprobada no reenviaba correctamente las herramientas del perfil hijo al chat.

## 3. Comprueba las herramientas

Envía primero:

```text
Utiliza CloverPong_list_files y dime qué carpeta está autorizada y qué archivos contiene. No crees ni modifiques archivos.
```

Si aparece una solicitud de autorización, revisa el nombre de la herramienta. Una respuesta con una ruta inventada no basta: debe verse una llamada real a `CloverPong_list_files` y su resultado. Si falla, comprueba en la consola que Python se inicia y que el MCP descubre cuatro herramientas.

## 4. Crea el juego

En otro chat nuevo copia [el prompt completo de Pong](prompts/02-pong.md). Debe usar `write_file` para guardar `index.html` y comprobar su existencia. Abre la carpeta `CloverPong` y verifica que está allí. El archivo es distinto del ejemplo de referencia que incluimos en `ejemplos/pong`.

Lee el HTML antes de abrirlo. Las herramientas están limitadas a archivos, pero el JavaScript generado se ejecutará en el navegador cuando abras el juego. En el ejemplo original se ha revisado que no haya recursos externos ni peticiones de red.

## Qué puede hacer y qué queda bloqueado

| Permitido | Bloqueado |
| --- | --- |
| Listar archivos de CloverPong | Acceder al resto de Windows |
| Leer texto UTF-8 | Ejecutar órdenes o abrir programas |
| Crear o reemplazar un archivo | Subcarpetas y rutas `..` |
| Sustituir una aparición exacta de texto | Rutas UNC, dispositivos y flujos ADS |
| HTML, CSS, JS, JSON, TXT y MD | Enlaces simbólicos, puntos de redirección y enlaces duros al leer/escribir |

El límite es de **2.000.000 de bytes por archivo**. Las validaciones usan rutas finales y handles de Windows; los directorios de la raíz se mantienen abiertos para impedir su sustitución mientras sirve las herramientas. No se habilitan `--agent`, `--tools all`, shell ni un puente HTTP adicional.

Es una restricción por herramientas, **no una máquina virtual ni una cuenta aislada**. El servicio Python conserva los permisos de tu usuario y sus registros guardan el contenido de las llamadas. No pongas información privada en la carpeta de pruebas ni publiques `registros` o `mcp-local.json`.

Para comprobar las operaciones permitidas y los bloqueos sin cargar el modelo:

```powershell
python .\scripts\archivos-restringidos.py --selftest
```

Esta prueba escribe `control.txt` en CloverPong y un centinela en registros; verifica que no puede modificar ese centinela desde las herramientas. Debe terminar con `PASS`. Usa una carpeta de pruebas sin documentos que quieras conservar: `write_file` puede reemplazar archivos dentro de CloverPong.

Para terminar, pulsa **Ctrl+C** en la ventana del servidor. Antes de volver al chat convencional, espera a que se cierre. Los dos lanzadores comparten el puerto 8080 y se usan de uno en uno.
