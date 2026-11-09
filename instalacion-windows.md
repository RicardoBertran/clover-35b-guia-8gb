# Instalar Clover en Windows

[Inicio](README.md) · [Archivos restringidos](agente-archivos.md) · [Resultados](resultados.md)

Este recorrido reproduce el modo autorregresivo usado en las pruebas. Necesitarás descargar unos 23 GB de modelo y preparar una segunda copia local. No necesitas programar ni instalar Llama UI por separado: la interfaz viene dentro de llama.cpp.

## 1. Comprueba tu ordenador

El equipo comprobado utiliza **Windows de 64 bits, Intel Core i7-13620H, RTX 5060 Laptop de 8 GB y 32 GB de RAM**. Esta guía usa CUDA para NVIDIA. No hemos comprobado este recorrido en AMD, Intel ni en equipos con menos RAM.

Abre **Administrador de tareas → Rendimiento** para ver CPU, memoria y GPU. En la GPU, mira la **memoria dedicada**; la memoria compartida no sustituye a la VRAM. Cierra otras aplicaciones que estén usando la gráfica antes de cargar el modelo.

Necesitas espacio libre para el GGUF original, la copia AR y el motor. Solo las dos copias del modelo suman alrededor de 46 GB decimales. Eso es espacio en disco, no un requisito de RAM. No se ha establecido un mínimo de RAM mediante pruebas: 32 GB es la capacidad del equipo utilizado.

## 2. Descarga la guía y llama.cpp

En la portada de este repositorio, pulsa **Code → Download ZIP**. Extrae el ZIP en una carpeta local normal, por ejemplo `C:\IA\clover-35b-guia-8gb`. No trabajes dentro del ZIP ni dentro de una carpeta enlazada o sincronizada mediante enlaces.

