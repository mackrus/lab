#set page(paper: "a4", numbering: none)
#set text(lang: "sv")
#set heading(numbering: none)
#set cite(style: "american-institute-of-physics")
#set math.equation(numbering: "(1)")
#align(center)[
  #text(2em, weight: "bold")[Värmepump - Labförslag]

  *Författare:* Filip Petrini, Markus Bajlo \ *Datum:* #datetime.today().display() \
  *Kurs:* Termodynamik *1FA517* \
]

// = Instruktioner
//
// En proposal ska innehålla:
//
// - En beskrivning av vilka storheter ni vill mäta och om ni vill mäta med eller utan vattenflöde
//
// - En hypotes kring vilka [kvalitativa] resultat ni förväntar er med en [kort] förklaring

#align(center, [= Förslag])

== Vad vi ska mäta och hur
Vi tänkte köra labben med två behållare med stillastående vatten (alltså utan vattenflöde) och kolla på hur temperaturerna ändras över tid. Det här är vad vi tänker mäta:

- temperaturer i den varma och kalla behållaren som funktion av tid, $T_ut (t)$ och $T_in (t)$
- elektrisk effekt till kompressorn, $P(t)$
- hur mycket vatten vi har i behållarna, $m_ut$ och $m_in$
- vi håller också koll på vilken fas kylmediet är i (vätska, ånga eller båda)

Sen kan vi räkna ut den avgivna och upptagna värmeeffekten genom att kolla på vattnets temperaturförändring över tid:
$ dot(Q)_ut = m_ut c_p dot(T)_ut $
och
$ dot(Q)_in = -m_in c_p dot(T)_in $

Värmefaktorn $"COP"_ut$ och kylfaktorn $"COP"_in$ får vi sen fram genom:
$ "COP"_ut = dot(Q)_ut / P_(#text([pump])) $
och
$ "COP"_in = dot(Q)_in / P_(#text([pump])) $


== Hypotes
Vår gissning är att COP beror på hur stor temperaturskillnaden är mellan reservoarerna, alltså
$ Delta T = T_ut - T_in $.
När $Delta T$ växer så tror vi att både $"COP"_ut$ och $"COP"_in$ kommer sjunka, eftersom kompressorn får jobba hårdare ju mer värme som flyttas, för en realistisk verkningsgrad borde mer energi gå till spillo vid större energinivåer. Rent kvalitativt borde det funka ungefär som för en ideal värmepump:
$ "COP"_(ut,#text([ideal])) = T_ut / (T_ut - T_in) $,
där man ser att COP minskar när nämnaren blir större.

