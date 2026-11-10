# Istruzioni per Claude — campagna "Fuoco sul Levante 1989"

Campagna dinamica DCS World (mappa Syria), giocatore singolo. Lingua: italiano.

## Ruoli
- **Sessione principale = ARBITRO.** Non prende decisioni per nessuna delle due parti.
  Costruisce le missioni unendo gli ordini dei comandanti, applica le regole (risorse,
  tempi, era 1989) e aggiorna lo stato condiviso in `campagna/`.
- **Comandante BLU** e **comandante ROSSO** lavorano ciascuno in un agente/contesto
  separato, che riceve SOLO: il README, lo stato pubblico, il proprio rapporto intel
  e la propria cartella (`blu/` oppure `rosso/`).

## Regola di separazione delle informazioni (inviolabile)
- L'arbitro non riassume e non rivela mai a un comandante il contenuto della cartella
  o del rapporto intel dell'altra parte.
- Al giocatore non si rivelano mai schieramenti o piani nemici: riceve solo il briefing
  della parte con cui vola e solo ciò che serve alla sua missione.

## Struttura
- `campagna/` stato condiviso (giorno di guerra, perdite totali, risorse)
- `missioni/` un .miz per giornata
- `script/` motore della campagna (Lua, MOOSE), strumenti di analisi
- `blu/`, `rosso/` diari e piani riservati

## Piazzamento delle unita' di terra (piazzatore)
- I comandanti NON danno coordinate esatte: danno un'intenzione per ogni unita'
  (sistema, nome, centro di ricerca, raggio, settore da coprire, obiettivo da proteggere).
- L'arbitro la passa a `script/tools/piazzatore.py` (`Intenzione`, `piazza_tutti`), che usa
  `campagna/terreno/terreno_completo.npz` e restituisce posizione, disposizione dei veicoli e
  3 alternative. Sistemi: sa2, sa3, sa5, sa6, sa8, aaa, ewr, hawk (vedi `SISTEMI`).
- Nella missione va incluso `script/lua/levante_piazzatore.lua` con la tabella
  `LEVANTE_PIAZZAMENTI` (vedi `script/costruisci_p00.py`): verifica ogni veicolo all'avvio e
  gestisce la segnalazione F10 SPOSTA. Gli spostamenti finiscono in `extra.piazzatore` dello
  stato salvato: alla giornata successiva vanno riportati nel piazzamento (posizione da evitare).
- Alberi: la vegetazione da satellite (80 m) non vede frutteti e filari piccoli. Per ogni
  batteria in zona agricola o costiera chiedere al giocatore uno screenshot ravvicinato
  (Mission Editor, vista SAT, zoom massimo, scala ~200 ft) e acquisirlo con
  `script/tools/aggiungi_verifiche.py <missione.miz> <screenshot...>`: riconosce la batteria,
  aggiunge gli alberi a `campagna/terreno/alberi_noti.npz`, e il piazzatore sposta i veicoli
  di pochi metri fuori dai filari. Dopo ogni volo, `script/tools/importa_stato.py <stato>`
  importa i segni BOSCO/SPOSTA come zone da evitare.

## Lezioni apprese (leggere `docs/lezioni.md` prima di costruire una missione)
- Ogni correzione del giocatore o errore trovato in DCS va registrato in `docs/lezioni.md`.
- Portaerei lontana dalla Siria; CVN e LHA contro vento (`script/lua/levante_navi.lua`).
- Voli del giocatore: decollo immediato, posti 5-8 della Supercarrier solo con avvio >= 5 s.
- A OGNI missione chiedere al giocatore: parte con cui vola (blu/rosso, a sua scelta) e tipo di partenza
  (freddo/caldo/pista/aria). Non deciderli.
- Mappa F10: solo forze amiche + stima intel del comandante della parte del giocatore; niente contatti
  in tempo reale, niente etichette.
- Giornata divisa in blocchi (di norma 3), una missione per blocco; CSAR per i piloti abbattuti; limite 30 giornate.
- Standard: giocatore + 1 gregario IA, volo di giorno (mattina; alba/tramonto ok). Notte e formazioni
  diverse solo se le chiede il giocatore.
- IA High che cala con il logoramento; media intensita' (max 3 SAM sull'obiettivo del giocatore);
  era 1989: niente GPS ne' AIM-120, eccezione AH-64D e CH-47F.
- Radio del giocatore preimpostate (piano in `RADIO_BLU`, canali in `Costruttore.canali()`); coordinate
  in gradi e minuti decimali, NM/ft/kt, QNH inHg (hPa).
- Solo F-14A (VF-84/VF-41), niente F-14B. Livree scelte dal giocatore in `LIVREE` (costruttore); modelli
  delle radio in `script/dati/radio_modelli.json`.
- Nomi dei voli in inglese (es. Hammer); F/A-18C solo VFA-87.
- Missili: AIM-54C Mk47, AIM-7MH (F-4E: AIM-7M), AIM-9M; siriani R-60M, sovietici R-73. Catalogo carichi in
  `docs/lezioni.md`, definizione in `script/tools/carichi.py` (piloni fissati per nome).
- Nominativi radio: numerici solo per i paesi orientali (Russia...); Siria e occidentali nome+numeri,
  altrimenti il Mission Editor si pianta al caricamento.
- `luatable.dump` non accetta liste Python: usare dizionari con chiavi 1..n.
- Missione di test a carte scoperte solo se il giocatore la chiede: `script/tools/apri_test.py <giorno>`.
- Per i problemi in DCS: `dcs.log` preso prima di riavviare DCS.
- Prestazioni (i7-7700K): max ~28 aerei in volo insieme, 220 unita' di terra, 120 vicino al giocatore;
  il costruttore avvisa con `PRESTAZIONI:`. Moduli pilotabili e tipi DCS in `docs/lezioni.md`.
