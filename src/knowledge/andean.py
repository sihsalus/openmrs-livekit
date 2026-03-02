"""
Módulo de Conocimiento Andino para Nebu.

Base de datos de cosmovisión andina REAL, basada en fuentes académicas:
- Josef Estermann — "Filosofía Andina" (principios relacionales)
- Manuscrito de Huarochirí (siglo XVI) — mitología andina original
- Zenón Depaz Toledo — "La cosmo-visión andina en el Manuscrito de Huarochirí"
- Garcilaso de la Vega — "Comentarios Reales de los Incas"
- Guamán Poma de Ayala — "Nueva Corónica y Buen Gobierno"
- María Rostworowski — "Historia del Tahuantinsuyo"

Cada entrada tiene versión académica y versión `para_ninos`.
Nebu usa la versión para_ninos en sus interacciones.
"""

import random
from typing import Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🌍 LOS TRES PACHAS — Las dimensiones de la realidad andina
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRES_PACHAS = [
    {
        "nombre": "Hanan Pacha",
        "quechua": "Hanan Pacha",
        "significado": "El mundo de arriba",
        "descripcion": (
            "Dimensión celeste donde habitan Inti (Sol), Mama Quilla (Luna), "
            "las estrellas y las constelaciones. No es un 'cielo' como en la "
            "tradición cristiana — es el espacio de lo ordenado, lo luminoso "
            "y lo que ya alcanzó su forma plena."
        ),
        "para_ninos": (
            "¡Es el mundo de arriba! Ahí viven el Sol (Inti), la Luna "
            "(Mama Quilla) y todas las estrellas. Los incas miraban el cielo "
            "todas las noches y veían figuras que les contaban historias."
        ),
        "dato_extra": (
            "Los incas no solo veían constelaciones de estrellas brillantes "
            "como los griegos — también veían 'constelaciones oscuras' en las "
            "manchas de la Vía Láctea: la llama, el sapo, la serpiente."
        ),
    },
    {
        "nombre": "Kay Pacha",
        "quechua": "Kay Pacha",
        "significado": "Este mundo, el mundo de aquí",
        "descripcion": (
            "La dimensión presente, el mundo de los seres vivos: humanos, "
            "animales, plantas, ríos, montañas. Es el espacio del tinku "
            "(encuentro de fuerzas opuestas) y donde se practica el ayni "
            "(reciprocidad). Todo lo que está vivo participa en Kay Pacha."
        ),
        "para_ninos": (
            "¡Es el mundo donde vivimos tú y yo! Aquí están los animales, "
            "las plantas, los ríos, las montañas. Los incas creían que todo "
            "lo que está aquí está VIVO — hasta las piedras y los ríos."
        ),
        "dato_extra": (
            "En la cosmovisión andina, las montañas son seres vivos llamados "
            "Apus. Cada montaña tiene su propia personalidad y poder."
        ),
    },
    {
        "nombre": "Ukhu Pacha",
        "quechua": "Ukhu Pacha",
        "significado": "El mundo interior, de abajo",
        "descripcion": (
            "Dimensión interior de la tierra. NO es el infierno cristiano — "
            "esa es una lectura colonial. Es donde germinan las semillas, "
            "donde viven los ancestros, donde nacen las fuentes de agua. "
            "Es el origen, la potencia, lo que todavía no ha salido a la luz. "
            "Las paqarinas (lugares de origen) conectan Ukhu con Kay Pacha."
        ),
        "para_ninos": (
            "¡Es el mundo de ADENTRO de la tierra! Pero no es un lugar malo. "
            "Es donde nacen las plantas, donde duermen las semillas, y donde "
            "viven los ancestros. Es como la raíz de un árbol gigante que "
            "sostiene todo lo demás."
        ),
        "dato_extra": (
            "Los incas creían que las lagunas, cuevas y manantiales eran "
            "puertas entre Kay Pacha y Ukhu Pacha."
        ),
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔮 PRINCIPIOS ANDINOS — (Estermann, "Filosofía Andina")
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRINCIPIOS_ANDINOS = [
    {
        "nombre": "Relacionalidad",
        "quechua": "Tinkuy",
        "descripcion": (
            "Todo está conectado con todo. Nada existe aislado. "
            "El individuo solo tiene sentido dentro de su red de relaciones. "
            "Es el principio más fundamental de la filosofía andina."
        ),
        "para_ninos": (
            "¡En el mundo andino TODO está conectado! Las montañas con "
            "los ríos, los animales con las plantas, las personas con la tierra. "
            "Nada existe solito — todo es parte de una gran familia."
        ),
    },
    {
        "nombre": "Complementariedad (Yanantin)",
        "quechua": "Yanantin",
        "descripcion": (
            "Los opuestos no se combaten, se complementan. Hombre-mujer, "
            "arriba-abajo, sol-luna, izquierda-derecha. No hay uno sin el otro. "
            "El mundo andino no busca eliminar lo opuesto sino integrarlo."
        ),
        "para_ninos": (
            "Para los incas, las cosas opuestas no pelean, ¡se ayudan! "
            "El sol y la luna, el frío y el calor, el día y la noche. "
            "Como el yin y yang pero andino: se llama YANANTIN."
        ),
    },
    {
        "nombre": "Reciprocidad (Ayni)",
        "quechua": "Ayni",
        "descripcion": (
            "Toda acción merece una respuesta equivalente. Si la Pachamama "
            "da alimento, hay que devolverle con ofrendas. Si un vecino te "
            "ayuda a construir tu casa, tú lo ayudarás después. El ayni "
            "mantiene el equilibrio del cosmos."
        ),
        "para_ninos": (
            "AYNI es la regla de oro andina: si alguien te ayuda, ¡tú "
            "lo ayudas después! Los incas hacían esto con todo: con sus "
            "vecinos, con la tierra, hasta con las montañas. Si la tierra "
            "te da comida, tú le devuelves una ofrenda."
        ),
    },
    {
        "nombre": "Correspondencia",
        "quechua": "No tiene término quechua único",
        "descripcion": (
            "Lo que pasa arriba pasa abajo, lo de adentro refleja lo de "
            "afuera. Los tres Pachas se corresponden entre sí. Las "
            "constelaciones del cielo corresponden a los animales de la "
            "tierra. La organización social refleja la organización cósmica."
        ),
        "para_ninos": (
            "Lo que pasa en el cielo pasa en la tierra y lo que pasa "
            "afuera pasa adentro. Los incas veían una llama en las "
            "estrellas y decían: '¡Es la misma llama que cuida nuestros "
            "rebaños, pero en el cielo!'"
        ),
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚡ PANTEÓN ANDINO — Los dioses y seres poderosos
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PANTEON_ANDINO = [
    {
        "nombre": "Viracocha",
        "titulo": "El Creador",
        "descripcion": (
            "Deidad creadora que emergió del lago Titicaca. Ordenó el mundo, "
            "creó el sol, la luna y las estrellas. Según el Manuscrito de "
            "Huarochirí, Cuniraya Viracocha se disfrazaba de mendigo para "
            "probar a las personas."
        ),
        "para_ninos": (
            "¡Viracocha es el creador de TODO! Salió del lago Titicaca y "
            "creó el sol, la luna y las personas. A veces se disfrazaba "
            "de viejito pobre para ver quién era buena gente de verdad."
        ),
    },
    {
        "nombre": "Inti",
        "titulo": "El Sol, padre de los incas",
        "descripcion": (
            "Dios Sol, considerado padre de los incas. El Sapa Inca era "
            "su representante en la tierra. El Inti Raymi (fiesta del Sol) "
            "se celebra cada solsticio de invierno en Cusco desde hace "
            "más de 500 años."
        ),
        "para_ninos": (
            "¡INTI es el Sol! Para los incas, el Sol era su papá cósmico. "
            "El rey inca era el 'Hijo del Sol'. Cada año le hacían una "
            "fiesta gigante llamada Inti Raymi que todavía se celebra."
        ),
    },
    {
        "nombre": "Mama Quilla",
        "titulo": "La Luna, esposa de Inti",
        "descripcion": (
            "Diosa Luna, esposa y hermana de Inti. Protectora de las mujeres "
            "y reguladora del calendario agrícola. Los eclipses lunares "
            "significaban que un animal la estaba atacando, y toda la "
            "comunidad hacía ruido para espantarlo."
        ),
        "para_ninos": (
            "Mama Quilla es la Luna, esposa del Sol. Ella cuidaba a las "
            "mujeres y les decía a los agricultores cuándo sembrar. Cuando "
            "había eclipse, los incas creían que un puma la estaba mordiendo "
            "y gritaban para asustarlo. ¡Funcionaba, la luna siempre volvía!"
        ),
    },
    {
        "nombre": "Pachamama",
        "titulo": "La Madre Tierra",
        "descripcion": (
            "No es simplemente 'la naturaleza'. Es la fuerza vital que "
            "sostiene toda la vida. Es tiempo-espacio viviente. Se le hacen "
            "ofrendas (pagos) de coca, chicha y comida antes de sembrar, "
            "construir o emprender viajes. Todavía se practica en los Andes."
        ),
        "para_ninos": (
            "¡PACHAMAMA es la Mamá Tierra! Pero no solo el suelo — es TODO "
            "lo que está vivo. Los andinos todavía hoy le dan regalitos "
            "(hojitas de coca, chicha) para agradecerle. Es como darle "
            "un abrazo a la tierra."
        ),
    },
    {
        "nombre": "Pachacamac",
        "titulo": "El que anima la tierra",
        "descripcion": (
            "Dios cuyo nombre significa 'el que anima el mundo'. Su templo "
            "en Lima era tan sagrado que los sacerdotes entraban de espaldas. "
            "Nadie podía mirarlo directamente. Su poder hacía temblar la "
            "tierra (terremotos)."
        ),
        "para_ninos": (
            "Pachacamac era tan poderoso que nadie podía mirarlo. Su templo "
            "estaba en lo que hoy es Lima, y los sacerdotes entraban "
            "¡CAMINANDO DE ESPALDAS! Cuando se enojaba, temblaba la tierra."
        ),
    },
    {
        "nombre": "Illapa",
        "titulo": "El Rayo",
        "descripcion": (
            "Dios del rayo, trueno y relámpago. Controlaba las lluvias. "
            "Si un rayo caía cerca de alguien sin matarlo, esa persona "
            "era elegida para ser chamán (paqo). Los templos de Illapa "
            "estaban entre los más importantes del Cusco."
        ),
        "para_ninos": (
            "¡ILLAPA es el dios del RAYO! Controlaba la lluvia y las "
            "tormentas. Si un rayo caía cerca de ti sin hacerte daño, "
            "significaba que habías sido elegido para ser un chamán "
            "especial. ¡El rayo te escogía!"
        ),
    },
    {
        "nombre": "Mama Cocha",
        "titulo": "La Madre Mar",
        "descripcion": (
            "Diosa del mar y las aguas. Protectora de pescadores y "
            "marineros. La corriente de Humboldt era considerada su "
            "regalo — traía peces en abundancia a la costa peruana."
        ),
        "para_ninos": (
            "Mama Cocha es la mamá del mar. Ella cuidaba a los pescadores "
            "y les mandaba peces. La corriente fría del mar peruano que "
            "trae tantos peces era su regalo."
        ),
    },
    {
        "nombre": "Pariacaca",
        "titulo": "Dios de la lluvia y los huaycos",
        "descripcion": (
            "Según el Manuscrito de Huarochirí, nació de cinco huevos en "
            "la montaña Condorcoto. Venció al dios del fuego Huallallo "
            "Carhuincho con una tormenta épica. Es la deidad principal "
            "de la sierra de Lima."
        ),
        "para_ninos": (
            "¡Pariacaca nació de CINCO HUEVOS en la cima de una montaña! "
            "Se convirtió en cinco halcones que luego se transformaron en "
            "uno solo. Venció al dios del fuego con una tormenta GIGANTE. "
            "Es como la batalla más épica de la mitología andina."
        ),
    },
    {
        "nombre": "Los Apus",
        "titulo": "Espíritus de las montañas",
        "descripcion": (
            "Cada montaña es un ser vivo, un protector. Los Apus más "
            "poderosos (Ausangate, Salcantay, Huascarán) protegen regiones "
            "enteras. Los paqos (chamanes) se comunican con ellos para "
            "pedir consejo y protección."
        ),
        "para_ninos": (
            "¡Las montañas están VIVAS! Cada montaña tiene un espíritu "
            "protector llamado Apu. Las montañas más grandes protegen "
            "ciudades enteras. Los chamanes hablan con ellas para pedir "
            "consejo. ¡Imagina tener una montaña como guardián!"
        ),
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🤝 SISTEMAS SOCIALES ANDINOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SISTEMAS_SOCIALES = [
    {
        "nombre": "Ayni",
        "tipo": "Reciprocidad entre iguales",
        "descripcion": (
            "Trabajo recíproco entre familias. Hoy te ayudo a construir "
            "tu casa, mañana tú me ayudas con la mía. Es la base de la "
            "economía andina. No hay deuda monetaria — la deuda es social. "
            "Todavía se practica en comunidades rurales del Perú."
        ),
        "para_ninos": (
            "Si yo te ayudo hoy, tú me ayudas mañana. ¡Así de simple! "
            "Los incas no necesitaban dinero porque todos se ayudaban. "
            "Hasta hoy en los pueblitos del Perú la gente hace ayni."
        ),
    },
    {
        "nombre": "Minka",
        "tipo": "Trabajo comunal",
        "descripcion": (
            "Trabajo colectivo para el bien de toda la comunidad. "
            "Construir puentes, limpiar canales, hacer caminos. "
            "Todos participan y al final se celebra con chicha y comida."
        ),
        "para_ninos": (
            "La minka es cuando TODO el pueblo trabaja junto para algo "
            "que beneficia a todos: un puente, un camino, un canal de agua. "
            "Al final, ¡fiesta con comida y chicha para todos!"
        ),
    },
    {
        "nombre": "Ayllu",
        "tipo": "Unidad social básica",
        "descripcion": (
            "Familia extendida que comparte tierra, trabajo y ceremonias. "
            "No solo lazos de sangre — también lazos con la tierra "
            "(pacarina de origen) y con los ancestros. El ayllu es "
            "la célula del Tawantinsuyo."
        ),
        "para_ninos": (
            "El ayllu es como una familia GIGANTE. No solo papá, mamá "
            "y hermanos, sino todos los primos, tíos, abuelos, y hasta "
            "los ancestros. Todos comparten la tierra y se ayudan."
        ),
    },
    {
        "nombre": "Mita",
        "tipo": "Turnos de trabajo para el estado",
        "descripcion": (
            "Sistema de turnos de trabajo obligatorio para el Tawantinsuyo. "
            "Cada ayllu enviaba trabajadores por turnos para construir "
            "caminos, templos, depósitos. A cambio, el estado les daba "
            "comida, chicha y coca. Los españoles pervirtieron este sistema."
        ),
        "para_ninos": (
            "Cada pueblo se turnaba para trabajar en las obras del imperio: "
            "caminos, puentes, templos. Pero no era gratis — el Inca les "
            "daba comida y chicha. Era un trato justo, no esclavitud."
        ),
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧠 CONCEPTOS CLAVE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONCEPTOS_CLAVE = [
    {
        "nombre": "Pacha",
        "definicion": "No solo 'tierra' o 'mundo'. Es espacio-tiempo unido. "
                      "Pacha es simultáneamente lugar y momento.",
        "para_ninos": "Pacha no solo significa tierra — significa TODO: "
                      "el espacio, el tiempo, la realidad. ¡Una sola palabra "
                      "para decir 'todo lo que existe'!",
    },
    {
        "nombre": "Pachakuti",
        "definicion": "Inversión cósmica del tiempo-espacio. Un cambio de era. "
                      "Lo de arriba pasa abajo, lo oculto se revela. "
                      "La conquista española fue un pachakuti.",
        "para_ninos": "Es cuando el mundo se da vuelta. Todo cambia. Lo que "
                      "estaba arriba se va abajo y lo escondido sale a la luz. "
                      "¡Como un terremoto del tiempo!",
    },
    {
        "nombre": "Kamaq",
        "definicion": "Fuerza vital que anima las cosas. No es 'crear de la nada' "
                      "sino dar vida, poner en movimiento lo que ya existe.",
        "para_ninos": "Es la chispa que hace que las cosas estén VIVAS. "
                      "No crear algo nuevo, sino despertar lo que ya estaba ahí.",
    },
    {
        "nombre": "Huaca",
        "definicion": "Cualquier cosa sagrada: una piedra, un manantial, una "
                      "momia, un templo. Lo sagrado no está separado del mundo "
                      "— está dentro de él.",
        "para_ninos": "¡Una huaca es algo sagrado! Puede ser una piedra especial, "
                      "un río mágico, o un templo. Para los incas, lo sagrado "
                      "estaba por todos lados.",
    },
    {
        "nombre": "Paqarina",
        "definicion": "Lugar de origen de un pueblo: cueva, lago, montaña. "
                      "Cada ayllu tiene su paqarina de donde emergieron sus ancestros.",
        "para_ninos": "Cada pueblo tiene un lugar de donde nacieron sus abuelos "
                      "más antiguos. Puede ser una cueva, un lago o una montaña. "
                      "¡Es como el punto de respawn del pueblo!",
    },
    {
        "nombre": "Ceques",
        "definicion": "Líneas sagradas que salían del Coricancha (templo del Sol en Cusco) "
                      "hacia todas las direcciones. Eran 41 líneas con 328 huacas.",
        "para_ninos": "Desde el templo del Sol en Cusco salían 41 líneas invisibles "
                      "hacia todas las direcciones, con más de 300 lugares sagrados. "
                      "¡Era como un GPS sagrado!",
    },
    {
        "nombre": "Tinku",
        "definicion": "Encuentro ritual de fuerzas opuestas. Puede ser una danza, "
                      "una pelea ritual, o el punto donde se encuentran dos ríos.",
        "para_ninos": "Es cuando dos fuerzas opuestas se encuentran. A veces es "
                      "una pelea ritual, a veces una danza, a veces el punto "
                      "donde se juntan dos ríos. ¡Los opuestos se encuentran!",
    },
    {
        "nombre": "Chakana",
        "definicion": "La cruz andina. Representa la conexión entre los tres Pachas "
                      "y los cuatro suyos. Es el símbolo más importante de la "
                      "cosmovisión andina.",
        "para_ninos": "¡La cruz andina de cuatro escalones! Conecta el cielo, "
                      "la tierra y el mundo de abajo. Es como el mapa del "
                      "universo andino, y todavía la ves en artesanías por todo Perú.",
    },
    {
        "nombre": "Yanantin",
        "definicion": "Dualidad complementaria. Macho-hembra, sol-luna, "
                      "arriba-abajo. Los opuestos no pelean, se necesitan.",
        "para_ninos": "Los opuestos son amigos. Día y noche, sol y luna, "
                      "montaña y valle. Uno no puede existir sin el otro. "
                      "¡Son un equipo!",
    },
    {
        "nombre": "Kuychi",
        "definicion": "El arcoíris. Considerado una serpiente de dos cabezas que "
                      "conecta el cielo con la tierra. Era a la vez bello y temido.",
        "para_ninos": "¡El arcoíris era una serpiente mágica de dos cabezas! "
                      "Una cabeza bebía agua de un río y la otra la soltaba en "
                      "otro. Conectaba el cielo con la tierra.",
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔬 CIENCIA ANDINA — Logros verificables
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CIENCIA_ANDINA = [
    {
        "nombre": "Constelaciones oscuras",
        "campo": "Astronomía",
        "descripcion": (
            "Los incas no solo miraban estrellas brillantes. Observaban las "
            "manchas oscuras de la Vía Láctea y veían figuras: una llama "
            "(Yacana), un sapo (Hanp'atu), una serpiente (Machacuay), una "
            "perdiz (Yutu). Esto es único en la historia de la astronomía."
        ),
        "para_ninos": (
            "¡Los incas veían figuras donde otros no veían nada! En las "
            "manchas oscuras de la Vía Láctea encontraban una llama, un "
            "sapo, una serpiente. ¡Eran los únicos en el mundo que hacían eso!"
        ),
    },
    {
        "nombre": "Trepanaciones craneales",
        "campo": "Medicina",
        "descripcion": (
            "Cirugías de cráneo con 80-90% de tasa de supervivencia, "
            "evidenciada por regeneración ósea en los cráneos encontrados. "
            "Usaban cuchillos de obsidiana más afilados que el acero moderno."
        ),
        "para_ninos": (
            "Los incas hacían cirugías en la cabeza hace 600 años. ¡Y el "
            "80-90% de los pacientes SOBREVIVÍA! Usaban cuchillos de piedra "
            "volcánica más afilados que el acero."
        ),
    },
    {
        "nombre": "Moray: laboratorio agrícola",
        "campo": "Agricultura",
        "descripcion": (
            "Terrazas circulares concéntricas en Cusco que funcionaban como "
            "laboratorio agrícola. Cada nivel tiene un microclima diferente "
            "(hasta 15°C de diferencia entre el más alto y el más bajo). "
            "Allí experimentaban con cultivos de diferentes altitudes."
        ),
        "para_ninos": (
            "¡Los incas tenían un LABORATORIO de plantas! Moray es un hoyo "
            "gigante con escalones circulares donde cada nivel tiene diferente "
            "temperatura. Probaban qué plantas crecían mejor en cada nivel."
        ),
    },
    {
        "nombre": "Puquios de Nazca",
        "campo": "Ingeniería hidráulica",
        "descripcion": (
            "Sistema de acueductos subterráneos en Nazca que captan agua "
            "del subsuelo y la transportan a la superficie usando el "
            "principio de presión natural. Construidos hace más de 1500 años "
            "y TODAVÍA funcionan. NASA los estudió con satélite."
        ),
        "para_ninos": (
            "En el desierto de Nazca, donde casi no llueve, los nazcas "
            "construyeron túneles subterráneos que traen agua del fondo de "
            "la tierra. ¡Tienen más de 1500 años y TODAVÍA FUNCIONAN! "
            "Hasta la NASA los estudió."
        ),
    },
    {
        "nombre": "Quipus",
        "campo": "Computación y contabilidad",
        "descripcion": (
            "Sistema de cuerdas anudadas para registrar información numérica "
            "y posiblemente narrativa. Más de 600 quipus sobreviven. "
            "Algunos investigadores creen que eran un sistema de escritura "
            "tridimensional. Manejaron un imperio de 12 millones de personas."
        ),
        "para_ninos": (
            "Los incas no tenían papel ni computadora, ¡pero tenían QUIPUS! "
            "Cuerdas con nudos de colores que guardaban información. Con eso "
            "manejaban un imperio de 12 millones de personas. ¡Eran la "
            "computadora andina!"
        ),
    },
    {
        "nombre": "Liofilización: el chuño",
        "campo": "Tecnología alimentaria",
        "descripcion": (
            "Proceso de congelación-deshidratación de la papa inventado "
            "hace miles de años. Las papas se exponen al frío nocturno, "
            "se pisan para extraer agua, y se secan al sol. El resultado "
            "dura años sin refrigeración. La NASA usa el mismo principio."
        ),
        "para_ninos": (
            "¡Los incas inventaron la comida espacial! Congelaban papas de "
            "noche, las pisaban de día para sacarles el agua, y quedaban "
            "secas para siempre. Se llama CHUÑO y dura años. La NASA usa "
            "la misma técnica para la comida de astronautas."
        ),
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📜 MANUSCRITO DE HUAROCHIRÍ — Mitos reales
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MANUSCRITO_HUAROCHIRI = [
    {
        "titulo": "El nacimiento de Pariacaca",
        "relato": (
            "En la montaña Condorcoto aparecieron cinco huevos. De ellos "
            "nacieron cinco halcones que se transformaron en cinco hombres "
            "que luego se unieron en uno: Pariacaca, dios de la lluvia. "
            "Su primera acción fue una tormenta que inundó el mundo."
        ),
        "para_ninos": (
            "¡CINCO HUEVOS mágicos aparecieron en la cima de una montaña! "
            "De cada huevo salió un halcón, y los cinco halcones se unieron "
            "en un solo dios superpoderoso: Pariacaca. Su primer poder fue "
            "crear la tormenta más grande del mundo."
        ),
    },
    {
        "titulo": "Cuniraya Viracocha el mendigo",
        "relato": (
            "Cuniraya Viracocha se disfrazó de mendigo harapiento para "
            "recorrer la tierra. Los campos que tocaba florecían "
            "instantáneamente. Una mujer hermosa llamada Cavillaca se "
            "negó a hablarle por su apariencia, sin saber que era un dios. "
            "Él la persiguió hasta el mar donde ella se convirtió en piedra."
        ),
        "para_ninos": (
            "Un dios se disfrazó de viejito pobre para ver quién era buena "
            "gente. Todo lo que tocaba florecía. Pero nadie le hacía caso "
            "porque estaba vestido con harapos. ¡Moraleja: nunca juzgues "
            "a alguien por cómo se ve!"
        ),
    },
    {
        "titulo": "La batalla del agua contra el fuego",
        "relato": (
            "Pariacaca (agua) luchó contra Huallallo Carhuincho (fuego) "
            "por el control de la sierra. Pariacaca envió lluvias y "
            "granizo; Huallallo respondió con fuego desde su montaña. "
            "Pariacaca ganó y Huallallo huyó a la selva. Por eso en la "
            "sierra llueve y en la selva hace calor."
        ),
        "para_ninos": (
            "¡La pelea más épica de la historia andina! El dios del AGUA "
            "contra el dios del FUEGO. Llovía contra llamaradas. Granizo "
            "contra lava. ¡El agua ganó! Por eso en la sierra llueve mucho "
            "y en la selva hace calor — el dios del fuego huyó para allá."
        ),
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🗣️ VOCABULARIO QUECHUA PARA NEBU
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VOCABULARIO_NEBU = [
    {"palabra": "Allillanchu", "significado": "¿Cómo estás?", "uso": "saludo"},
    {"palabra": "Allinmi", "significado": "Estoy bien", "uso": "respuesta"},
    {"palabra": "Ñuqa", "significado": "Yo", "uso": "pronombre"},
    {"palabra": "Qam", "significado": "Tú", "uso": "pronombre"},
    {"palabra": "Sumaq", "significado": "Hermoso/bonito", "uso": "adjetivo"},
    {"palabra": "Munay", "significado": "Amor/querer", "uso": "sentimiento"},
    {"palabra": "Yachay", "significado": "Saber/conocimiento", "uso": "concepto"},
    {"palabra": "Llank'ay", "significado": "Trabajar", "uso": "acción"},
    {"palabra": "Ama suwa", "significado": "No robes", "uso": "ley inca"},
    {"palabra": "Ama llulla", "significado": "No mientas", "uso": "ley inca"},
    {"palabra": "Ama quella", "significado": "No seas perezoso", "uso": "ley inca"},
    {"palabra": "Tinkuy", "significado": "Encuentro", "uso": "concepto"},
    {"palabra": "Wawa", "significado": "Niño/bebé", "uso": "sustantivo"},
    {"palabra": "Runa", "significado": "Persona/ser humano", "uso": "sustantivo"},
    {"palabra": "Kawsay", "significado": "Vida/vivir", "uso": "concepto"},
    {"palabra": "Ñan", "significado": "Camino", "uso": "sustantivo"},
    {"palabra": "Mayu", "significado": "Río", "uso": "sustantivo"},
    {"palabra": "Urqu", "significado": "Montaña/cerro", "uso": "sustantivo"},
    {"palabra": "Qucha", "significado": "Lago/laguna", "uso": "sustantivo"},
    {"palabra": "Wayra", "significado": "Viento", "uso": "sustantivo"},
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛠️ FUNCIONES HELPER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_random_pacha_wisdom() -> dict:
    """Retorna un Pacha aleatorio con su para_ninos."""
    return random.choice(TRES_PACHAS)


def get_random_principle() -> dict:
    """Retorna un principio andino aleatorio."""
    return random.choice(PRINCIPIOS_ANDINOS)


def get_random_deity() -> dict:
    """Retorna una deidad aleatoria del panteón."""
    return random.choice(PANTEON_ANDINO)


def get_random_science() -> dict:
    """Retorna un logro científico andino aleatorio."""
    return random.choice(CIENCIA_ANDINA)


def get_random_social_system() -> dict:
    """Retorna un sistema social aleatorio."""
    return random.choice(SISTEMAS_SOCIALES)


def get_huarochiri_myth() -> dict:
    """Retorna un mito del Manuscrito de Huarochirí."""
    return random.choice(MANUSCRITO_HUAROCHIRI)


def get_quechua_word() -> dict:
    """Retorna una palabra quechua aleatoria."""
    return random.choice(VOCABULARIO_NEBU)


def build_andean_knowledge_injection() -> str:
    """
    Construye una inyección de conocimiento andino para el prompt.
    Mezcla diferentes tipos de contenido para variedad.
    """
    blocks = []

    # Elegir 1-2 piezas de conocimiento aleatorio
    source = random.choice([
        "pacha", "principio", "deidad", "ciencia", "mito", "concepto",
    ])

    if source == "pacha":
        pacha = get_random_pacha_wisdom()
        blocks.append(
            f"CONOCIMIENTO ANDINO ({pacha['nombre']}): "
            f"{pacha['para_ninos']} "
            f"Dato extra: {pacha['dato_extra']}"
        )
    elif source == "principio":
        princ = get_random_principle()
        blocks.append(
            f"SABIDURÍA ANDINA — {princ['nombre']} ({princ['quechua']}): "
            f"{princ['para_ninos']}"
        )
    elif source == "deidad":
        deity = get_random_deity()
        blocks.append(
            f"PANTEÓN ANDINO — {deity['nombre']}, {deity['titulo']}: "
            f"{deity['para_ninos']}"
        )
    elif source == "ciencia":
        sci = get_random_science()
        blocks.append(
            f"CIENCIA INCA — {sci['nombre']} ({sci['campo']}): "
            f"{sci['para_ninos']}"
        )
    elif source == "mito":
        myth = get_huarochiri_myth()
        blocks.append(
            f"MITO ANDINO — {myth['titulo']}: {myth['para_ninos']}"
        )
    elif source == "concepto":
        concept = random.choice(CONCEPTOS_CLAVE)
        blocks.append(
            f"PALABRA ANDINA — {concept['nombre']}: {concept['para_ninos']}"
        )

    # Bonus: 40% de chance de agregar una palabra quechua
    if random.random() < 0.4:
        word = get_quechua_word()
        blocks.append(
            f"PALABRA QUECHUA: '{word['palabra']}' = {word['significado']}. "
            f"¡Enséñasela al niño si encaja!"
        )

    return "\n".join(blocks)
