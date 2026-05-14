#import "template.typ": *

#show: project.with(
  title: [Värmepump],
  authors: ("Filip Petrini", "Markus Bajlo"),
  date: datetime.today().display(),
  course: [Termodynamik *1FA517*],
)

= Introduktion

- Undersökning av värmepumpens effektivitet.
- Fokus på värmeöverföring mellan slutna behållare.
- Experiment utan vattenflöde ($dot m = 0$).
- Mål: $C O P$ som funktion av $Delta T$.

== Teori

Beräkning av värmeeffekt:
$ dot(Q)_H = m_H c_p dot(T)_H quad #text("och") quad dot(Q)_C = -m_C c_p dot(T)_C $

Värmefaktor ($C O P$):
$ C O P_H = dot(Q)_H / P_text("el") quad #text("och") quad C O P_C = dot(Q)_C / P_text("el") $

== Metod

- Slutet system: Ingen extern tillförsel av vatten.
- Mätstorheter: $T_H(t), T_C(t)$ och $P(t)$.
- $P(t)$ extraherat via OCR från video.
- Stationära massor: $m_H$ och $m_C$.

== Hypotes

$ C O P prop 1 / (Delta T) $

- Ideal värmepump: $C O P_(h,"ideal") = T_H / (T_H - T_C)$.
- Realistiskt system: Ökade förluster vid högre tryck/temperatur-differens.

== Felanalys

Kvadratisk felutbredning:
$ ( (delta C O P) / (C O P) )^2 = ( (delta m) / m )^2 + ( (delta dot(T)) / dot(T) )^2 + ( (delta P) / P )^2 $

- *Massa ($m$):* $plus.minus 2 %$.
- *Effekt ($P$):* $plus.minus 3 %$.
- *Temp-gradient ($dot(T)$):* $plus.minus 0.1$ °C / $30$ s.

*Huvudinsikt:* Felet domineras av $dot(T)$ när systemet närmar sig jämvikt.

== Resultat: Temperaturutveckling

#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 10pt,
  image("../images/temperature_run1.png", width: 100%),
  image("../images/temperature_run2.png", width: 100%),
  image("../images/temperature_run3.png", width: 100%)
)

- Tydlig trend: $T_H$ ökar, $T_C$ minskar.
- $P(t)$ stabilt i intervallet $130$–$160$ W.

== Resultat: COP-analys

#align(center)[
  #image("../images/cop_analysis.png", width: 65%)
]

- $C O P$ sjunker som väntat med ökande $Delta T$.
- Run 2: Högre massflöde ger högre initial effektivitet.

== Resultat: Osäkerhet

#grid(
  columns: (1fr, 1fr),
  gutter: 10pt,
  image("../images/uncertainty_cop_bands.png", width: 100%),
  image("../images/error_sources_comparison.png", width: 100%)
)

- Relativt fel: $15$–$30 %$.
- Osäkerheten ökar när $dot(T) -> 0$.

= Slutsats

- Hypotesen bekräftad.
- Massa har stor inverkan på praktisk $C O P$.
- Sensorprecision begränsar mätning vid små gradienter.