Usaremos **llama.cpp b12144**, la versión comprobada, con CUDA 13.4. Descarga estos dos archivos de [la publicación oficial](https://github.com/ggml-org/llama.cpp/releases/tag/b12144):

- [llama-b12144-bin-win-cuda-13.4-x64.zip](https://github.com/ggml-org/llama.cpp/releases/download/b12144/llama-b12144-bin-win-cuda-13.4-x64.zip).
- [cudart-llama-bin-win-cuda-13.4-x64.zip](https://github.com/ggml-org/llama.cpp/releases/download/b12144/cudart-llama-bin-win-cuda-13.4-x64.zip).

Crea una carpeta `motor` dentro de la guía y extrae **el contenido de ambos ZIP en ella**. `llama-server.exe` y las DLL deben quedar juntos, directamente en `motor`. No basta con copiar solo el ejecutable. El controlador NVIDIA del equipo probado es el 621.14; no se ha determinado el controlador mínimo compatible. Si faltan bibliotecas de Visual C++, utiliza el [redistribuible x64 de Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe).

Para la preparación local del GGUF hace falta **Python 3.11 o posterior de 64 bits**. Descárgalo de [python.org](https://www.python.org/downloads/windows/). En el instalador, activa **Add python.exe to PATH**. No hace falta instalar paquetes de Python. La prueba se ha hecho con Python 3.12.14.

## 3. Descarga el modelo exacto

Abre [Files and versions del GGUF oficial](https://huggingface.co/Diffuspace/Clover-35B-A3B-Preview-GGUF/tree/main) y descarga **Clover-35B-A3B-Preview-Q4_K_M.gguf**. También tienes el [enlace directo al archivo](https://huggingface.co/Diffuspace/Clover-35B-A3B-Preview-GGUF/resolve/main/Clover-35B-A3B-Preview-Q4_K_M.gguf?download=true).

Crea la carpeta `modelos` dentro de la guía y guarda allí el GGUF. No descargues BF16, otros tipos de cuantización ni archivos de otro repositorio para seguir estos pasos.

## 4. Prepara la copia AR

El archivo oficial utilizado en las pruebas necesita una adaptación para esta versión de llama.cpp. El script incluido conserva el original y crea `Clover-35B-A3B-Preview-Q4_K_M-AR.gguf`. Comprueba primero el SHA256 del origen; si ha cambiado, se detiene. No modifica los pesos cuantizados: retira 120 tensores exclusivos de difusión, añade la información del experto compartido y convierte 30 tensores recurrentes a la convención del motor.

En el Explorador, entra en la carpeta de la guía, escribe `powershell` en su barra de direcciones y pulsa Intro. Copia cada línea:

```powershell
python --version
python .\scripts\preparar-modelo-ar.py .\modelos\Clover-35B-A3B-Preview-Q4_K_M.gguf
```

Espera al mensaje **Modelo AR preparado**. La lectura del archivo y la copia pueden tardar. Si el destino ya existe, el script se detiene y no lo sobrescribe. Si se interrumpe, deja un `.gguf.part`: con el proceso ya cerrado, elimina solo ese archivo parcial antes de repetir.

El SHA256 del original comprobado es:

```text
4d439bb832487fbb91d0a739a5746cf3089bde4137c17050576b24e6dba3539c
```

La carpeta debe quedar así:

```text
clover-35b-guia-8gb/
  Iniciar-chat.cmd
  Iniciar-archivos.cmd
  scripts/
  motor/
    llama-server.exe
    ... DLL de los dos ZIP
  modelos/
    Clover-35B-A3B-Preview-Q4_K_M.gguf
    Clover-35B-A3B-Preview-Q4_K_M-AR.gguf
```

## 5. Conoce el perfil que vas a usar

Los lanzadores incluidos aplican estos ajustes del equipo probado:

| Ajuste | Valor | Para qué sirve |
| --- | --- | --- |
| Contexto | 65.536 | Espacio total para entrada, historial y respuesta |
| Conversaciones simultáneas | 1 | Evita repartir el contexto entre varias sesiones |
| Capas GPU | all | Descarga a GPU lo permitido por las excepciones de CPU |
| Expertos en CPU | Primeras 36 capas | Mantiene gran parte de los expertos en RAM |
| Ajuste automático de memoria | off | Conserva el reparto explícito de la prueba |
| Flash Attention | on | Usa la implementación de atención optimizada |
| Batch / microbatch | 256 / 128 | Tamaño de procesamiento de la entrada |
| Caché K / V | f16 / f16 | Tipos de almacenamiento del contexto |
| Hilos CPU | Automáticos | El motor eligió 10 en el equipo probado |

`fit-target=768` se conserva en el lanzador, pero con `fit=off` no es una reserva de VRAM garantizada. Tampoco se limita la RAM a un valor fijo. Consulta los consumos verificados en [resultados](resultados.md).

## 6. Arranca Clover

Haz doble clic en **Iniciar-chat.cmd**. Deja la ventana abierta. La primera carga lee el modelo desde el disco; espera hasta que aparezca `listening on http://127.0.0.1:8080`.

El lanzador verifica la versión del motor y se detiene si el puerto ya está ocupado. No cierra otros servidores ni cambia tus perfiles existentes. Utiliza solo el equipo local: no hace falta abrir puertos del router.

## 7. Abre Llama UI

Abre **http://127.0.0.1:8080/** en Chrome. Pulsa **New chat / Nuevo chat**. Este arranque sirve un solo modelo: **Clover-35B-A3B-Q4_K_M**. Si la interfaz muestra un selector, ese es el nombre que debes ver. No reutilices una conversación asociada a otro modelo ni una pestaña de otro servidor.

## 8. Envía tu primer mensaje

```text
Responde en español: ¿cuánto es 2 más 2?
```

Pulsa Enviar y espera a que termine. Puede mostrar primero un apartado de razonamiento. Comprueba que la respuesta sea coherente y dé **4**. Después abre un chat nuevo y copia [el prompt original de la historia](prompts/01-historia.md).

## 9. Consulta velocidad y memoria

Al terminar una respuesta, Llama UI muestra estadísticas debajo del mensaje: tokens, tiempo y tokens/s. El tiempo de generación y el tiempo total de espera no son necesariamente iguales: este último puede incluir carga, procesamiento de la entrada y herramientas.

En **Administrador de tareas → Rendimiento → GPU**, consulta memoria dedicada y compartida. En **Memoria**, mira el uso total de RAM. También puedes usar, en otra ventana de PowerShell:

```powershell
nvidia-smi
```

El consumo mostrado por NVIDIA puede incluir otras aplicaciones. Los tokens generados pueden incluir razonamiento y llamadas a herramientas: no equivalen a las palabras del texto final.

## 10. Detén el servidor

Vuelve a la ventana de **Iniciar-chat.cmd** y pulsa **Ctrl+C**. Si Windows pregunta si deseas terminar el trabajo por lotes, confirma con la opción que indique. Espera a que el servidor termine. **Cerrar Chrome no detiene el modelo.** Puedes comprobar que el consumo de GPU baja y que la dirección local deja de responder.

## Si algo falla

| Lo que ves | Qué comprobar |
| --- | --- |
| `python` no se reconoce o abre la tienda | Instala Python de python.org con PATH y abre otra consola |
| Falta una DLL o no arranca el ejecutable | Extrae ambos ZIP en `motor`; comprueba el controlador y el redistribuible de Microsoft |
| SHA256 distinto | No fuerces la adaptación: la descarga está incompleta o el archivo ya no es el mismo |
| El modelo no carga | Comprueba el sufijo `-AR.gguf`, la versión b12144 y la última línea de error |
| `out of memory` | Cierra otros usos de GPU y RAM; no está validado el mismo perfil en equipos con menos memoria |
| 8080 ocupado | Detén el servidor anterior desde su propia ventana |
| Solo escribe código en el chat | Para guardar archivos necesitas [el modo de herramientas](agente-archivos.md) |

Este recorrido reproduce los ajustes locales verificados. No se ha ensayado una instalación limpia completa de Windows ni una descarga nueva de los pesos para preparar esta guía.
