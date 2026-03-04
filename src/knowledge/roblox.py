"""
Modulo de Conocimiento Gaming/Roblox/Tech para Nebu.

Base de datos de cultura gaming y ciencias de la computacion REAL,
basada en fuentes verificables:
- "A History of Video Games in 64 Objects" — World Video Game Hall of Fame
- GDC (Game Developers Conference) — charlas y postmortems historicos
- Wikipedia (articulos verificados) sobre historia de videojuegos
- Comunicados oficiales de Roblox Corporation, Nintendo, Mojang
- "Masters of Doom" — David Kushner
- "Racing the Beam" — Nick Montfort & Ian Bogost
- "Blood, Sweat, and Pixels" — Jason Schreier

Cada entrada tiene version academica y version `para_ninos`.
Nebu usa la version para_ninos en sus interacciones.
"""

import random

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HISTORIA_GAMING — El nacimiento y evolucion de los videojuegos
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HISTORIA_GAMING = [
    {
        "nombre": "El primer videojuego: Tennis for Two",
        "periodo": "1958",
        "descripcion": (
            "En 1958, el fisico William Higinbotham creo 'Tennis for Two' "
            "en el Laboratorio Nacional de Brookhaven (Nueva York). Usaba un "
            "osciloscopio como pantalla y simulaba una partida de tenis vista "
            "desde el lado. Fue creado para entretener a los visitantes del "
            "laboratorio durante una jornada de puertas abiertas. Nunca fue "
            "patentado ni comercializado."
        ),
        "para_ninos": (
            "El PRIMER videojuego de la historia se llamo 'Tennis for Two' "
            "y lo hizo un cientifico en 1958. Era un juego de tenis en una "
            "pantallita redonda de laboratorio. Lo creo solo para que la gente "
            "se divirtiera visitando su trabajo. No gano ni un centavo con el."
        ),
        "dato_extra": (
            "Higinbotham trabajo en el Proyecto Manhattan. Dijo que crear "
            "Tennis for Two le tomo solo unas pocas horas de diseno."
        ),
    },
    {
        "nombre": "Pong y el nacimiento de la industria",
        "periodo": "1972",
        "descripcion": (
            "En 1972, Nolan Bushnell y Ted Dabney fundaron Atari y lanzaron "
            "Pong, el primer videojuego arcade comercialmente exitoso. El "
            "primer prototipo fue instalado en un bar llamado Andy Capp's "
            "Tavern en Sunnyvale, California. La maquina dejo de funcionar "
            "a los pocos dias porque la caja de monedas estaba tan llena "
            "que se atasco."
        ),
        "para_ninos": (
            "Pong fue el juego que lo CAMBIO TODO. Lo pusieron en un bar "
            "en 1972 y la gente hacia FILA para jugar. La maquina se rompio "
            "a los pocos dias... pero no porque estuviera mal, sino porque "
            "tenia TANTAS monedas adentro que se atasco. Asi nacio Atari "
            "y la industria de los videojuegos."
        ),
        "dato_extra": (
            "Las instrucciones de Pong eran las mas simples de la historia: "
            "'Avoid missing ball for high score' (Evita fallar la pelota "
            "para obtener puntuacion alta)."
        ),
    },
    {
        "nombre": "La era de los arcades",
        "periodo": "1978-1985",
        "descripcion": (
            "Entre 1978 y 1985, los salones arcade dominaron el entretenimiento "
            "juvenil. Space Invaders (1978) fue tan popular en Japon que causo "
            "escasez de monedas de 100 yenes. Pac-Man (1980) se convirtio en "
            "el primer personaje reconocible de videojuegos. En 1982, la "
            "industria arcade en EE.UU. genero mas dinero que Hollywood y la "
            "industria musical combinadas."
        ),
        "para_ninos": (
            "Hubo una epoca en que los ninos iban a SALONES LLENOS de "
            "maquinas de videojuegos llamados arcades. Space Invaders fue "
            "tan popular en Japon que se acabaron las monedas del pais. "
            "Y Pac-Man se volvio tan famoso como Mickey Mouse. Los arcades "
            "ganaban MAS dinero que todas las peliculas de Hollywood juntas."
        ),
        "dato_extra": (
            "El record mundial original de Pac-Man (puntaje perfecto de "
            "3,333,360 puntos) fue logrado por Billy Mitchell en 1999, "
            "jugando durante casi 6 horas sin perder una sola vida."
        ),
    },
    {
        "nombre": "La revolucion de las consolas hogare\u00f1as",
        "periodo": "1985-presente",
        "descripcion": (
            "Despues del crash de 1983, Nintendo revivio la industria con el "
            "NES (Nintendo Entertainment System) en 1985. Incluia Super Mario "
            "Bros., que vendio mas de 40 millones de copias. Esto abrio paso "
            "a la guerra de consolas: SNES vs. Sega Genesis en los 90, "
            "PlayStation vs. Nintendo 64, y la era moderna con PlayStation, "
            "Xbox y Nintendo Switch."
        ),
        "para_ninos": (
            "Cuando parecia que los videojuegos iban a desaparecer, llego "
            "Nintendo con el NES y Super Mario Bros. Fue como un superhero "
            "salvando el dia. Desde entonces, las consolas llegaron a las "
            "casas: Super Nintendo, PlayStation, Xbox, Nintendo Switch. "
            "Ahora puedes jugar en tu sala lo que antes solo existia en arcades."
        ),
        "dato_extra": (
            "Super Mario Bros. fue el juego mas vendido del mundo durante "
            "casi 25 anhos, hasta que Wii Sports lo supero en 2009."
        ),
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONCEPTOS_COMPUTACION — Como funcionan las computadoras por dentro
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONCEPTOS_COMPUTACION = [
    {
        "nombre": "Codigo binario",
        "concepto": "El lenguaje de las computadoras: ceros y unos",
        "descripcion": (
            "Las computadoras solo entienden dos numeros: 0 y 1. Esto se "
            "llama sistema binario. Cada 0 o 1 es un 'bit', y 8 bits forman "
            "un 'byte'. Toda imagen, sonido, video y texto que ves en una "
            "pantalla esta representado internamente como largas cadenas de "
            "ceros y unos. Por ejemplo, la letra 'A' en codigo ASCII es "
            "01000001."
        ),
        "para_ninos": (
            "Las computadoras solo saben contar con DOS numeros: 0 y 1. "
            "Con esos dos numeritos pueden hacer TODO: mostrar fotos, "
            "tocar musica, correr juegos. La letra 'A' para una computadora "
            "es 01000001. Es como un idioma secreto de prendido y apagado."
        ),
    },
    {
        "nombre": "Pixeles",
        "concepto": "Los puntitos que forman las imagenes",
        "descripcion": (
            "Un pixel (picture element) es el punto mas pequeno que puede "
            "mostrar una pantalla. Las pantallas modernas tienen millones de "
            "pixeles. Una pantalla Full HD tiene 1920x1080 = 2,073,600 pixeles. "
            "Cada pixel puede mostrar un color diferente, y juntos forman la "
            "imagen completa. Los juegos retro usaban muy pocos pixeles, por "
            "eso se veian 'cuadrados'."
        ),
        "para_ninos": (
            "Si te acercas MUCHO a una pantalla, vas a ver puntitos de "
            "colores. Esos puntitos se llaman PIXELES. Una pantalla HD tiene "
            "mas de 2 MILLONES de puntitos. Los juegos viejos como Mario Bros "
            "usaban pocos pixeles, por eso se veian cuadraditos. Los juegos "
            "de hoy usan millones y por eso se ven tan reales."
        ),
    },
    {
        "nombre": "Algoritmos",
        "concepto": "Instrucciones paso a paso para resolver problemas",
        "descripcion": (
            "Un algoritmo es una secuencia ordenada de instrucciones para "
            "resolver un problema. El nombre viene del matematico persa "
            "Al-Juarismi (siglo IX). Todo programa de computadora esta hecho "
            "de algoritmos. Desde ordenar una lista de numeros hasta "
            "determinar que video recomendarte en YouTube, todo son "
            "algoritmos ejecutados millones de veces por segundo."
        ),
        "para_ninos": (
            "Un ALGORITMO es como una receta de cocina para la computadora: "
            "instrucciones paso a paso. 'Primero haz esto, luego esto otro, "
            "si pasa esto haz aquello.' Cuando un enemigo en un videojuego "
            "te persigue, esta siguiendo un algoritmo. Cuando YouTube te "
            "recomienda un video, tambien es un algoritmo."
        ),
    },
    {
        "nombre": "Latencia (Ping)",
        "concepto": "Por que los juegos online a veces van lento",
        "descripcion": (
            "La latencia es el tiempo que tarda un dato en viajar desde tu "
            "computadora hasta el servidor del juego y volver. Se mide en "
            "milisegundos (ms) y se le llama 'ping'. Un ping de 20ms es "
            "excelente, 100ms es aceptable, y mas de 200ms causa 'lag' "
            "notable. La senal viaja por cables de fibra optica a la "
            "velocidad de la luz, pero la distancia fisica importa."
        ),
        "para_ninos": (
            "Cuando juegas online, tu computadora le manda un mensaje al "
            "servidor diciendo 'me movi aqui' y el servidor contesta. Ese "
            "viaje de ida y vuelta se llama PING. Si el ping es bajo (20ms), "
            "todo va rapido. Si es alto (200ms), sientes LAG y todo va "
            "lento y raro. Es como gritar en un canon: si es corto, el eco "
            "vuelve rapido. Si es largo, tarda."
        ),
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIGURAS_GAMING — Las personas que crearon los juegos que conocemos
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FIGURAS_GAMING = [
    {
        "nombre": "Shigeru Miyamoto",
        "titulo": "Creador de Mario, Zelda y Donkey Kong",
        "descripcion": (
            "Disenador japones de Nintendo. Creo Super Mario Bros., "
            "The Legend of Zelda y Donkey Kong. Miyamoto no era programador "
            "sino artista industrial. Se inspiro en sus aventuras de nino "
            "explorando cuevas y bosques cerca de Kioto. Es considerado "
            "el disenador de videojuegos mas influyente de la historia."
        ),
        "para_ninos": (
            "Shigeru Miyamoto es el papa de Mario, Zelda y Donkey Kong. "
            "De chiquito exploraba cuevas y bosques cerca de su casa en "
            "Japon, y esas aventuras le inspiraron para crear sus juegos. "
            "No sabia programar, era artista. Pero sus ideas cambiaron "
            "los videojuegos para siempre."
        ),
    },
    {
        "nombre": "David Baszucki",
        "titulo": "Creador de Roblox",
        "descripcion": (
            "Ingeniero y empresario estadounidense. Cofundo Roblox en 2004 "
            "(lanzado en 2006) junto a Erik Cassel. Antes de Roblox, creo "
            "un programa educativo de simulacion de fisica llamado "
            "'Interactive Physics' usado en escuelas. Roblox nacio de la "
            "idea de que los jugadores pudieran crear sus propios mundos "
            "y experiencias."
        ),
        "para_ninos": (
            "David Baszucki creo ROBLOX. Antes de eso, hacia programas "
            "de fisica para escuelas. Un dia penso: 'Que tal si los "
            "jugadores pueden CREAR sus propios juegos dentro de un juego?' "
            "Y asi nacio Roblox, donde millones de personas crean mundos "
            "y juegos para que otros los jueguen."
        ),
    },
    {
        "nombre": "Markus 'Notch' Persson",
        "titulo": "Creador de Minecraft",
        "descripcion": (
            "Programador sueco que creo Minecraft en 2009, trabajando solo "
            "desde su departamento. El juego se inspiro en Infiniminer, "
            "Dwarf Fortress y Dungeon Keeper. Minecraft se convirtio en el "
            "videojuego mas vendido de la historia con mas de 300 millones "
            "de copias. En 2014, Microsoft compro Mojang (la empresa de "
            "Notch) por 2,500 millones de dolares."
        ),
        "para_ninos": (
            "Markus 'Notch' Persson creo Minecraft SOLITO en su "
            "departamento en Suecia. Un juego de bloques donde puedes "
            "construir lo que quieras. Se volvio el juego MAS VENDIDO DE "
            "LA HISTORIA con mas de 300 millones de copias. Microsoft lo "
            "compro por 2,500 millones de dolares. Todo empezo con un "
            "programador y una idea simple."
        ),
    },
    {
        "nombre": "Hideo Kojima",
        "titulo": "Creador de Metal Gear Solid",
        "descripcion": (
            "Disenador japones conocido por la saga Metal Gear (1987). "
            "Revoluciono los videojuegos al introducir narrativas "
            "cinematograficas complejas y mecanicas de sigilo. Es uno de "
            "los primeros autores reconocidos del medio. Sus juegos mezclan "
            "filosofia, politica y ciencia ficcion de maneras que nadie "
            "habia intentado antes."
        ),
        "para_ninos": (
            "Hideo Kojima hizo que los videojuegos contaran historias tan "
            "buenas como las peliculas. Creo Metal Gear, donde en vez de "
            "pelear contra todos, tienes que esconderte y ser sigiloso. "
            "Fue uno de los primeros en demostrar que un videojuego puede "
            "hacerte pensar y sentir como una gran pelicula."
        ),
    },
    {
        "nombre": "Toru Iwatani",
        "titulo": "Creador de Pac-Man",
        "descripcion": (
            "Disenador japones de Namco que creo Pac-Man en 1980. Se inspiro "
            "en una pizza a la que le faltaba una rebanada. Queria crear un "
            "juego que atrajera a las mujeres a los arcades, que en esa "
            "epoca estaban dominados por hombres. Pac-Man se convirtio en "
            "un fenomeno cultural mundial y el primer personaje icono de "
            "los videojuegos."
        ),
        "para_ninos": (
            "Toru Iwatani invento Pac-Man en 1980 inspirandose en una PIZZA "
            "a la que le faltaba un pedazo. Queria que mas personas "
            "disfrutaran los videojuegos, no solo los que les gustaba "
            "disparar. Pac-Man se volvio tan famoso que lo conoce todo el "
            "mundo, y todo empezo con una pizza."
        ),
    },
    {
        "nombre": "Ralph Baer",
        "titulo": "El padre de las consolas de videojuegos",
        "descripcion": (
            "Ingeniero aleman-estadounidense que invento la primera consola "
            "de videojuegos: la Magnavox Odyssey (1972). Baer concibio la "
            "idea en 1966 mientras esperaba en una terminal de autobuses. "
            "Penso: 'Si hay 40 millones de televisores en EE.UU., deberia "
            "poder hacerse algo mas que ver programas.' Recibio la Medalla "
            "Nacional de Tecnologia en 2006."
        ),
        "para_ninos": (
            "Ralph Baer invento la PRIMERA CONSOLA de la historia: la "
            "Magnavox Odyssey. La idea se le ocurrio esperando un autobus. "
            "Penso: 'La tele solo sirve para ver programas... Y si pudieramos "
            "JUGAR en ella?' Esa idea cambio el mundo. Sin Ralph Baer, no "
            "existirian PlayStation, Xbox ni Nintendo Switch."
        ),
    },
    {
        "nombre": "Roberta Williams",
        "titulo": "Pionera de los juegos de aventura grafica",
        "descripcion": (
            "Disenadora estadounidense que cofundo Sierra On-Line con su "
            "esposo Ken Williams. Creo la saga King's Quest (1984), el "
            "primer juego de aventura grafica con personaje animado en "
            "pantalla. Fue una de las primeras mujeres prominentes en la "
            "industria de videojuegos y pionera en la narrativa interactiva."
        ),
        "para_ninos": (
            "Roberta Williams fue una de las primeras mujeres en crear "
            "videojuegos. Invento los juegos de aventura grafica, donde "
            "resuelves puzzles y exploras mundos con una historia. Su juego "
            "King's Quest (1984) fue el primero donde veias a tu personaje "
            "caminar por la pantalla. Sin ella, los juegos de aventura no "
            "existirian como los conocemos."
        ),
    },
    {
        "nombre": "Satoru Iwata",
        "titulo": "Presidente de Nintendo (2002-2015)",
        "descripcion": (
            "Programador y ejecutivo japones. Fue programador genio antes "
            "de ser presidente de Nintendo. Programo partes de EarthBound, "
            "Pokemon Stadium y ayudo a comprimir Pokemon Gold/Silver para "
            "que cupiera la region de Kanto completa. Su filosofia era: "
            "'En mi tarjeta dice presidente, pero en mi corazon soy "
            "un gamer.' Fallecio en 2015."
        ),
        "para_ninos": (
            "Satoru Iwata fue presidente de Nintendo, pero antes fue un "
            "programador GENIO. Ayudo a que Pokemon Gold y Silver tuvieran "
            "DOS regiones en vez de una, porque encontro una forma de meter "
            "todo en el cartucho. Siempre decia: 'En mi tarjeta dice "
            "presidente, pero en mi corazon soy un gamer.' Toda la "
            "comunidad gamer lo recuerda con mucho carino."
        ),
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CIENCIA_DETRAS_JUEGOS — Como funcionan los videojuegos por dentro
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CIENCIA_DETRAS_JUEGOS = [
    {
        "nombre": "Graficos 3D: poligonos y vertices",
        "campo": "Graficos por computadora",
        "descripcion": (
            "Todo objeto 3D en un videojuego esta hecho de triangulos "
            "(poligonos). Un cubo son 12 triangulos. Un personaje detallado "
            "puede tener decenas de miles. Cada esquina de un triangulo se "
            "llama vertice. La tarjeta grafica (GPU) calcula la posicion de "
            "cada vertice y colorea cada triangulo 30 a 60 veces por segundo "
            "para crear la ilusion de movimiento."
        ),
        "para_ninos": (
            "Todo lo que ves en un juego 3D esta hecho de TRIANGULOS "
            "diminutos. Un cubo son 12 triangulos. Un personaje puede tener "
            "miles. La tarjeta grafica de tu computadora pinta todos esos "
            "triangulos 60 veces por SEGUNDO. Es como un artista "
            "superrapido dibujando miles de triangulos cada instante."
        ),
    },
    {
        "nombre": "Servidores multijugador",
        "campo": "Redes de computadoras",
        "descripcion": (
            "En un juego online, hay una computadora central (servidor) que "
            "mantiene el 'estado real' del juego. Cada jugador envia sus "
            "acciones al servidor, que las procesa y envia los resultados "
            "a todos. Roblox, por ejemplo, usa miles de servidores en la "
            "nube. El servidor debe procesar las acciones de todos los "
            "jugadores y decidir que es valido para evitar trampas."
        ),
        "para_ninos": (
            "Cuando juegas online, hay una computadora gigante llamada "
            "SERVIDOR que es como el arbitro. Tu computadora le dice 'me "
            "movi aqui' y el servidor revisa si es valido y le avisa a "
            "todos los demas jugadores. Roblox tiene MILES de estos "
            "servidores funcionando al mismo tiempo para que millones "
            "de personas puedan jugar a la vez."
        ),
    },
    {
        "nombre": "Generacion procedural",
        "campo": "Programacion y matematicas",
        "descripcion": (
            "Es cuando la computadora crea contenido usando formulas "
            "matematicas en vez de que un humano lo disene a mano. "
            "Minecraft usa esto: cada mundo es generado por un algoritmo "
            "usando una 'semilla' (seed) numerica. Con la misma semilla, "
            "se genera exactamente el mismo mundo. Hay 2^64 semillas "
            "posibles, es decir, 18 trillones de mundos unicos posibles."
        ),
        "para_ninos": (
            "En Minecraft, nadie diseno tu mundo a mano. Lo creo un "
            "ALGORITMO usando matematicas. Le das un numero (la semilla) "
            "y la computadora genera montanas, rios, cuevas y biomas. "
            "Si usas la misma semilla, obtienes el mismo mundo. Hay "
            "tantas semillas posibles que nunca en la historia se jugaran "
            "todos los mundos de Minecraft."
        ),
    },
    {
        "nombre": "Motores de fisica",
        "campo": "Fisica computacional",
        "descripcion": (
            "Un motor de fisica simula las leyes de la fisica real en el "
            "juego: gravedad, colisiones, friccion, rebotes. Calcula "
            "ecuaciones de Newton muchas veces por segundo. Cuando un "
            "personaje salta, el motor aplica gravedad para hacerlo caer. "
            "Cuando choca con algo, calcula la colision. Roblox usa su "
            "propio motor de fisica integrado."
        ),
        "para_ninos": (
            "Cuando saltas en un videojuego y caes, no es magia: hay un "
            "MOTOR DE FISICA calculando la gravedad. Es un programa que "
            "simula las leyes de la fisica real. Gravedad, rebotes, "
            "choques: todo esta calculado con matematicas. Cuando algo "
            "rueda por una colina en Roblox, el motor de fisica esta "
            "calculando cada movimiento."
        ),
    },
    {
        "nombre": "Inteligencia artificial en juegos (NPC AI)",
        "campo": "Inteligencia artificial",
        "descripcion": (
            "Los NPCs (Non-Player Characters) usan algoritmos de IA para "
            "comportarse de forma inteligente. Las tecnicas incluyen maquinas "
            "de estados (patrullar, perseguir, atacar), arboles de "
            "comportamiento, y pathfinding (algoritmo A* para encontrar "
            "caminos). En juegos como los de la saga Halo, los enemigos "
            "trabajan en equipo, se cubren y flanquean al jugador."
        ),
        "para_ninos": (
            "Los personajes que no son jugadores (NPC) usan INTELIGENCIA "
            "ARTIFICIAL para actuar. Un guardia en un juego tiene reglas: "
            "'Si veo al jugador, perseguirlo. Si me disparan, cubrirme.' "
            "Hay un algoritmo famoso llamado A* (A estrella) que les "
            "ensena a encontrar el camino mas corto. Por eso los enemigos "
            "siempre saben donde estas."
        ),
    },
    {
        "nombre": "Diseno de sonido en videojuegos",
        "campo": "Audio digital",
        "descripcion": (
            "El sonido en los juegos se crea combinando grabaciones reales, "
            "sintesis digital y musica compuesta especificamente. Los "
            "primeros juegos usaban 'chiptunes': musica generada directamente "
            "por el chip de sonido. El tema de Super Mario Bros. (compuesto "
            "por Koji Kondo) es una de las melodias mas reconocibles del "
            "mundo. Los juegos modernos usan audio espacial 3D para que "
            "puedas oir de que direccion vienen los sonidos."
        ),
        "para_ninos": (
            "La musica de los videojuegos viejos la hacia directamente "
            "el chip de la consola, por eso sonaba 'electronica'. Se llaman "
            "CHIPTUNES. La melodia de Mario la compuso Koji Kondo y es una "
            "de las mas famosas del mundo. Hoy los juegos usan sonido 3D: "
            "si un enemigo esta a tu izquierda, lo escuchas por la "
            "izquierda. Tu cerebro siente que esta AHI."
        ),
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HITOS_GAMING — Momentos que cambiaron la historia del gaming
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HITOS_GAMING = [
    {
        "titulo": "Tetris escapa de la Union Sovietica",
        "relato": (
            "En 1984, el programador ruso Alexey Pajitnov creo Tetris en un "
            "centro de investigacion de la Academia de Ciencias de Moscu. "
            "El juego se propago por toda la Union Sovietica de computadora "
            "en computadora. La batalla por los derechos internacionales fue "
            "epica: varias empresas pelearon por ellos mientras el gobierno "
            "sovietico reclamaba la propiedad. Nintendo finalmente consiguio "
            "los derechos para Game Boy. Tetris ayudo a vender mas de 118 "
            "millones de Game Boys. Pajitnov no recibio regalias hasta 1996, "
            "cuando fundo The Tetris Company."
        ),
        "para_ninos": (
            "Tetris fue creado en RUSIA en 1984 por Alexey Pajitnov. El juego "
            "era tan divertido que se copiaba de computadora en computadora "
            "como un virus. Pero como Rusia era comunista, el gobierno decia "
            "que el juego era SUYO, no de Alexey. Hubo una pelea mundial por "
            "los derechos hasta que Nintendo los consiguio para Game Boy. "
            "Tetris ayudo a vender mas de 118 millones de Game Boys. Alexey "
            "no gano dinero por su juego hasta 12 anhos despues."
        ),
    },
    {
        "titulo": "El crash de los videojuegos de 1983",
        "relato": (
            "Entre 1983 y 1985, la industria de videojuegos en EE.UU. colapso. "
            "Los ingresos cayeron de 3,200 millones de dolares en 1983 a 100 "
            "millones en 1985 (una caida del 97%). La causa principal fue la "
            "inundacion del mercado con juegos de pesima calidad. El simbolo "
            "del crash fue el juego de E.T. para Atari 2600, tan malo que "
            "millones de cartuchos fueron enterrados en un vertedero de "
            "Nuevo Mexico. La industria fue rescatada por Nintendo con el NES "
            "en 1985, que implemento un sello de calidad para evitar juegos "
            "basura."
        ),
        "para_ninos": (
            "En 1983, los videojuegos casi DESAPARECEN. Habia tantos juegos "
            "MALOS que la gente dejo de comprarlos. El peor de todos fue el "
            "juego de E.T., tan terrible que enterraron millones de copias "
            "en el desierto. La industria perdio casi todo su dinero. Pero "
            "entonces llego Nintendo con el NES y dijo: 'Solo se venderan "
            "juegos BUENOS.' Y salvo los videojuegos para siempre."
        ),
    },
    {
        "titulo": "Los eventos en vivo de Fortnite cambian el entretenimiento",
        "relato": (
            "En febrero de 2019, Fortnite realizo un concierto virtual del "
            "DJ Marshmello al que asistieron 10.7 millones de jugadores "
            "simultaneos dentro del juego. En abril de 2020, Travis Scott "
            "realizo su evento 'Astronomical' con 12.3 millones de jugadores "
            "simultaneos. Estos eventos demostraron que los videojuegos no "
            "son solo para jugar: pueden ser espacios sociales, salas de "
            "conciertos y plataformas de entretenimiento."
        ),
        "para_ninos": (
            "Fortnite hizo algo que nunca se habia visto: un CONCIERTO "
            "DENTRO de un videojuego. En 2020, el rapero Travis Scott dio "
            "un show dentro de Fortnite y asistieron 12 MILLONES de personas "
            "al mismo tiempo, sin moverse de su casa. Fue como ir a un "
            "concierto gigante pero dentro del juego. Eso demostro que los "
            "videojuegos son mucho mas que solo jugar."
        ),
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VOCABULARIO_GAMER — Terminos tecnicos explicados para ninos
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VOCABULARIO_GAMER = [
    {
        "palabra": "FPS (Frames Per Second)",
        "significado": "Cuadros por segundo. Es cuantas imagenes dibuja tu pantalla cada segundo.",
        "uso": "Si un juego corre a 60 FPS, la pantalla dibuja 60 imagenes por segundo, y se ve suave.",
    },
    {
        "palabra": "NPC (Non-Player Character)",
        "significado": "Personaje No Jugador. Cualquier personaje del juego controlado por la computadora.",
        "uso": "El vendedor de la tienda en un juego es un NPC, porque lo controla la maquina, no un jugador.",
    },
    {
        "palabra": "Respawn",
        "significado": "Reaparecer en el juego despues de ser eliminado.",
        "uso": "Cuando te eliminan en Roblox y vuelves a aparecer, eso es un respawn.",
    },
    {
        "palabra": "Hitbox",
        "significado": "Caja invisible alrededor de un personaje que detecta golpes y colisiones.",
        "uso": "A veces un disparo parece que le dio al enemigo pero fallo porque no toco la hitbox.",
    },
    {
        "palabra": "Sandbox",
        "significado": "Juego de mundo abierto donde puedes hacer lo que quieras sin un objetivo fijo.",
        "uso": "Minecraft y Roblox son juegos sandbox: tu decides que hacer, no hay un camino obligatorio.",
    },
    {
        "palabra": "Speedrun",
        "significado": "Completar un juego lo mas rapido posible, a veces usando trucos.",
        "uso": "Hay personas que terminan Mario 64 en menos de 7 minutos haciendo speedrun.",
    },
    {
        "palabra": "Easter egg",
        "significado": "Secreto escondido por los desarrolladores dentro de un juego.",
        "uso": "El nombre viene de la busqueda de huevos de Pascua. El primer Easter egg fue en el juego Adventure de Atari (1980).",
    },
    {
        "palabra": "Mod",
        "significado": "Modificacion hecha por jugadores que cambia o agrega cosas a un juego.",
        "uso": "En Minecraft hay mods que agregan dragones, mods de tecnologia, mods de magia y miles mas.",
    },
    {
        "palabra": "Nerf",
        "significado": "Cuando los desarrolladores hacen que algo sea menos poderoso en una actualizacion.",
        "uso": "Si un arma es demasiado fuerte, los desarrolladores la 'nerfean' para equilibrar el juego.",
    },
    {
        "palabra": "Buff",
        "significado": "Lo contrario de nerf: cuando los desarrolladores hacen algo mas poderoso.",
        "uso": "Si un personaje es muy debil y nadie lo usa, lo 'buffean' para que sea mas util.",
    },
    {
        "palabra": "DLC (Downloadable Content)",
        "significado": "Contenido descargable extra que se agrega a un juego despues de su lanzamiento.",
        "uso": "Muchos juegos venden DLC con nuevos niveles, personajes o historias.",
    },
    {
        "palabra": "Indie",
        "significado": "Juego creado por un equipo pequeno o una sola persona, sin una gran empresa detras.",
        "uso": "Minecraft empezo como un juego indie hecho por una sola persona. Otros famosos son Undertale, Celeste y Hollow Knight.",
    },
    {
        "palabra": "Open world",
        "significado": "Mundo abierto. Un juego donde puedes explorar libremente en cualquier direccion.",
        "uso": "Zelda: Breath of the Wild es un juego open world donde puedes ir a cualquier parte desde el inicio.",
    },
    {
        "palabra": "Roguelike",
        "significado": "Tipo de juego donde si mueres, pierdes todo y empiezas de cero con niveles generados al azar.",
        "uso": "Se llama asi por el juego 'Rogue' de 1980. Cada partida es diferente porque los niveles se generan aleatoriamente.",
    },
    {
        "palabra": "Lag",
        "significado": "Retraso o demora en un juego online causado por mala conexion.",
        "uso": "Cuando un personaje se teletransporta o se congela en un juego online, es por el lag.",
    },
    {
        "palabra": "Bug",
        "significado": "Error en el codigo del juego que causa comportamientos inesperados.",
        "uso": "El termino viene de 1947, cuando una polilla real causo una falla en una computadora Harvard Mark II.",
    },
    {
        "palabra": "Render",
        "significado": "El proceso de la computadora dibujando los graficos del juego en la pantalla.",
        "uso": "La tarjeta grafica (GPU) es la encargada de renderizar todo lo que ves en el juego.",
    },
    {
        "palabra": "Crafting",
        "significado": "Sistema de fabricacion donde combinas materiales para crear objetos.",
        "uso": "En Minecraft, juntas madera y palos para craftear una mesa de crafteo. Es el sistema central del juego.",
    },
    {
        "palabra": "PvP (Player vs Player)",
        "significado": "Modo de juego donde luchas contra otros jugadores reales, no contra la computadora.",
        "uso": "En Roblox hay muchos juegos PvP donde peleas contra otros jugadores de todo el mundo.",
    },
    {
        "palabra": "Spawn point",
        "significado": "El lugar exacto donde apareces o reapareces en un juego.",
        "uso": "En Minecraft, tu spawn point es donde apareciste por primera vez o donde esta tu cama.",
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNCIONES HELPER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_random_gaming_history() -> dict:
    """Retorna un hito historico del gaming aleatorio."""
    return random.choice(HISTORIA_GAMING)


def get_random_computing_concept() -> dict:
    """Retorna un concepto de computacion aleatorio."""
    return random.choice(CONCEPTOS_COMPUTACION)


def get_random_gaming_figure() -> dict:
    """Retorna una figura del gaming aleatoria."""
    return random.choice(FIGURAS_GAMING)


def get_random_game_science() -> dict:
    """Retorna un dato cientifico sobre juegos aleatorio."""
    return random.choice(CIENCIA_DETRAS_JUEGOS)


def get_random_gaming_milestone() -> dict:
    """Retorna un hito del gaming aleatorio."""
    return random.choice(HITOS_GAMING)


def get_random_gamer_word() -> dict:
    """Retorna una palabra del vocabulario gamer aleatoria."""
    return random.choice(VOCABULARIO_GAMER)


def build_gaming_knowledge_injection() -> str:
    """
    Construye una inyeccion de conocimiento gaming para el prompt.
    Mezcla diferentes tipos de contenido para variedad.
    """
    blocks = []

    # Elegir 1 pieza de conocimiento aleatorio
    source = random.choice([
        "historia", "computacion", "figura", "ciencia", "hito",
    ])

    if source == "historia":
        item = get_random_gaming_history()
        blocks.append(
            f"HISTORIA GAMING ({item['nombre']}, {item['periodo']}): "
            f"{item['para_ninos']} "
            f"Dato extra: {item['dato_extra']}"
        )
    elif source == "computacion":
        item = get_random_computing_concept()
        blocks.append(
            f"COMPUTACION — {item['nombre']} ({item['concepto']}): "
            f"{item['para_ninos']}"
        )
    elif source == "figura":
        item = get_random_gaming_figure()
        blocks.append(
            f"FIGURAS DEL GAMING — {item['nombre']}, {item['titulo']}: "
            f"{item['para_ninos']}"
        )
    elif source == "ciencia":
        item = get_random_game_science()
        blocks.append(
            f"CIENCIA DE JUEGOS — {item['nombre']} ({item['campo']}): "
            f"{item['para_ninos']}"
        )
    elif source == "hito":
        item = get_random_gaming_milestone()
        blocks.append(
            f"HITO GAMING — {item['titulo']}: {item['para_ninos']}"
        )

    # Bonus: 40% de chance de agregar una palabra gamer
    if random.random() < 0.4:
        word = get_random_gamer_word()
        blocks.append(
            f"PALABRA GAMER: '{word['palabra']}' = {word['significado']} "
            f"Ejemplo: {word['uso']}"
        )

    return "\n".join(blocks)
