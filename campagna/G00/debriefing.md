# G00 Ambientamento: debriefing del primo volo (9 novembre 2026)

## Esito tecnico
- Salvataggio funzionante: stato scritto all'avvio, ogni 5 minuti e a fine missione.
- Interruzione dopo 10 min 20 s, alle 07:40:19 di missione: il visore Rift S si è
  scollegato (USB), la sessione OpenXR è andata persa e DCS si è chiuso. Gli script della
  missione non c'entrano.
- Avviso innocuo nel log: `RANGE ... os or os.date() not available` (MOOSE vorrebbe la
  data del PC; `os` resta bloccato apposta).

## Volo (Dodge 2-1, F-14A, partenza a motori accesi)
| Ora | Evento |
|---|---|
| 07:30:00 | Ingresso in cabina sul ponte della CVN-71 |
| 07:33:00 | Catapultato |
| 07:33:11 | In volo |
| 07:38:29 | Sgancio BDU-33 sul bersaglio A |
| 07:38:49 | Impatto |
| 07:40:19 | Fine (disconnessione del visore) |

## Sgancio
| Parametro | Valore |
|---|---|
| Arma | BDU-33 |
| Bersaglio | A |
| Rotta di attacco | 039° (prevista 040°) |
| Quota | 8.465 ft |
| Velocità | 576 kt (profilo suggerito 450 kt) |
| Distanza allo sgancio | 4,85 km |
| Impatto | 304 m (1.000 ft) lungo, radiale 045° |
| Valutazione | POOR |

L'impatto è quasi sulla linea di volo ma 300 m oltre il bersaglio: errore in distanza,
non in direzione. Cause probabili: velocità molto più alta del profilo (576 contro 450 kt)
e sgancio da quota elevata con lunga traiettoria, dove piccoli errori di tempo si amplificano.
