# Formato degli ordini del giorno (G16)

Ogni comandante scrive **un solo file JSON** nella propria cartella (`blu/ordini_G16.json`
oppure `rosso/ordini_G16.json`) con questa struttura. I valori ammessi (tipi di velivolo,
carichi, basi, tipi di unità, limiti) sono in `campagna/G16/parametri.json`.

```json
{
  "giorno": 16,
  "intento_generale": "frase breve: cosa vuoi ottenere oggi",
  "missioni_aeree": [
    {
      "nome": "nome del volo in inglese, breve e univoco, es. 'Hammer', 'Viper', 'Sledge'",
      "blocco": "numero del blocco della giornata (1 alba, 2 mezzogiorno, 3 pomeriggio; vedi parametri.json)",
      "tipo": "CAP | GCI | SCORTA | STRIKE | CAS | SEAD | ANTINAVE | AWACS | TANKER | TRASPORTO",
      "velivolo": "tipo DCS dalla lista della tua parte",
      "numero": 2,
      "carico": "nome del carico dalla lista del velivolo ('nessuno' per AWACS/tanker/trasporto)",
      "base": "base di partenza dalla lista della tua parte",
      "decollo": "HH:MM, dentro la finestra del blocco (parametri.json -> blocchi)",
      "obiettivo": [lat, lon],
      "raggio_km": 20,
      "quota_ft": 20000,
      "durata_min": 40,
      "rotta": [[lat, lon], [lat, lon]],
      "scorta_di": "nome della missione da scortare (solo SCORTA)",
      "giocatore": false,
      "note": "facoltativo"
    }
  ],
  "unita_terra": [
    {
      "nome": "nome breve univoco",
      "tipo": "carri | meccanizzata | artiglieria | lanciarazzi | contraerea_mobile | sa2 | sa3 | sa5 | sa6 | sa8 | aaa | ewr | hawk",
      "centro": [lat, lon],
      "raggio_km": 5,
      "settore": [da_gradi, a_gradi],
      "obiettivo": [lat, lon],
      "missione": "difesa | attacco | fuoco",
      "avanza_verso": [lat, lon],
      "bersaglio_fuoco": [lat, lon]
    }
  ]
}
```

Significato dei campi:
- **obiettivo** (aereo): CAP/GCI = centro della zona di pattuglia; STRIKE = punto da bombardare;
  CAS/SEAD = centro della zona d'azione (raggio_km); ANTINAVE = zona dove cercare navi;
  AWACS/TANKER = centro dell'orbita; TRASPORTO = punto di atterraggio.
- **rotta**: facoltativa, punti intermedi per evitare le difese.
- **blocchi**: la giornata ha 3 blocchi (alba 05:45-08:45, mezzogiorno 10:30-13:30, pomeriggio
  14:30-17:30). Ogni volo appartiene a un blocco e decolla nella sua finestra. **In ogni blocco al
  massimo 14 aerei della tua parte in volo contemporaneamente**, AWACS e cisterne compresi (si conta
  dal decollo alla fine della durata, piu' circa 40 minuti di trasferimento). Limiti totali della
  giornata in `parametri.json`.
- **unita_terra** valgono per tutta la giornata: le schieri una volta, restano nei tre blocchi.
- **giocatore** (solo blu): `true` per i voli che il giocatore può pilotare (al massimo 4,
  velivoli in `velivoli_giocatore_blu`); il giocatore ne sceglie uno, gli altri volano in AI.
- **unita_terra**: NON dai coordinate esatte. Dai un **centro di ricerca** e un **raggio**: il
  piazzatore dell'arbitro sceglie il punto preciso sul terreno (pendenza, edifici, vegetazione,
  strade, visibilità radar). **settore** = rotte verso la minaccia da coprire o il fronte.
- **missione**: `difesa` = resta in posizione; `riserva` (solo SAM) = batteria nascosta e spenta,
  entra in azione solo quando la rete perde un'altra batteria; `attacco` = avanza verso `avanza_verso`;
  `fuoco` (solo artiglieria/lanciarazzi) = bombarda `bersaglio_fuoco`.
- Puoi riusare i siti fissi già esistenti (SA-5, SA-2, SA-3) indicandone il centro: se il centro
  coincide con un sito noto, resta lì.


## Correzioni tra un blocco e l'altro
Dopo ogni blocco il comandante riceve il proprio rapporto intel e puo' scrivere
`<parte>/ordini_GNN_Bk.json` per il blocco k: `missioni_aeree` sostituisce i voli di quel blocco,
`unita_terra` aggiunge o sostituisce (per nome) unita' di terra, che vengono ripiazzate.
Le unita' di terra non nominate restano dove sono, con le perdite e i danni del blocco precedente.
