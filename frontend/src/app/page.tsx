import { EventBlock } from "@/components/event/EventBlock";
import { EventFooter } from "@/components/event/EventFooter";
import { FestivalBanner } from "@/components/event/FestivalBanner";

export const metadata = {
  title: "El Festival · Salesianos FEST 2026",
  description:
    "Por que un festival, familia y convivencia, infraestructura, comodidad para todos y la fiesta que continua cuando cae la noche.",
};

export default function EventPage() {
  return (
    <main className="w-full">
      <FestivalBanner />

      <EventBlock
        id="por-que"
        eyebrow="Por que un Festival"
        headline={
          <>
            Un festival en un{" "}
            <span className="text-[#1557b8]">solo lugar</span>
          </>
        }
        pill="Deporte · Familia · Diversion · Musica"
        paragraph="Reunimos el campeonato deportivo y la fiesta en una sola jornada para que nadie tenga que elegir entre competir y celebrar."
        bullets={[
          { icon: "deporte", title: "Campeonato deportivo", description: "Futbol 7, voley y basquet en paralelo." },
          { icon: "familia", title: "Actividades y juegos para la familia", description: "Espacios para grandes y chicos." },
          { icon: "carrusel", title: "Patio de juegos para ninos", description: "Zona segura con juegos inflables." },
          { icon: "comida", title: "Propuesta gastronomica", description: "Food trucks y menu festival todo el dia." },
        ]}
        images={[
          { src: "/images/fulbito-varones.webp", alt: "Futbol 7" },
          { src: "/images/voley-mixto.webp", alt: "Voley" },
          { src: "/images/basket-varones.webp", alt: "Basquet" },
        ]}
        chips={["Deporte", "Familia", "Musica", "Diversion"]}
        ribbon="Del campeonato a la fiesta · Sin cambiar de lugar"
      />

      <EventBlock
        id="familia"
        eyebrow="Familia y Convivencia"
        flipped
        headline={
          <>
            Un festival para{" "}
            <span className="text-[#ec4899]">disfrutar en familia</span>
          </>
        }
        pill="Mientras la promocion compite, la familia disfruta"
        paragraph="El festival tambien esta pensado para quienes vienen a compartir y pasar un buen dia."
        bullets={[
          { icon: "carrusel", title: "Zona campestre", description: "Para comer, beber, conversar y realizar actividades." },
          { icon: "comida", title: "Venta de alimentos y bebidas", description: "Food trucks, heladeria y barra." },
          { icon: "fiesta", title: "Juegos y competencias familiares", description: "Premios y sorpresas para todos." },
          { icon: "familia", title: "Zona de juegos para ninos", description: "Castillos inflables y actividades guiadas." },
        ]}
        images={[
          { src: "/images/voley-mixto.webp", alt: "Convivencia" },
          { src: "/images/fulbito-varones.webp", alt: "Familia" },
          { src: "/images/basket-varones.webp", alt: "Familia 2" },
        ]}
        chips={["Convivencia", "Ninos", "Gastronomia", "Familia"]}
        ribbon="Porque el reencuentro tambien se vive fuera de la cancha"
      />

      <EventBlock
        id="infraestructura"
        eyebrow="Infraestructura"
        headline={
          <>
            Todo lo que necesitamos para{" "}
            <span className="text-[#1557b8]">competir</span>
          </>
        }
        pill="Un complejo deportivo a la altura del festival"
        paragraph="Contamos con la infraestructura para desarrollar simultaneamente las diferentes competencias."
        bullets={[
          { icon: "cancha", title: "4 canchas de futbol 7", description: "Grass sintetico de ultima generacion." },
          { icon: "cancha", title: "2 canchas de voley", description: "Con red reglamentaria y demarcacion oficial." },
          { icon: "cancha", title: "1 cancha de basquet", description: "Techada y al aire libre." },
          { icon: "bano", title: "Banos, duchas y camerinos equipados", description: "Para deportistas y asistentes." },
          { icon: "palco", title: "Tribunas techadas", description: "Para disfrutar las competencias con comodidad." },
        ]}
        images={[
          { src: "/images/fulbito-varones.webp", alt: "Canchas" },
          { src: "/images/basket-varones.webp", alt: "Basquet" },
          { src: "/images/voley-mixto.webp", alt: "Voley" },
        ]}
        chips={["Futbol 7", "Voley", "Basquet", "Camerinos"]}
        ribbon="Mas canchas · Mas partidos · Mas emocion"
      />

      <EventBlock
        id="noche"
        eyebrow="Y cuando caiga la noche"
        flipped
        headline={
          <>
            La fiesta{" "}
            <span className="text-[#22d3ee]">continua en el mismo lugar</span>
          </>
        }
        pill="Nos trasladamos al salon de eventos del complejo"
        paragraph="Cuando termina el campeonato, el salon ya esta listo para la fiesta. Sin buses, sin traslados, sin perderse nada."
        bullets={[
          { icon: "familia", title: "Capacidad para mas de 400 personas", description: "Salon principal climatizado." },
          { icon: "comida", title: "Barra de bebidas", description: "Cocteleria y barra abierta." },
          { icon: "musica", title: "DJ + Orquesta", description: "Show en vivo y musica para todos." },
          { icon: "escenario", title: "Escenario, luces y sonido", description: "Produccion profesional." },
        ]}
        images={[
          { src: "/images/basket-varones.webp", alt: "Salon" },
          { src: "/images/fulbito-varones.webp", alt: "Noche" },
          { src: "/images/voley-mixto.webp", alt: "Fiesta" },
        ]}
        chips={["Noche", "Musica", "Salon", "Fiesta"]}
        ribbon="Del campeonato a la fiesta · Sin cambiar de lugar"
      />

      <EventBlock
        id="comodidad"
        eyebrow="Comodidad para todos"
        headline={
          <>
            Todo pensado para que solo te preocupes por{" "}
            <span className="text-[#1557b8]">disfrutar</span>
          </>
        }
        pill="Llega, estaciona, disfruta y quedate hasta el final"
        paragraph="La logistica del festival esta cubierta para que asistas tranquilo desde temprano y hasta el cierre."
        bullets={[
          { icon: "parking", title: "Amplio estacionamiento", description: "Tarifa plana durante todo el evento." },
          { icon: "puerta", title: "Servicios higienicos amplios y equipados", description: "Con mantenimiento continuo." },
          { icon: "bano", title: "Duchas y camerinos", description: "Para deportistas y asistentes." },
          { icon: "palco", title: "Tribunas techadas", description: "Para ver todas las competencias." },
          { icon: "escudo", title: "Seguridad permanente", description: "Equipo de seguridad en todo momento." },
          { icon: "familia", title: "Ambulancia durante el evento", description: "Atencion medica disponible." },
        ]}
        images={[
          { src: "/images/voley-mixto.webp", alt: "Estacionamiento" },
          { src: "/images/basket-varones.webp", alt: "Tribunas" },
          { src: "/images/fulbito-varones.webp", alt: "Servicios" },
        ]}
        chips={["Estacionamiento", "Seguridad", "Servicios", "Salud"]}
        ribbon="Llega, estaciona, disfruta y quedate hasta el final"
      />

      <EventFooter />
    </main>
  );
}
