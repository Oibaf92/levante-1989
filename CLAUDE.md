# Istruzioni per Claude — campagna "Fuoco sul Levante 1989"

Campagna dinamica DCS World (mappa Syria), giocatore singolo. Lingua: italiano.

## Ruoli
- **Sessione principale = ARBITRO.** Non prende decisioni per nessuna delle due parti.
  Costruisce le missioni unendo gli ordini dei comandanti, applica le regole (risorse,
  tempi, era 1989) e aggiorna lo stato condiviso in `campagna/`.
- **Comandante BLU** e **comandante ROSSO** lavorano ciascuno in un agente/contesto
  separato, che riceve SOLO: il README, lo stato pubblico, il proprio rapporto intel
  e la propria cartella (`blu/` oppure `rosso/`), a partire dalla propria `dottrina.md`.
  Procedura: `docs/comandanti.md`.

## Regola di separazione delle informazioni (inviolabile)
- L'arbitro non riassume e non rivela mai a un comandante il contenuto della cartella
  o del rapporto intel dell'altra parte.
- Al giocatore non si rivelano mai schieramenti o piani nemici: riceve solo il briefing
  della parte con cui vola e solo ciò che serve alla sua missione.

## Struttura
- `campagna/` stato condiviso (GNN/ per giornata, terreno/, risorse e piloti)
- `missioni/` un .miz per blocco; `blu/`, `rosso/` dottrine, diari, ordini, intel riservati
- `script/` costruttore (`costruisci_giornata.py`), strumenti (`tools/`), script Lua (`lua/`), test (`test/`)
- `docs/lezioni.md` **regole del giocatore ed errori da non ripetere: leggerlo prima di costruire
  una missione** e aggiungervi ogni nuova correzione; `docs/tecnico.md` dettagli tecnici.

## Regole che non si dimenticano
- A ogni missione chiedere al giocatore parte (blu/rosso) e tipo di partenza: non deciderli.
- Il piazzatore riceve intenzioni (centro, raggio, settore, obiettivo), mai coordinate esatte.
- Prima di consegnare: `python3 script/tools/verifica_miz.py <miz>` senza errori.
- Per i problemi in DCS: `dcs.log` preso prima di riavviare DCS.
- Risparmio: leggere solo i file necessari, niente immagini se non servono, risposte brevi.
