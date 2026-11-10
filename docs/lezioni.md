# Lezioni apprese (versione compatta)

Regole del giocatore ed errori da non ripetere. Leggere prima di costruire una missione; aggiungere
ogni nuova correzione in una riga. La storia completa e' nella cronologia git.

## Preferenze del giocatore
- **Prima di ogni missione chiedere**: parte con cui vola (blu/rosso) e partenza (`freddo`/`caldo`/
  `pista`/`aria`, in `parametri.json` -> `partenza_giocatore`; senza, il costruttore si ferma).
- Giocatore + 1 gregario IA (`aerei_giocatore` solo se chiede altro); decollo immediato (orario solo nel
  briefing); di giorno, notte solo su richiesta (`"notte": true`).
- Portaerei a nord di Cipro, >= 150 km dalla Siria; CVN e LHA contro vento (`levante_navi.lua`; con
  vento < 3 m/s a ovest). Supercarrier: posti 5-8 solo con avvio >= 5 s.
- Navi con ROE difensive (rispondono solo se attaccate, `ROE_NAVI_DIFENSIVE`); attacchi navali solo come
  missioni ANTINAVE. **Niente SA-5**: piu' SA-2 (citta' + Dumayr, Al Qusayr, Baalbek, Tartus).
- Mappa F10: solo forze amiche + stima intel della propria parte (`rapporto_intel.py`), niente
  contatti in tempo reale ne' etichette; legenda a forme, simboli in posizione esatta.
- Giornata in blocchi (alba 05:45-08:45, mezzogiorno 10:30-13:30, pomeriggio 14:30-17:30), una missione
  per blocco; perdite: distrutto = perso, danneggiato = fermo 1-2 blocchi; CSAR; limite 30 giornate.
- IA High, cala con il logoramento (>20% Good, >40% Average); media intensita' (max 3 SAM
  sull'obiettivo del giocatore, avviso `INTENSITA:`); era 1989 (niente GPS ne' AIM-120, eccezione
  AH-64D e CH-47F; `ERA_VIETATE` in `carichi.py`).
- Radio del giocatore preimpostate (`RADIO_BLU`, `Costruttore.canali()`, modelli in
  `script/dati/radio_modelli.json`; mancano MiG-29 e Su-25). Coordinate in gradi e minuti decimali,
  NM/ft/kt, QNH inHg (hPa). Tavolette: ordini, una pagina per volo (con radio), intel.
- Nomi dei voli in inglese (es. Hammer); il nominativo radio DCS e' a parte (mostrato su briefing).
- Missioni a carte scoperte (`apri_test.py`) e da osservare (`--osservatore`) solo su richiesta.

## Moduli, livree, missili
- Blu: `F-14A-135-GR-Early` (solo A, VF-84/VF-41), `FA-18C_hornet` (solo VFA-87), `F-4E-45MC`,
  `AH-64D_BLK_II`, `CH-47Fbl1`. Rosso: `MiG-29 Fulcrum`, `Su-25`, `Mi-24P`, `Mi-8MT`. Niente mod salvo accordo.
- Livree in `LIVREE` (costruttore). Missili: AIM-54C Mk47, AIM-7MH (F-4E: AIM-7M), AIM-9M; siriani
  R-27R + R-60M, sovietici R-27R + R-73.
- Carichi in `script/tools/carichi.py` (piloni fissati per nome; `python3 script/tools/carichi.py` = 0
  errori). F-14: CAP 2-3-2 e 0-6-2, TARPS, strike Mk-84/Mk-82 (eccezione voluta). F/A-18C: CAP 2-4 / 2-6
  (AR), SEAD, strike, CAS (AR), antinave. F-4E: CAP, strike, CAS, SEAD, bombe laser con Pave Spike.
  AH-64D, Su-25, Mi-24P, Mi-8MT, MiG-29, MiG-23 (IA). AR = autonomia ridotta (avviso `AUTONOMIA:`).

