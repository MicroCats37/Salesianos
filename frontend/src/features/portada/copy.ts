/**
 * Copy editorial de la portada principal.
 *
 * Contenido tomado del micrositio oficial ya publicado. Vive en un solo
 * módulo para que `/informacion` pueda consumir la misma voz y la web no se
 * contradiga.
 */

export const COPY = {
  hero: {
    topline: "EL REENCUENTRO QUE NOS MUEVE",
    edicion: "LIMA, PERÚ · EDICIÓN 2026",
    eyebrow: "21 DE NOVIEMBRE DE 2026",
    tituloLineas: ["UN FESTIVAL.", "TODA LA", "FAMILIA."],
    descripcion: ["Deporte que nos une.", "Diversión para compartir."],
    comunidad: [
      "Salesianos y María Auxiliadora.",
      "Todas las promociones. Todas las generaciones.",
    ],
    ctaPrimario: { label: "VIVE EL FESTIVAL", href: "#paquetes" },
    ctaSecundario: { label: "Mira quiénes vienen", href: "#promociones" },
    momentos: [
      {
        numero: "01",
        etiqueta: "COMPARTIR",
        titular: "Un día para estar juntos.",
        imagen: "/images/portada/familia.png",
        alt: "Familias compartiendo al aire libre, con juegos y un castillo inflable",
        href: "#familia",
        destacada: true,
      },
      {
        numero: "02",
        etiqueta: "ALENTAR",
        titular: "La pasión de siempre.",
        imagen: "/images/portada/futbol.png",
        alt: "Preparación de un balón de fútbol sobre el césped",
        href: "#campeonato",
        destacada: false,
      },
      {
        numero: "03",
        etiqueta: "DISFRUTAR",
        titular: "Sonrisas para todos.",
        imagen: "/images/portada/juegos.png",
        alt: "Patio de juegos infantiles al aire libre",
        href: "#familia",
        destacada: false,
      },
    ],
    pie: {
      lugar: "ASOCIACIÓN OKINAWENSE DEL PERÚ",
      lugarDetalle: "Ate, Lima · Bienvenida desde las 8:00 a. m.",
      promesa: "DEPORTE + FAMILIA + DIVERSIÓN",
      countdownAntes: "NOS VOLVEMOS A ENCONTRAR EN",
      countdownDurante: "HOY VIVIMOS EL FESTIVAL",
      countdownDespues: "GRACIAS POR SER PARTE",
    },
  },

  ribbon: [
    "DEPORTE",
    "FAMILIA",
    "DIVERSIÓN",
    "REENCONTRADO",
    "SALESIANOS FEST",
  ],

  experiencia: {
    eyebrow: "01 / LA EXPERIENCIA",
    titulo: ["UN DÍA.", "MIL FORMAS DE", "REENCONTRARNOS."],
    destacado: "REENCONTRARNOS.",
    copy: [
      "La misma pasión. Una nueva forma de vivirla.",
      "De la cancha a la mesa, y de la mesa a la pista. Reúne a tu promoción y disfruta el campeonato, la familia y la fiesta sin cambiar de lugar.",
    ],
    tarjetas: [
      {
        numero: "01",
        miniLabel: "PARTIDOS DESDE LAS 9:00 A. M.",
        titulo: ["LA PASIÓN", "NOS REÚNE."],
        descripcion: "El campeonato de tu promoción.",
        imagen: "/images/portada/futbol.png",
        alt: "Balón de fútbol sobre el césped",
        href: "#campeonato",
      },
      {
        numero: "02",
        miniLabel: "PARA GRANDES Y CHICOS",
        titulo: ["LA FAMILIA", "SE ENCUENTRA."],
        descripcion: "Hay un lugar para todos.",
        imagen: "/images/portada/campestre.png",
        alt: "Zona campestre y espacios familiares",
        href: "#familia",
      },
      {
        numero: "03",
        miniLabel: "6:00 P. M. — 3:00 A. M.",
        titulo: ["LA HISTORIA", "CONTINÚA."],
        descripcion: "DJ, orquesta y una gran noche.",
        imagen: "/images/portada/salon.png",
        alt: "Salón de eventos con escenario y mesas",
        href: "#fiesta",
      },
    ],
    pie: {
      frase: "UNA VEZ SALESIANOS, SALESIANOS PARA SIEMPRE.",
      accion: "Guarda la fecha",
    },
  },

  promociones: {
    eyebrow: "LA FAMILIA SIGUE CRECIENDO",
    titulo: ["ELLOS YA DIJERON", "¡PRESENTE!"],
    destacado: "¡PRESENTE!",
    copy: [
      "La próxima foto puede ser la de tu promoción.",
      "Estas siete promociones ya recibieron la bienvenida oficial al Salesianos FEST. Comparte el anuncio de tu promoción y haz que el reencuentro empiece desde hoy.",
    ],
    etiqueta: "PROMOCIÓN",
    estado: "CONFIRMADA",
    accionCompartir: "Compartir promoción",
    invitacion: {
      miniLabel: "FALTA TU PROMOCIÓN",
      titulo: ["LA HISTORIA", "SE COMPLETA", "CONTIGO."],
      descripcion: "Reúne a tu equipo y súmense al festival.",
      cta: "QUIERO PARTICIPAR",
    },
    pie: {
      aviso:
        "Participaciones anunciadas en Facebook · Revisión: 25 de octubre de 2026. Los anuncios de preinscripción se muestran por separado en el canal oficial.",
      enlace: "VER GALERÍA OFICIAL",
    },
    share: {
      eyebrow: "QUE TU PROMOCIÓN SE HAGA SENTIR",
      titulo: "COMPARTE LA PROMO {anio}.",
      posterEyebrow: "PUBLICACIÓN OFICIAL · FACEBOOK",
      posterTitulo: "PROMOCIÓN {anio}",
      etiqueta: "PUBLICACIÓN OFICIAL",
      destacado: "¡YA DIJIMOS PRESENTE!",
      fecha: "21 noviembre 2026",
      lugar: "Asociación Okinawense del Perú",
      verAnuncio: "Ver anuncio oficial de la promoción {anio}",
      altPoster:
        "Bienvenida oficial a la promoción {anio}, Salesianos FEST 2026",
      compartirAnuncio: "Compartir la publicación de la promoción {anio}",
      whatsapp: "WhatsApp",
      facebook: "Facebook",
      copiar: "Copiar enlace",
      mas: "Más aplicaciones",
      etiquetaEnlace: "Enlace de esta publicación",
      ayudaEnlace: "Mantén pulsado el enlace o selecciónalo para copiarlo.",
      copiado: "Enlace de la promoción {anio} copiado.",
      copiarManual: "Selecciona y copia el enlace para compartirlo.",
      errorCompartir:
        "El menú de compartir no está disponible. Elige WhatsApp, Facebook o copia el enlace.",
      explicacion:
        "Se compartirá el anuncio original de tu promoción. En WhatsApp se prepara un mensaje con el enlace; tú eliges dónde enviarlo.",
      verOriginal: "Ver publicación original",
      tituloNativo: "Promoción {anio} · Salesianos FEST 2026",
      mensaje:
        "¡La promoción {anio} ya dijo presente en Salesianos FEST! Nos vemos el 21 de noviembre de 2026 en la Asociación Okinawense del Perú, Ate, Lima. Deporte, familia y diversión. #SalesianosFEST #Promo{anio}",
    },
  },

  campeonato: {
    eyebrow: "02 / EL CAMPEONATO",
    titulo: ["LA CAMISETA", "SE VUELVE", "A SENTIR."],
    destacado: "SENTIR.",
    copy: "Los amigos de siempre. La emoción de competir otra vez. Fútbol 7, vóley mixto y básquet en una jornada para alentar, compartir y celebrar.",
    enlace: "Encuentra tu inscripción",
    fecha: { dia: "21", mes: "NOV / 2026" },
    perks: [
      "Árbitros profesionales",
      "Tribunas techadas",
      "Copas y premiación",
      "Transmisiones y entrevistas",
    ],
  },

  programa: {
    eyebrow: "21 NOVIEMBRE / ORGANIZA TU DÍA",
    titulo: ["DESDE EL PRIMER SALUDO", "HASTA EL ÚLTIMO BAILE."],
    destacado: "BAILE.",
    enlaceCronograma: "Cronograma oficial",
    hitos: [
      {
        hora: "08:00",
        meridiem: "A. M.",
        titulo: "Bienvenida",
        descripcion: "Nos reunimos con nuestra promoción.",
      },
      {
        hora: "08:30",
        meridiem: "A. M.",
        titulo: "Inauguración",
        descripcion: "La familia salesiana abre el festival.",
      },
      {
        hora: "09:00",
        meridiem: "A. M.",
        titulo: "¡A la cancha!",
        descripcion: "Inicio de partidos y jornada deportiva.",
      },
      {
        hora: "06:00",
        meridiem: "P. M.",
        titulo: "Deporte → fiesta",
        descripcion: "Finalizan los partidos. Empieza la celebración.",
      },
      {
        hora: "09:00",
        meridiem: "P. M.",
        titulo: "Premiación",
        descripcion: "Celebramos a los equipos durante la fiesta.",
      },
    ],
    notaPie: "La fiesta continúa hasta las 3:00 a. m. del domingo 22.",
    accionCalendario: "GUARDAR EN MI CALENDARIO",
    categorias: {
      titulo: "Categorías del campeonato",
      nota: "La organización puede reconfigurar las categorías para maximizar el número de partidos de cada promoción, según el cronograma publicado.",
    },
  },

  familia: {
    eyebrow: "03 / EN FAMILIA",
    titulo: ["EL MEJOR PLAN:", "ESTAR JUNTOS."],
    destacado: "ESTAR JUNTOS.",
    copy: "Ven con los tuyos. Entre partido y partido, hay tiempo para conversar, compartir algo rico y crear nuevos recuerdos.",
    items: [
      "Zona campestre y espacios para compartir",
      "Venta de alimentos y bebidas",
      "Juegos, gincanas y actividades familiares",
      "Patio de juegos para niños",
    ],
    nota: "Juegos infantiles sujetos a pago o disponibilidad, según el programa.",
    cita: "EL REENCUENTRO TAMBIÉN SE VIVE FUERA DE LA CANCHA.",
    imagen: "/images/portada/campestre.png",
    alt: "Zona campestre y espacios familiares al aire libre",
  },

  fiesta: {
    eyebrow: "04 / LA GRAN FIESTA",
    titulo: ["CAE LA NOCHE.", "SUBE LA EMOCIÓN."],
    destacado: "EMOCIÓN.",
    copy: [
      "Del campeonato a la fiesta. Sin cambiar de lugar.",
      "Nos encontramos en el salón de eventos de la AOP para seguir escribiendo nuestra historia.",
    ],
    inicio: { hora: "18:00", dia: "21 NOV" },
    fin: { hora: "03:00", dia: "22 NOV" },
    lineup: ["DJ", "ORQUESTA", "TU PROMOCIÓN"],
    features: [
      "Escenario, luces y sonido",
      "Barra de bebidas",
      "Boxes para promociones",
    ],
    ctaPrimario: { label: "ELIGE TU PACK CON FIESTA", href: "#paquetes" },
    ctaSecundario: {
      label: "Quiero ir solo a la fiesta",
      href: "#pase-fiesta",
    },
    nota: "Artistas y programación detallada por anunciar. Imagen de la propuesta del festival.",
  },

  paquetes: {
    eyebrow: "05 / ELIGE CÓMO VIVIRLO",
    titulo: ["TU PROMOCIÓN.", "TU PLAN."],
    destacado: "TU PLAN.",
    copy: [
      "Compite, celebra o hazlo todo.",
      "Compara lo que incluye cada opción y continúa tu inscripción en la plataforma del festival.",
    ],
    tabs: [
      { id: "packs", label: "Campeonato + fiesta" },
      { id: "sports", label: "Solo campeonato" },
    ],
    disclaimer:
      "Precios según las publicaciones oficiales. Confirma disponibilidad y condiciones con la organización antes de pagar.",
    enlaceCuenta: "Ya tengo una cuenta",
    calendario: [
      {
        numero: "01",
        titulo: "Preventa",
        descripcion: "Hasta el 25 de octubre",
        cierre: "Cierre: 8:00 p. m.",
      },
      {
        numero: "02",
        titulo: "Regular",
        descripcion: "26 de octubre al 8 de noviembre",
        cierre: "Cierre: 8:00 p. m.",
      },
      {
        numero: "03",
        titulo: "Extemporánea",
        descripcion: "9 al 18 de noviembre",
        cierre: "Cierre: 8:00 p. m.",
      },
      {
        numero: "04",
        titulo: "El torneo toma forma",
        descripcion: "Sorteo: 19 nov · 6:00 p. m.",
        cierre: "Fixture: 20 nov · 10:00 p. m.",
      },
    ],
  },

  paseFiesta: {
    id: "pase-fiesta",
    miniLabel: "TAMBIÉN PUEDES VENIR SOLO A LA FIESTA",
    titulo: ["TU PASE PARA", "REENCONTRARNOS."],
    copy: "DJ, orquesta y tus amigos de siempre.",
    precioPreventa: 25,
    precioPuerta: 35,
    cta: "VER PASE A LA FIESTA",
    enlaceAnuncio: "Ver anuncio oficial",
  },

  pasosInscripcion: {
    titulo: ["REÚNE A TU PROMOCIÓN.", "NOS VEMOS EN EL FEST."],
    pasos: [
      { numero: "01", texto: "Elige tu disciplina o paquete." },
      { numero: "02", texto: "Crea tu cuenta y registra tu equipo." },
      { numero: "03", texto: "Completa el proceso en la plataforma oficial." },
    ],
  },

  enVivo: {
    eyebrow: "06 / TRANSMISIÓN EN VIVO",
    titulo: ["LA DISTANCIA", "NO NOS", "SEPARA."],
    destacado: "SEPARA.",
    copy: "Sigue el campeonato, las entrevistas y los momentos del festival desde donde estés. La familia salesiana siempre encuentra la forma de estar cerca.",
    nota: "El enlace y los horarios de transmisión se anunciarán por los canales oficiales.",
    cta: "IR A LA TRANSMISIÓN",
    estado: "PRÓXIMAMENTE",
  },

  lugar: {
    eyebrow: "07 / NUESTRO PUNTO DE ENCUENTRO",
    titulo: ["UN LUGAR.", "TODA LA EXPERIENCIA."],
    destacado: "EXPERIENCIA.",
    cta: "CÓMO LLEGAR",
    horarios: [
      { etiqueta: "BIENVENIDA", valor: "8:00 a. m." },
      { etiqueta: "PARTIDOS", valor: "9:00 a. m." },
      { etiqueta: "FIESTA", valor: "6:00 p. m." },
    ],
    accionCalendario: "Agregar a mi calendario",
    comodidades: [
      {
        numero: "01",
        titulo: "Ven con tranquilidad",
        descripcion:
          "Seguridad permanente y ambulancia con paramédicos previstas en el programa.",
      },
      {
        numero: "02",
        titulo: "Llega y quédate",
        descripcion:
          "Amplio estacionamiento con tarifa plana durante todo el evento.",
      },
      {
        numero: "03",
        titulo: "Todo a tu alcance",
        descripcion:
          "Tribunas techadas, servicios higiénicos, duchas y camerinos.",
      },
    ],
  },

  auspiciadores: {
    eyebrow: "08 / AUSPICIADORES Y ALIADOS",
    titulo: ["GRANDES REENCUENTROS.", "GRANDES ALIADOS."],
    destacado: "ALIADOS.",
    copy: "Un espacio para las marcas que quieren acompañar a nuestra comunidad y ser parte de una celebración que une generaciones.",
    invitacion: {
      miniLabel: "SÉ PARTE DE SALESIANOS FEST",
      titulo: ["Tu marca también", "tiene un lugar aquí."],
      descripcion:
        "Los auspiciadores confirmados se anunciarán en este espacio.",
      cta: "QUIERO SER AUSPICIADOR",
    },
  },

  preguntas: {
    eyebrow: "ANTES DE VERNOS",
    titulo: ["TODO LO QUE", "QUIERES", "SABER."],
    destacado: "SABER.",
    faq: [
      {
        pregunta: "¿Quiénes pueden participar?",
        respuesta:
          "El festival convoca a las promociones de Salesianos y María Auxiliadora, junto a sus familias. Para participar en las competencias, revisa las bases y condiciones de inscripción en la plataforma oficial.",
      },
      {
        pregunta: "¿El campeonato y la fiesta son en el mismo lugar?",
        respuesta:
          "Sí. Las actividades deportivas, la zona familiar y la fiesta se desarrollan en el complejo de la Asociación Okinawense del Perú. La celebración nocturna es en su salón de eventos.",
      },
      {
        pregunta: "¿Qué incluyen los paquetes?",
        respuesta:
          "Los paquetes combinan inscripción deportiva y pases a la fiesta. Dúo y Trío incluyen acceso a un box exclusivo y una caja de cerveza, según el programa. Revisa el detalle de cada opción; la venta de bebidas alcohólicas es solo para mayores de edad.",
      },
      {
        pregunta: "¿Puedo asistir solo a la fiesta?",
        respuesta:
          "Sí. El anuncio oficial ofrece un pase individual: S/ 25 en preventa hasta el 25 de octubre y S/ 35 en puerta. Consulta la disponibilidad vigente con la organización.",
      },
      {
        pregunta: "¿Habrá actividades para niños?",
        respuesta:
          "Sí. La propuesta incluye espacios familiares, juegos y gincanas. El acceso al patio de juegos infantiles está sujeto a pago o disponibilidad.",
      },
      {
        pregunta: "¿Dónde podré ver la transmisión en vivo?",
        respuesta:
          "Desde el botón «En vivo» de la parte superior. El reproductor se habilitará cuando se anuncie el enlace oficial. Mientras tanto, puedes guardar la fecha y seguir las novedades del festival.",
      },
    ],
  },

  cierre: {
    fecha: "21 NOVIEMBRE 2026 · LIMA",
    titulo: ["LAS MEJORES HISTORIAS", "SE VIVEN JUNTOS."],
    destacado: "JUNTOS.",
    cta: "REÚNE A TU PROMOCIÓN",
    compartir: "Comparte el festival",
  },

  footer: {
    frase: ["Una historia que nos une.", "Una familia que permanece."],
    copyright: "© 2026 SALESIANOS FEST · LIMA, PERÚ",
    organiza: "Organiza: Promoción Salesianos 2002 · Bodas de Plata",
    inscripciones: "INSCRIPCIONES: 967 951 650",
  },

  barraMovil: {
    texto: "21 NOV · LIMA 2026",
    cta: "VER PAQUETES",
  },
} as const;
