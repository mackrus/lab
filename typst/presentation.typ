#import "template.typ": *

#let full-plot(path) = slide(
  config: config-page(
    margin: 0em,
    header: none,
    footer: none,
  ),
)[
  #align(center + horizon)[
    #image(path, width: 91%)
  ]
]

#show: project.with(
  title: [Värmepump],
  authors: ("Filip Petrini", "Markus Bajlo"),
  date: datetime.today().display(),
  course: [Termodynamik *1FA517*],
)

= Värmepump

== Introduktion
#align(horizon)[
  - Undersökning av värmepumpens effektivitet (COP).
  - Fokus på värmeöverföring mellan slutna behållare.
  - Experiment utan vattenflöde ($dot(m) = 0$).
  - Mål: Jämför $"COP"$ som funktion av $T_H - T_C$ med hypotes.
]
== Teori

Beräkning av värmeeffekt:
$
  dot(Q)_"ut" = m_H c_p dot(T)_H
$
Värme- och kylfaktor ($"COP"$):
$
  "COP"_H = dot(Q)_"ut" / P_text("el")
$
// quad #text("och") quad "COP"_C = dot(Q)_"in" / P_text("el")
// quad #text("och") quad dot(Q)_"in" = -m_C c_p dot(T)_C

== Metod
=== Uppställning
#grid(
  columns: (1fr, 1fr),
  gutter: 6pt,
  align: auto,
  image("../images/setup_with_ref.png", width: 92%),
  image("../images/flow_diagram.pdf", width: 92%),

  image("../images/p_setup.png", width: 20%),
)

#align(horizon)[
  - Slutet system: Ingen extern tillförsel av vatten ($dot(m) = 0$).
  - Mätstorheter: $T_(H)(t), T_(C)(t)$ och $P(t)$.
  - $P(t)$ extraherat via OCR från video av elmätaren.
  - Stationära massor i varje försök: $m_H approx 4.6$ kg, $m_C approx 4.5$ kg.
  - Fasövervakning av kylmediet.
]

== Hypotes

Definiera temperaturskillnaden som
$
  Delta T = T_H - T_C
$

$ "COP"_H approx T_H / (T_H - T_C) $

- Ideal värmepump: $"COP"_(H,"ideal") = T_H / (T_H - T_C)$.
- Realistiskt system: Förluster ökar vid större tryck- och temperaturdifferenser.
- Större $Delta T$ $=>$ lägre $"COP"_H$.


= Resultat

#full-plot("../images/temperature_mätnintg1.png")
#full-plot("../images/temperature_mötning2.png")
#full-plot("../images/temperature_mätnintg3.png")
#full-plot("../images/cop_analysis.png")

= Slutsats

- $"Hypotesen större" Delta T => "mindre COP stämmer överens med data" checkmark$.
- Uppmätta värden för COP avviker från de ideala.


== Felanalys

Rimlighet:
- Värden för COP (bortsett från anomali) varierar mellan 1 och 5 vilket är inom ramen för verkliga maskiner.
- Ideala värden divergerar vid mycket små temperaturskillnader.

Systematiska fel:
- Värmeläckage till omgivningen.
- Tidsförskjutning mellan temperatur och effekt.

Andra fel:
- Osäkerheter i P(t) pga okulär avläsning av värden + OCR.
- Mätosäkerheter i temperatur.
- Mätosäkerheter i massa.
