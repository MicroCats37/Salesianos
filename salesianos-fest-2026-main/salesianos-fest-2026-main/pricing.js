/* Public sales windows, in Lima time, from the official event schedule. */
window.FestPricing = {
 state(now=Date.now()) {
  const c=window.FEST_CONFIG;
  if(now<new Date(c.presaleEnd).getTime())return {key:'presale',label:'PREVENTA · HASTA EL 25 OCT, 8 P. M.',note:'Preventa hasta el 25 de octubre a las 8:00 p. m. (hora de Lima).'};
  if(now<new Date(c.regularStart).getTime())return {key:'gap',label:'PREVENTA FINALIZADA',note:'La inscripción regular comienza el 26 de octubre. Consulta con la organización.'};
  if(now<new Date(c.regularEnd).getTime())return {key:'regular',label:'TARIFA REGULAR · HASTA EL 8 NOV, 8 P. M.',note:'Inscripción regular del 26 de octubre al 8 de noviembre; cierre a las 8:00 p. m. (hora de Lima).'};
  if(now<new Date(c.lateStart).getTime())return {key:'gap',label:'ETAPA REGULAR FINALIZADA',note:'La inscripción extemporánea comienza el 9 de noviembre. Consulta su tarifa con la organización.'};
  if(now<new Date(c.registrationEnd).getTime())return {key:'late',label:'INSCRIPCIÓN EXTEMPORÁNEA',note:'Del 9 al 18 de noviembre, hasta las 8:00 p. m. La tarifa extemporánea debe confirmarse con la organización.'};
  return {key:'closed',label:'INSCRIPCIONES FINALIZADAS',note:'El cronograma publicado cerró las inscripciones el 18 de noviembre a las 8:00 p. m. Contacta a la organización para cualquier consulta.'};
 },
 amount(ticket,now=Date.now()) {const stage=this.state(now).key;return stage==='presale'?ticket.price:stage==='regular'?ticket.regular:null;}
};