## Prestazioni (i7-7700K 4 core, DCS 2.9 MT)
- Bilancio `BILANCIO`: 28 aerei in volo insieme (14 per parte, `aerei_in_volo_max`, avviso `LIMITI:`),
  220 veicoli, 120 vicino al giocatore, 12 navi, 300 unita'.
- Siti SAM fissi lontani dai voli del blocco fuori dalla missione (`MARGINE_SITI_KM`); aerei IA rimossi
  dopo il rientro (`levante_prestazioni.lua`, `extra.rientrati` non sono perdite).
- Script leggeri: controlli periodici >= 5 s, niente ricerche di oggetti in volo, file piccoli.
- Le prestazioni si valutano senza accelerazione del tempo (con l'accelerazione: "ANTIFREEZE").

## Ciclo di una giornata
1. `python3 script/tools/meteo.py <g>` (meteo + previsione nella situazione pubblica).
2. `python3 script/tools/rapporto_intel.py <g> <b>` (intel riservati `blu/`, `rosso/`).
3. Comandanti (agenti separati, `docs/comandanti.md`) -> `<parte>/ordini_GNN.json`.
4. `python3 script/costruisci_giornata.py <g> <b> [--osservatore]` -> `missioni/GNN_Bb_<data>.miz`.
5. Volo; `python3 script/tools/importa_stato.py <stato>` -> `campagna/GNN/esiti_Bb.json`
   (+ AIM-54, piloti, TPQ-37, TARPS in `regole_speciali.py`); poi blocco successivo (correzioni in
   `<parte>/ordini_GNN_Bb.json`).

## Script in missione
`levante_core` (stato, registro, `LEVANTE.debug`), `levante_piazzatore` (verifica veicoli, SPOSTA/BOSCO),
`levante_navi`, `levante_prestazioni`, `levante_iads` (rete senza onniscienza: sensori veri, ritardi,
HARM 65%, spostamento dopo il tiro, riserva, radar acceso finche' guida i missili), `levante_regole`.

## Errori gia' commessi
| Errore | Prevenzione |
|---|---|
| Nominativi radio numerici per la Siria: il Mission Editor si pianta | numerici solo per i paesi orientali; `verifica_miz.py` |
| Rotta senza `ETA_locked`: l'editor non salva | primo punto bloccato; `verifica_miz.py` |
| `a_do_script` con chiave del dizionario | `a_do_script_file` |
| `luatable.dump` con liste Python | dizionari con chiavi 1..n |
| JSON trasforma le chiavi intere in stringhe | ricaricare con `chiavi_int` |
| Nomi di gruppo uguali tra le parti | `_rinomina_doppi` |
| Gruppi di terra sovrapposti | `DIST_VEICOLI` = 60 m |
| Risolutore automatico dei piloni (AIM-54 sulle spalle) | carichi del giocatore fissati a mano |
| `piloni.json` incompleto | rigenerare con `estrai_piloni.py` |
| `zipfile.writestr(ZipInfo)` riusato | scrivere per nome |
| Navi con ROE libere: guerra navale da sola (G16) | `ROE_NAVI_DIFENSIVE` |
| Radar SAM spento con missile in volo | `GUIDA` in `levante_iads.lua` |
| Unita' oltre il fronte dopo lo scorrimento | vincoli `dentro`/`fuori` |

## Diagnosi e consegna
- `dcs.log` preso prima di riavviare DCS; cercare `ALERT`, `GUI Error`, `traceback`, `[LEVANTE`.
- Prima di consegnare: `verifica_miz.py` senza errori; test in `script/test/` (prova_blocchi lavora su
  una copia temporanea); nessun avviso `PRESTAZIONI:`/`LIMITI:` non spiegato.

## Da verificare / in attesa
- In DCS: flotta che si difende con ROE difensive; basi delle nubi nei limiti dei preset; magazzino
  AIM-54 della portaerei; torre di Incirlik 360.100; Stinger Baabda senza posto (zona urbana).
- Dal giocatore: modelli radio di MiG-29 e Su-25 (aprire la pagina radio nel Mission Editor e salvare).
