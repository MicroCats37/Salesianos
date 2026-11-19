import Link from "next/link";
import { BrandMark } from "@/components/brand/BrandMark";
import { ENLACES } from "@/lib/enlaces";
import { RUTAS } from "@/lib/routes";
import { FacebookIcon, InstagramIcon, TikTokIcon } from "./SocialIcons";

/**
 * SiteFooter - the public footer.
 *
 * It closes the page with the brand mark and the destinations that make sense
 * to a visitor. The social marks are the official brand icons (simple-icons)
 * and they inherit the color of the text around them.
 *
 * The band uses the INVERSE surface, so its text uses the inverse pair
 * (`--surface-inverse-foreground` / `--surface-inverse-muted`) and NEVER
 * `--background`: in the dark theme the page background is dark and the text
 * of the band disappeared with it.
 */
export function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-surface-inverse-foreground/15 bg-surface-inverse text-surface-inverse-foreground">
      <div className="mx-auto grid max-w-[1200px] gap-8 px-4 py-12 sm:px-6 md:grid-cols-3 lg:px-10">
        <div className="flex flex-col gap-4">
          <BrandMark size={30} wordmark="brand" />
          <p className="max-w-[42ch] text-sm text-surface-inverse-muted">
            Campeonato deportivo y fiesta de cierre del Colegio Salesiano. Una
            edición, muchas disciplinas, un mismo encuentro.
          </p>
        </div>

        <nav aria-label="Enlaces del pie" className="flex flex-col gap-3">
          <p className="text-eyebrow-brand text-accent">La edición</p>
          <ul className="flex flex-col gap-2 text-sm">
            <li>
              <Link
                href={RUTAS.publico.informacion}
                className="text-surface-inverse-muted transition-colors duration-(--motion-duration-fast) hover:text-surface-inverse-foreground"
              >
                Información y reglamentos
              </Link>
            </li>
            <li>
              <Link
                href={RUTAS.publico.pases}
                className="text-surface-inverse-muted transition-colors duration-(--motion-duration-fast) hover:text-surface-inverse-foreground"
              >
                Pases de fiesta
              </Link>
            </li>
            <li>
              <Link
                href={RUTAS.publico.tienda}
                className="text-surface-inverse-muted transition-colors duration-(--motion-duration-fast) hover:text-surface-inverse-foreground"
              >
                Tienda del evento
              </Link>
            </li>
            <li>
              <Link
                href={RUTAS.publico.recuperarCompra}
                className="text-surface-inverse-muted transition-colors duration-(--motion-duration-fast) hover:text-surface-inverse-foreground"
              >
                Recuperar mi compra
              </Link>
            </li>
          </ul>
        </nav>

        <div className="flex flex-col gap-3">
          <p className="text-eyebrow-brand text-accent">Síguenos</p>
          <ul className="flex items-center gap-2">
            {[
              { icon: FacebookIcon, label: "Facebook", href: ENLACES.facebook },
              {
                icon: InstagramIcon,
                label: "Instagram",
                href: ENLACES.instagram,
              },
              { icon: TikTokIcon, label: "TikTok", href: ENLACES.tiktok },
            ].map(({ icon: Icon, label, href }) => (
              <li key={label}>
                <a
                  href={href}
                  target="_blank"
                  rel="noreferrer noopener"
                  aria-label={label}
                  className="inline-flex size-11 items-center justify-center rounded-full border border-surface-inverse-foreground/25 text-surface-inverse-muted transition-colors duration-(--motion-duration-fast) hover:border-accent hover:text-accent"
                >
                  <Icon className="size-5" aria-hidden="true" />
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="border-t border-surface-inverse-foreground/15">
        <div className="mx-auto max-w-[1200px] px-4 py-6 text-xs text-surface-inverse-muted sm:px-6 lg:px-10">
          <p>
            © {new Date().getFullYear()} Colegio Salesiano. Todos los derechos
            reservados.
          </p>
        </div>
      </div>
    </footer>
  );
}
