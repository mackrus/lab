#import "template.typ": *

#show: project.with(
  title: [Värmepump],
  authors: ("Filip Petrini", "Markus Bajlo"),
  date: datetime.today().display(),
  course: [Termodynamik *1FA517*],
)

= Introduktion

I den här laborationen undersöker vi effektiviteten hos en värmepump genom att studera värmeöverföring mellan två slutna vattenbehållare.

- Experiment utan vattenflöde (stillastående vatten).
- Beräkning av värmeeffekt via temperaturförändring.
- Analys av värmefaktorns ($C O P$) beroende av temperaturskillnad.

== Teori

Värmeeffekten som avges till den varma behållaren ($dot Q_H$) och tas upp från den kalla ($dot Q_C$) beräknas ur vattnets temperaturförändring:

$ dot(Q)_H = m_H c_p dot(T)_H $
$ dot(Q)_C = -m_C c_p dot(T)_C $

Värmefaktorn ($C O P_H$) och kylfaktorn ($C O P_C$) definieras som:

$ C O P_H = dot(Q)_H / P_(#text([pump])) $
$ C O P_C = dot(Q)_C / P_(#text([pump])) $

== Metod

Vi använder två behållare med en känd mängd vatten ($m_H, m_C$) och mäter följande storheter som funktion av tid:

+ Temperaturer $T_H(t)$ och $T_C(t)$.
+ Elektrisk effekt till kompressorn $P(t)$.
+ Kylmediets fas i olika delar av cykeln.

Inget vattenflöde används, vilket förenklar beräkningen av den totala energin i systemet.

== Hypotes

Vi förväntar oss att $C O P$ minskar när temperaturskillnaden $Delta T = T_H - T_C$ ökar.

Kvalitativt bör det följa beteendet hos en ideal värmepump:
$ C O P_(h,"ideal") = T_H / (T_H - T_C) $

Ju större temperaturskillnad kompressorn måste arbeta mot, desto lägre blir verkningsgraden.

== Resultat

Här presenteras mätdata, grafer över $T(t)$ samt beräknade värden på $C O P$ som funktion av $Delta T$.
