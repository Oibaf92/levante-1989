# Lezioni apprese — correzioni del giocatore ed errori da non ripetere

Registro vivo: ogni correzione del giocatore e ogni errore trovato in DCS va aggiunto qui
(con la data e, se c'e', la verifica automatica che lo previene). Va letto prima di
costruire o modificare una missione. Le regole piu' importanti sono riassunte in CLAUDE.md.

## Preferenze del giocatore

| Tema | Regola | Origine |
|---|---|---|
| Portaerei | Lontana dalla Siria: a nord di Cipro, almeno ~150 km dalla costa siriana (zona `ZONA_NAVALE_USA`). | G00, chiesto due volte |
| Navi da aviazione | CVN e LHA navigano **contro vento** (decolli e appontaggi). Rotta calcolata in volo sul vento reale da `script/lua/levante_navi.lua`; CVN con scarto di ~9 gradi per il ponte angolato. Serve mare aperto davanti alla prua per tutta la missione. | G15 |
| Partenza dalla portaerei | Non usare i primi 4 posti; avvio ritardato (>= 5 s) perche' a missione avviata i posti 5-8 della Supercarrier si disattivano. In G00 il giocatore voleva il parcheggio 10 (secondo elevatore, vicino all'isola). | G00 |
| Voli del giocatore | Entra subito in cabina (decollo 0 / 5 s), l'orario previsto resta solo nel briefing: non deve aspettare. | G15 |
| Gregario | Il giocatore vola con un gregario IA di scorta (aria-aria). F-14 di scorta: 2 AIM-9, 3 AIM-7, 2 AIM-54 sui primi due pallet. (2 AIM-54 + 4 AIM-7 non e' un carico valido.) | G00 |
| Ponte della portaerei | Aerei statici sul ponte per realismo. | G00 |
| Mappa F10 | Confini con poligoni chiusi; niente scritte sulla mappa ma una **legenda** con forme diverse; simboli nella posizione **esatta** anche se si sovrappongono; simboli diversi per SA-2, SA-3, SA-5, SA-6, SA-8. Le tavolette vanno aggiornate insieme alla mappa. | G00 |
| Piazzamento | Niente unita' in boschi, frutteti, edifici o pendii; poligono di tiro fuori dalle foreste; per le batterie in zona agricola/costiera chiedere lo screenshot ravvicinato. | G00, P00 |
| Informazioni | Campagna: separazione rigida (CLAUDE.md). **Missione di test**: se il giocatore lo chiede, versione a carte scoperte con `script/tools/apri_test.py <giorno>` (mappa F10 completa, briefing di entrambe le parti, dossier, mappa). | G15 |
| Lingua | Italiano. | sempre |

## Errori tecnici gia' commessi (e come si evitano)

| Errore | Effetto in DCS | Correzione / prevenzione |
|---|---|---|
| `a_do_script` con una chiave del dizionario | script non eseguito | Usare file di script (`a_do_script_file` + `mapResource`). |
| Nominativi radio numerici per la Siria | **il Mission Editor si pianta al caricamento** (`me_aircraft getNewCallsign: attempt to index field 'callsign'`) | Numerici solo per i paesi orientali (Russia, URSS, Ucraina, Bielorussia, Cina, Jugoslavia, DDR, Abcasia, Ossezia del Sud, Insorti); tutti gli altri, Siria compresa, `{1=nome, 2=gruppo 1-9, 3=aereo, name="Enfield11"}`. AWACS (Overlord...) e cisterne (Texaco...) hanno liste proprie. |
| Navi con un solo punto di rotta o rotta fissa | ferme o con vento in coda | Rotta contro vento in volo (`levante_navi.lua`); nel file di missione `wind.dir` e' la direzione VERSO cui soffia il vento. |
| `luatable.dump` con una lista Python | Lua non valido (sintassi `[...]`) | Usare dizionari con chiavi 1, 2, 3... (le liste non sono supportate). Il test Lua lo rileva. |
| Stesso nome di gruppo per le due parti | gruppi sovrascritti | `_rinomina_doppi` aggiunge (USA)/(SY). |
| Gruppi di terra sovrapposti | veicoli uno dentro l'altro | Il piazzatore tiene almeno 60 m tra veicoli di gruppi diversi (`DIST_VEICOLI`). |
| Carichi con CLSID inventati / piloni sbagliati | carico rifiutato o vuoto | `script/tools/carichi.py` (CLSID verificati o risolti su `piloni.json`); `python3 script/tools/carichi.py` deve dare 0 errori. |
| Poligoni non chiusi, riempimento concavo errato | disegni strani | Linee chiuse, poligoni scomposti in pezzi convessi. |
| Poligono di tiro in una foresta | bersagli invisibili | Banca dati della vegetazione (R01) + verifica ravvicinata. |
| Unita' oltre la linea del fronte dopo lo scorrimento | unita' in territorio nemico | Vincoli `dentro`/`fuori` rispettati anche durante lo scorrimento. |
| Giocatore in attesa del proprio orario di decollo | fino a un'ora di attesa | Voli del giocatore sempre a decollo immediato. |
| `zipfile.writestr(ZipInfo)` riusato | CRC errato alla rilettura | Scrivere per nome o rileggere tutto prima. |
| Bersaglio d'artiglieria oltre la portata | il pezzo non spara | Il costruttore lo segnala come AVVISO (va riferito al comandante interessato, non all'altro). |

## Diagnosi dei problemi in DCS

- Chiedere `Saved Games\DCS\Logs\dcs.log` **prima di riavviare DCS** (al riavvio diventa `dcs.log.old`).
- Missione che si pianta al caricamento: cercare `ALERT`/`GUI Error` e `traceback` nelle ultime righe.
- Se il log non basta: versioni ridotte della missione (senza aerei / terra / navi / disegni) per isolare la parte.

## Controlli prima di consegnare una missione

1. Test Lua simulati: `script/test/prova_piazzatore.py`, `script/test/prova_navi.py` (e gli altri pertinenti).
2. `python3 script/tools/carichi.py` senza errori.
3. ID di gruppi e unita' unici; nomi di gruppo unici; nominativi radio validi per paese.
4. Nessuna coppia di gruppi di terra con veicoli sotto 60 m (salvo protezioni volute).
5. Navi da aviazione con mare aperto contro vento; portaerei nella zona navale USA.
6. Rileggere questo file.
