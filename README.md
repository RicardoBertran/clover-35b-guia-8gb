# Clover 35B en una gráfica de 8 GB

Clover ha escrito una historia y ha creado un Pong guardándolo directamente en el ordenador. Las dos pruebas tienen aciertos y fallos: el relato se equivoca con una condición temporal y el juego necesita pulir el movimiento de una pala. Aquí tienes la instalación de Windows, los dos prompts originales y el juego tal como salió.

## Índice

- [Empezar aquí](#empezar-aquí)
- [Instalación paso a paso en Windows](instalacion-windows.md)
- [Permitir que Clover cree y edite archivos](agente-archivos.md)
- [Prompt de la historia](prompts/01-historia.md) y [prompt de Pong](prompts/02-pong.md)
- [Resultados y equipo de las pruebas](resultados.md)
- [Pong original para descargar](ejemplos/pong/)
- [Modelo, fuentes y licencias](#modelo-fuentes-y-licencias)

## Empezar aquí

**El equipo probado tiene una RTX 5060 Laptop de 8 GB y 32 GB de RAM.** El modelo no cabe entero en la gráfica: utiliza también la memoria del ordenador. «8 GB» se refiere a la VRAM, no a la RAM total necesaria.

1. Sigue [la instalación de Windows](instalacion-windows.md). Incluye la descarga exacta y los archivos para arrancar con doble clic.
2. Prueba [la historia de 100 palabras](prompts/01-historia.md).
3. Para crear Pong sin copiar código, sigue primero [la guía de archivos restringidos](agente-archivos.md).

Si solo quieres ver el resultado, descarga [el HTML original](ejemplos/pong/index.html) y ábrelo en tu navegador. [Aquí están los controles y los fallos conocidos](ejemplos/pong/README.md).

## Qué es Clover

[Clover-35B-A3B-Preview](https://huggingface.co/Diffuspace/Clover-35B-A3B-Preview) es un modelo de texto de DiffuSpace, publicado en Hugging Face el **24 de octubre de 2026**. Parte de Qwen3.6-35B-A3B y combina una arquitectura de mezcla de expertos, o MoE, con generación por difusión en bloques. Es una versión preliminar.

Los **35B** son unos 35.000 millones de parámetros totales. Para cada token se activa una selección de expertos: aproximadamente **3.000 millones de parámetros**. Eso reduce el trabajo de cálculo por token, pero no convierte los pesos en un modelo de 3B: los demás expertos deben seguir disponibles en memoria.

### Difusión y modo utilizado en estas pruebas

La generación por difusión trabaja con bloques de posiciones aún sin resolver y puede completar varias en paralelo. Es distinta de la generación autorregresiva, que va añadiendo un token tras otro. El proyecto también describe un modo autoespeculativo: el propio modelo propone varios tokens y después los verifica causalmente.

**Las pruebas de esta guía son autorregresivas. No hemos medido una aceleración por difusión ni por generación especulativa.** Usamos una copia del GGUF oficial adaptada a llama.cpp b12144. La [integración de Clover en llama.cpp](https://github.com/ggml-org/llama.cpp/pull/31306) incorpora el modo AR; la [propuesta de autoespeculación](https://github.com/ggml-org/llama.cpp/pull/31732) es un trabajo separado. El estado de las fuentes se consultó el 9 de noviembre de 2026.

### Cómo funciona con 8 GB de VRAM

La cuantización Q4_K_M reduce el tamaño de los pesos. El GGUF oficial ocupa **22.998.009.248 bytes, unos 21,42 GiB**: todavía supera ampliamente la VRAM disponible. El perfil mantiene en CPU los expertos de las primeras 36 capas y utiliza la GPU para el resto de los cálculos que se descargan en ella. Así se reparte el trabajo entre CPU, RAM y GPU.

El contexto configurado es de **65.536 tokens**, compartidos entre entrada, historial y respuesta. Hemos comprobado que carga y responde con ese ajuste; no hemos validado una conversación que llene todo ese contexto. [Consulta qué consumos están medidos y cuáles no](resultados.md#equipo-y-configuración).

## Qué puedes esperar

En estas pruebas Clover redacta en español y utiliza herramientas para guardar un HTML jugable. También puede cumplir la longitud de una historia y aun así interpretar mal una condición esencial. Crear el archivo tampoco demuestra que el programa esté libre de errores.

Las respuestas pueden variar entre ejecuciones. La velocidad depende del ordenador, el contexto, los ajustes y el trabajo solicitado. Los aproximadamente 31–34 tokens/s de las grabaciones no son una promesa para otros equipos.

## Modelo, fuentes y licencias

- [Modelo oficial y ficha](https://huggingface.co/Diffuspace/Clover-35B-A3B-Preview).
- [GGUF oficial](https://huggingface.co/Diffuspace/Clover-35B-A3B-Preview-GGUF), utilizado como origen de nuestra copia AR.
- [Proyecto Clover](https://github.com/DiffuSpace/Clover-35B-A3B-Preview).
- [llama.cpp](https://github.com/ggml-org/llama.cpp) y [versión b12144](https://github.com/ggml-org/llama.cpp/releases/tag/b12144).
- [Licencia Apache 2.0 del modelo](https://huggingface.co/Diffuspace/Clover-35B-A3B-Preview/blob/main/LICENSE) y [licencia MIT de llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/LICENSE).

La documentación y los scripts de este repositorio se distribuyen con [licencia MIT](LICENSE). El ejemplo de Pong es la salida generada durante la prueba y se comparte bajo esa misma licencia en la medida en que existan derechos aplicables. No se incluyen pesos del modelo ni ejecutables de terceros. La adaptación AR es local y no es una nueva versión oficial de DiffuSpace.
