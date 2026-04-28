#import "template.typ": *

#show: project.with(
  title: [Värmepump],
  authors: ("Filip Petrini", "Markus Bajlo"),
  date: datetime.today().display(),
  course: [Termodynamik *1FA517*],
)
= Introduktion

I den här laborationen undersöker vi effektiviteten hos en värmepump.

- Teoretisk bakgrund
- Experimentell uppställning
- Resultat och analys


Vi kommer särskilt fokusera på värmefaktorn ($epsilon$).


== Teori

En värmepump flyttar värme från en kall reservoar till en varm.

$ epsilon = Q_H / W $ <eq-cop>

Som vi ser i ekvation @eq-cop, beror effektiviteten på förhållandet mellan utvunnen värme och tillfört arbete.

== Metod

1. Mät temperaturer vid in- och utlopp.
2. Registrera effekten från kompressorn.
3. Beräkna flödeshastigheten.

== Resultat

Här kan vi presentera våra mätdata och grafer.
