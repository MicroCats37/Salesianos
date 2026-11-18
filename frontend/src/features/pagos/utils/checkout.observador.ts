/**
 * Detection of the moment the provider STOPS rendering the checkout form.
 *
 * The provider renders the checkout inside the container of the modal
 * (`#izipay-checkout`). When the popup closes, the provider releases what it
 * rendered and the container becomes empty. That is the only provider-agnostic
 * signal that the popup is gone: the SDK contract this application uses does
 * not expose a "closed" event.
 *
 * The observer is a SIGNAL, never a decision: it reports that the checkout is
 * no longer rendered and the caller decides what that means for its flow.
 */

/**
 * Watches the container of the checkout and reports when the provider stops
 * rendering the form.
 *
 * It only reports a CLOSE: the container must have had content (the provider
 * rendered the form) and must lose it. A container that was never rendered is
 * never reported, so a provider that manages its own overlay never produces a
 * false close.
 *
 * @returns the function that stops watching.
 */
export function observarCierreCheckout(
  contenedor: HTMLElement | null,
  alCerrar: () => void,
): () => void {
  if (!contenedor || typeof MutationObserver === "undefined") {
    return () => {};
  }

  let teniaContenido = contenedor.childElementCount > 0;

  const observer = new MutationObserver(() => {
    const tieneContenidoAhora = contenedor.childElementCount > 0;

    if (teniaContenido && !tieneContenidoAhora) {
      observer.disconnect();
      alCerrar();
      return;
    }

    teniaContenido = tieneContenidoAhora;
  });

  observer.observe(contenedor, { childList: true });

  return () => observer.disconnect();
}
