# Qué ocurrió en las dos pruebas

[Inicio](README.md) · [Historia](prompts/01-historia.md) · [Pong](prompts/02-pong.md)

## Resultados de la grabación

| Prueba | Tokens generados | Tiempo aproximado | Velocidad reportada |
| --- | ---: | ---: | ---: |
| Historia | 2.475 | 72 s | 34,11 tokens/s |
| Pong | 4.690 | 150 s | 31,24 tokens/s |

Son las cifras recogidas por el autor durante sus pruebas en Llama UI, no benchmarks universales. Los tiempos están redondeados: dividir tokens entre el tiempo aproximado no tiene por qué dar exactamente la velocidad mostrada. La generación puede incluir razonamiento y, en Pong, contenido de herramientas; 2.475 tokens no son 2.475 palabras de relato.

**Procedencia y alcance:** los prompts completos y estas cifras los ha facilitado el autor de las grabaciones. Se conservan registros locales de las herramientas y el HTML original; confirman una escritura correcta de `index.html` y una comprobación posterior de archivos. No se dispone aquí del vídeo original ni de la respuesta íntegra de la historia para volver a cronometrar, contar sus palabras o cotejar las estadísticas del chat. Por tanto, esas comprobaciones de la grabación se presentan como observaciones del autor, no como nuevas mediciones independientes.

### Historia: respeta la forma, falla en la condición temporal

Según la revisión de la grabación, entrega 100 palabras y termina con «Entonces comprendió que nunca había estado solo». Sin embargo, no resuelve correctamente que el mensaje recibido desde la Tierra **se vaya a enviar dentro de 50 años**. Cumplir la extensión y el remate no significa haber cumplido todo el encargo.

### Pong: crea el archivo, pero necesita una revisión

Clover utiliza herramientas y guarda el juego. El archivo recuperado coincide con el contenido escrito en el registro local de `write_file`. El autor lo abre en Chrome y observa pelota y marcador funcionando. También señala que **la pala izquierda se mueve menos fluida que la derecha**. No se ha determinado la causa ni se ha realizado una reparación completa.

Compartimos [el HTML original](ejemplos/pong/index.html), sin corregirlo para que parezca mejor de lo que fue. No se ha validado exhaustivamente la partida, todas las colisiones ni el comportamiento en distintos navegadores y teclados.

## Equipo y configuración

| Elemento | Valor comprobado |
| --- | --- |
| Sistema | Windows de 64 bits |
| CPU | Intel Core i7-13620H |
| RAM instalada | 32 GB nominales; Windows informa de unos 31,64 GiB utilizables |
| GPU | NVIDIA GeForce RTX 5060 Laptop GPU |
| VRAM comunicada por NVIDIA | 8.151 MiB, clase de 8 GB |
| Controlador | 621.14 |
| Motor real | llama.cpp 0.9.0-dev, build 12144, commit 69ee2ecc0 |
| Compilación | Clang 20.1.8 para Windows x86_64, distribución CUDA 13.4 |
| Modelo | Clover-35B-A3B-Preview-Q4_K_M-AR.gguf, derivado local del Q4_K_M oficial |
| Generación | Autorregresiva; sin difusión ni especulación |
| Contexto / sesiones | 65.536 / 1 |
| Expertos en CPU | Primeras 36 capas |
| Descarga GPU | all, con la excepción anterior para expertos |
| Atención / cachés | Flash Attention on; K y V f16 |
| Batch / microbatch | 256 / 128 |
| Hilos CPU | Automáticos; 10 elegidos por el motor en el registro |

El perfil del chat y el de archivos coinciden en esos ajustes. El segundo añade únicamente el MCP restringido. El acceso local «Clover - Archivos restringidos» arranca un servidor dedicado, lee el INI habitual y utiliza ese perfil; los lanzadores públicos reproducen los valores sin depender de rutas de ese ordenador.

En una prueba local previa de tres respuestas cortas de 160 tokens se registraron **34,73 / 33,90 / 35,23 tokens/s**, usando el mismo GGUF AR, contexto y reparto de expertos. NVIDIA indicó **6.492 MiB de memoria total de GPU ocupada**. Es una referencia separada de las dos grabaciones y puede incluir otros procesos. No representa el pico de consumo de Pong ni demuestra cuánta RAM necesita como mínimo.

No se ha registrado una medición fiable del pico de RAM de las dos grabaciones. No debe confundirse la RAM instalada con la consumida por el proceso. Tampoco se ha ensayado una entrada de 65.536 tokens completa.

## Cómo comparar tu resultado

Usa un chat nuevo por prueba y el prompt sin cambios. Apunta modelo, cuantización, contexto, hardware y estadísticas al finalizar. Para la historia, cuenta solo el relato y comprueba cada condición. Para Pong, verifica la llamada de escritura, el archivo en disco y su funcionamiento. Obtener una velocidad parecida no garantiza obtener la misma respuesta.

No atribuyas la velocidad de estas pruebas a la difusión: la copia AR no conserva los tensores de ese modo. Probar difusión o autoespeculación necesitaría otro recorrido compatible y una comparación separada en el mismo ordenador.
