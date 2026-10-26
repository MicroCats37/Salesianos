/* Share the original public Facebook announcement for each promotion. */
window.FestSharing = {
 data(promotion) {
  return {
   title: `Promoción ${promotion.year} · Salesianos FEST 2026`,
   text: `¡La promoción ${promotion.year} ya dijo presente en Salesianos FEST! Nos vemos el 21 de noviembre de 2026 en la Asociación Okinawense del Perú, Ate, Lima. Deporte, familia y diversión. #SalesianosFEST #Promo${promotion.year}`,
   url: promotion.source
  };
 },
 links(promotion) {
  const data=this.data(promotion);
  return {
   whatsapp: `https://wa.me/?text=${encodeURIComponent(`${data.text}\n${data.url}`)}`,
   facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(data.url)}`
  };
 }
};
