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
| Tipo di partenza | **Lo decide il giocatore a ogni missione** (cosi' gestisce la durata): chiedere sempre prima di costruire tra `freddo` (accensione), `caldo` (motori accesi al parcheggio), `pista` e `aria`; si scrive in `parametri.json` -> `partenza_giocatore` (un valore, o `{"nome volo": tipo, "*": tipo}`). Senza indicazione il costruttore si ferma. | punto 2 delle lezioni |
| Formazione standard | Il giocatore vola **con un gregario IA** (2 aerei). Formazioni diverse solo se le chiede lui (`parametri.json` -> `aerei_giocatore`: `{"nome volo": n}`); il costruttore impone 2 ai voli del giocatore. | punto 2 delle lezioni |
| Orario | Di **giorno**, di solito **mattina**; vanno bene anche l'alba e il tardo pomeriggio verso il tramonto. **Notte solo su sua richiesta** (`parametri.json` -> `"notte": true`); il costruttore avvisa con `ORARIO:` se la missione esce dal giorno. | punto 2 delle lezioni |
| Gregario | Il giocatore vola con un gregario IA di scorta (aria-aria). F-14 di scorta: 2 AIM-9, 3 AIM-7, 2 AIM-54 sui primi due pallet. (2 AIM-54 + 4 AIM-7 non e' un carico valido.) | G00 |
| Versioni dei missili (autunno 1989) | **AIM-54C Mk47, AIM-7MH, AIM-9M** su F-14 e F/A-18C; l'F-4E usa AIM-7M (in DCS non ha il 7MH) e AIM-9M. Niente AIM-54C Mk60/C+, AIM-7P, AIM-9X. Rossi: **siriani R-27R + R-60M**, **contingente sovietico R-27R + R-73** (quest'ultimo da verificare sul modulo MiG-29 del giocatore: CLSID ignoti). | punto 4 |
| Carichi F-14 (CAP) | I due carichi tipici, in notazione AIM-54 - AIM-7 - AIM-9: **2-3-2** (AIM-54 sui due pallet anteriori, AIM-7 su spalle e ventre, AIM-9 alle punte; e' anche il carico di scorta) e **0-6-2** (sei AIM-7: spalle + quattro sul ventre). Sempre con 2 serbatoi da 300 gal. In `carichi.py`: `cap 2-3-2`, `cap 0-6-2` (piloni fissati a mano). | punto 4 |
| Carichi F/A-18C (CAP) | **2 AIM-9 + 4 AIM-7 con i due serbatoi sotto le ali** (`cap 2-4 serbatoi ali`, carico CAP normale) oppure **2 AIM-9 + 6 AIM-7 con il serbatoio sul pilone centrale** (`cap 2-6 serbatoio centrale`): **autonomia ridotta**, solo CAP brevi o vicino a una cisterna; il costruttore avvisa con `AUTONOMIA:` oltre 40 min sull'obiettivo. | punto 4 |
| Ponte della portaerei | Aerei statici sul ponte per realismo. | G00 |
| Mappa F10 | Confini con poligoni chiusi; niente scritte sulla mappa ma una **legenda** con forme diverse; simboli nella posizione **esatta** anche se si sovrappongono; simboli diversi per SA-2, SA-3, SA-5, SA-6, SA-8. Le tavolette vanno aggiornate insieme alla mappa. | G00 |
| Piazzamento | Niente unita' in boschi, frutteti, edifici o pendii; poligono di tiro fuori dalle foreste; per le batterie in zona agricola/costiera chiedere lo screenshot ravvicinato. | G00, P00 |
| Informazioni | Campagna: separazione rigida (CLAUDE.md). **Missione di test**: se il giocatore lo chiede, versione a carte scoperte con `script/tools/apri_test.py <giorno>` (mappa F10 completa, briefing di entrambe le parti, dossier, mappa). | G15 |
| Radio | **Canali preimpostati** nei velivoli del giocatore (lui e il gregario), uguali per tutti i suoi voli: CH1 pacchetto 251, poi AWACS (264), cisterne (270, 271...), CVN 258, LHA 256, Incirlik 360.1, gli interni dei voli del giocatore (301, 302...), guardia 243. I gruppi IA ascoltano la loro frequenza (AWACS, cisterne). Tabella dei canali nella prima tavoletta e nel briefing. I canali si scrivono solo per i moduli di cui conosciamo la struttura della radio (`RADIO_MODELLI`, ricavata da missioni salvate dal Mission Editor): per gli altri il costruttore avvisa con `RADIO:`. Da verificare in volo: frequenza della torre di Incirlik. | punto 4 |
| Coordinate e unita' (deciso dall'arbitro) | Coordinate in gradi e minuti decimali (`N 33°48.000'`), che vanno bene per F-14, F/A-18, F-4E e AH-64; miglia nautiche, piedi, nodi; QNH in inHg con hPa tra parentesi; vento "da" (direzione di provenienza). Meteo nella prima tavoletta. | punto 4 |
| Tavolette | Vanno bene cosi' (ordini, una pagina per volo, intel). | punto 4 |
| Abbattimento / eiezione | **Soccorso (CSAR)**: eiezione su territorio amico o mare -> recupero automatico; su territorio nemico -> posizione registrata (evento `eiezione` del registro), missione di soccorso possibile nei blocchi successivi (CH-47/AH-64 blu, Mi-8/Mi-24 rossi); senza soccorso entro la fine della giornata successiva -> pilota catturato (perdita + morale). Vale per il giocatore e il suo gregario. | punto 5 |
| Ritmo | **Ogni giornata e' divisa in blocchi** (di norma 3: alba ~05:45-08:45, mezzogiorno ~10:30-13:30, pomeriggio ~14:30-17:30), **una missione per blocco**: piu' missioni nella stessa giornata. I risultati di un blocco valgono per il successivo; tra un blocco e l'altro i comandanti possono correggere il piano. Blocchi non volati: risolti dall'arbitro a tavolino. File: `missioni/GNN_Bk_<data>.miz`. | punto 5 |
| Perdite | Distrutto in volo = perso per la campagna; danneggiato = fuori servizio 1-2 blocchi. | punto 5 |
| Parte con cui vola | **A scelta del giocatore, blocco per blocco**: chiederla a ogni missione insieme al tipo di partenza. Il briefing e le tavolette sono solo della parte scelta (separazione delle informazioni). | punto 5 |
| Fine campagna | Condizioni di vittoria del README; **limite 30 giornate**, poi esito ai punti deciso dall'arbitro (territorio, perdite, difesa aerea siriana, gruppo navale). | punto 5 |
| Mappa F10 | Va bene cosi': `optview_allies` (solo forze amiche), **nessun contatto nemico in tempo reale**, niente etichette delle unita'. Le forze nemiche compaiono solo come **stima del comandante** della parte con cui si vola (carta intel nello strato della parte), costruita dal suo rapporto intel di quel blocco, mai dalle posizioni vere. | punto 6 |
| Livree | Scelte dal giocatore (C00, seconda revisione): **F-14A** VF-84 (`vf-84 ghost by reflected`, `vf-84 jaws by reflected`, numeri 2xx) e VF-41 (`vf-41 aj100 1989 by reflected`, `vf-41 aj105 1989 by reflected`, numeri 1xx), a rotazione; **F/A-18C** solo `vfa-87` (4xx); **F-4E** `rs68-381_e1_526tfs`; **AH-64D** `12th combat aviation brigade griffins`; **CH-47F** `us army dark green`; **Su-25** `field camo scheme #1 (native)`; **MiG-29** siriani `syria af`, sovietici `air force standard`; **MiG-23MLD** siriani `Syria_2`; **Mi-24P** siriani `syaaf`, sovietici `af 440 ovp`; **Mi-8** `Russia_VVS_Standard` da trasporto, `Russia_VVS_Standard_2` armato. Stessa livrea per tutto un volo (`LIVREE` nel costruttore, con filtro per carico). Le livree "by reflected" sono un mod del giocatore. | C00 |
| Radio (modelli) | Struttura delle radio dei moduli in `script/dati/radio_modelli.json`, ricavata dalla C00 salvata dal giocatore: F-14A (2 UHF: 20+30 canali), F/A-18C (2x20), F-4E (18+20), AH-64D (VHF 10, **UHF 10**, 2 FM), CH-47F (FM 20, UHF 20, FM 10), Mi-24P e Mi-8 (VHF 20, FM 10). Il piano blu va sulle radio UHF; se i canali non bastano (Apache) si tolgono interni degli altri voli, Incirlik, cisterne, e la tavoletta del volo mostra la lista ridotta. | C00 |
| Nomi dei voli | **In inglese**, una parola breve e univoca (es. *Hammer*), per entrambe le parti: va scritto negli ordini dei comandanti (README, `formato_ordini.md`). Il nominativo radio DCS (Enfield, Chevy...) resta separato ed e' indicato in briefing e tavolette ("radio: Chevy 1-1"). | dopo C00 |
| Livello dell'IA | Nemici **High** all'inizio; il livello **cala con le perdite**: logoramento (frazione persa dell'ordine di battaglia, `parametri.json` -> `logoramento`) oltre 20% -> Good, oltre 40% -> Average (`LOGORAMENTO_ABILITA`). Stessa regola per l'IA blu. | punto 3 |
| Intensita' | Conflitto di **media intensita'** (anche per le prestazioni); missioni del giocatore **abbastanza sopravvivibili**: l'obiettivo di un suo volo non deve essere coperto da piu' di 3 batterie SAM nemiche (SA-2/3/6/8/Hawk; SA-5 escluso, i SEAD esclusi). Il costruttore avvisa con `INTENSITA:`. | punto 3 |
| Era 1989 | **Niente GPS, niente AIM-120** (ne' AIM-9X, R-77, JSOW, SLAM, pod di puntamento moderni). `carichi.py` rifiuta i carichi fuori era (`ERA_VIETATE`). **Eccezioni**: AH-64D e CH-47F con il loro armamento. Nel menu di riarmo in gioco il rispetto dell'era e' affidato al giocatore. | punto 3 |
| Lingua | Italiano. | sempre |

## Moduli del giocatore

| Parte | Moduli pilotabili | Tipo DCS da usare per lo slot |
|---|---|---|
| Blu | F-14A, F/A-18C, F-4E, AH-64D, CH-47F | `F-14A-135-GR-Early` (**niente F-14B**: nel 1989 la Roosevelt aveva F-14A di VF-84 e VF-41), `FA-18C_hornet`, `F-4E-45MC`, `AH-64D_BLK_II`, `CH-47Fbl1` |
| Rosso | MiG-29, Su-25, Mi-24, Mi-8 | `MiG-29 Fulcrum`, `Su-25`, `Mi-24P` (il modulo e' il P, non il V), `Mi-8MT` |

- Gli slot del giocatore (`Client`) si creano solo per questi moduli; tutti gli altri velivoli sono IA.
- Volando con i rossi servono carichi verificati anche per `Mi-24P` e `Mi-8MT` (da aggiungere a
  `carichi.py` alla prima missione rossa, ricavandoli da una missione salvata dal giocatore).
- Nessuna unita' che richieda mod o asset pack non base, salvo accordo esplicito.

## Prestazioni (PC del giocatore: i7-7700K 4 core / 8 thread, 64 GB, DCS 2.9 MT)

In DCS il limite e' la CPU della simulazione (IA, sensori, radar, balistica), non la RAM ne' la
grafica: con 4 core il thread principale si satura presto. Ogni aereo IA costa molto piu' di un
veicolo; i radar SAM attivi, l'artiglieria che spara e la fanteria in gran numero pesano piu' dei
veicoli fermi. Bilancio per missione (costante `BILANCIO` in `script/costruisci_giornata.py`, il
costruttore avvisa con `PRESTAZIONI:` se lo si supera):

| Voce | Limite | Note |
|---|---|---|
| Aerei in volo contemporaneamente (entrambe le parti, supporto incluso) | **28** | circa 14 per parte; scaglionare i decolli |
| Unita' di terra totali | **220** | fanteria solo dove serve (ogni soldato e' un'unita') |
| Unita' di terra entro 30 km dagli obiettivi del giocatore | **120** | e' dove si vola basso e si guarda |
| Navi | **12** | |
| Unita' totali | **300** | |

Regole che ne derivano:
- Ai comandanti va dato un tetto di **aerei in volo contemporaneamente** (non solo di voli),
  compresi AWACS e cisterne, che restano in aria per tutta la missione.
- Le unita' lontane dall'azione del giorno (siti SAM di Aleppo, Hama... oltre ~150 km da rotte e
  obiettivi) restano nello stato della campagna ma non vanno messe nella missione, o vanno
  messe "dormienti" (IA spenta finche' un nemico non si avvicina).
- Aerei IA che atterrano: rimossi 10 s dopo lo spegnimento dei motori (o 180 s dopo l'atterraggio)
  da `script/lua/levante_prestazioni.lua`, tranne i gruppi del giocatore; annotati in
  `extra.rientrati`, che `esiti.py` NON conta come perdite (test `script/test/prova_prestazioni.py`).
- Siti SAM fissi rossi lontani: entrano nella missione solo se un volo blu del blocco passa entro
  portata + 40 km (`MARGINE_SITI_KM`); gli altri restano nella campagna (`fuori_missione` nel
  resoconto). In G15: 247 -> 190 veicoli.
- Tetto per parte di **14 aerei in volo contemporaneamente** (`parametri.json` ->
  `limiti.<parte>.aerei_in_volo_max`): se gli ordini lo superano il costruttore avvisa con `LIMITI:` e
  gli ordini tornano al comandante.
- Riferimento: G15 di prova aveva 325 unita' e circa 60 aerei in volo insieme alle 08:00 —
  troppo per questo PC.

## Catalogo dei carichi (approvato dal giocatore; definizione esatta in `script/tools/carichi.py`)

Notazione: tra parentesi il nome del carico in `carichi.py`. Piloni fissati a mano e verificati
contro `script/dati/piloni.json`; "(AR)" = autonomia ridotta (avviso `AUTONOMIA:` del costruttore).

- **F-14A** (solo A): CAP 2-3-2 (`cap 2-3-2`, anche scorta), CAP 0-6-2 (`cap 0-6-2`), ricognizione con
  pod TARPS + 2 AIM-7 + 2 AIM-9 (`ricognizione TARPS`); **aria-terra per
  eccezione voluta dal giocatore** (nella realta' dal 1990-92): 4 Mk-84 (`strike Mk-84`),
  14 Mk-82 su MAK-79 (`strike Mk-82`), sempre con 2 AIM-7, 2 AIM-9, 2 serbatoi. Niente pod di puntamento.
- **F/A-18C**: CAP 2-4 (`cap 2-4 serbatoi ali`), CAP 2-6 (`cap 2-6 serbatoio centrale`, AR);
  SEAD 2 HARM (`sead`), SEAD 4 HARM (`sead pesante`, AR); strike 2 Mk-84 (`strike Mk-84`),
  4 Mk-83 (`strike Mk-83`); CAS 4 Rockeye + 2 Maverick F (`cas`, AR); antinave 2 Harpoon
  (`antinave`). Autodifesa sempre 2 AIM-9 + 2 AIM-7. AGM-88C accettato al posto degli AGM-88A/B.
- **F-4E**: CAP 4 AIM-7 + 4 AIM-9 + ALQ-131 (`cap`); strike 6 Mk-82 con serbatoi (`strike Mk-82`),
  12 Mk-82 senza serbatoi (`strike Mk-82 pesante`, AR); CAS 6 Maverick B (`cas maverick`),
  8 CBU-87 (`cas cbu`); SEAD 2 Shrike + 4 CBU-87 (`sead`); **bombe laser con Pave Spike approvate
  dal giocatore**: 4 GBU-12 (`strike laser GBU-12`), 2 GBU-10 (`strike laser GBU-10`).
  Autodifesa 3 AIM-7 + 2 AIM-9 + ALQ-131 (nel pozzetto anteriore, o il Pave Spike).
- **AH-64D**: 16 Hellfire (`anticarro`), 8 Hellfire + 38 Hydra (`appoggio`), 4 Hellfire + 57 Hydra (`fanteria`).
- **CH-47F**: nessun carico.
- **MiG-23MLD** (solo IA, siriani): aria-aria 2 R-24R + 4 R-60M (`aria-aria`), 2 B-8M1 + 2 R-60M
  (`attacco razzi`), entrambi indicati dal giocatore in C00.
- **MiG-29** (CLSID del modulo del giocatore, da C00): CAP siriano 2 R-27R + 4 R-60M (`cap siriano R-60M`),
  CAP sovietico 2 R-27R + 4 R-73 (`cap sovietico R-73`), attacco 4 FAB-500 + 2 R-60M (`attacco FAB-500`),
  sempre con serbatoio centrale.
- **Su-25**: CAS 4 B-8 + 4 FAB-250 (`appoggio`), anticarro 4 RBK-250 PTAB + 2 B-8 + 2 SPPU-22
  (`anticarro`), 6 FAB-500 (`strike`), 2 Kh-29L + 2 Kh-25ML (`precisione`); sempre 2 R-60M.
  Niente SEAD (la fanno i Su-24M IA con Kh-58).
- **Mi-24P**: 8 Shturm + 2 B-8V20 (`anticarro`), 4 Shturm + 4 B-8V20 (`appoggio`),
  4 Shturm + 2 GUV + 2 B-8V20 (`fanteria`).
- **Mi-8MT**: nessun carico (`trasporto`), 4 B-8V20 + 2 GUV (`armato`).
- Tutti i carichi (tranne CAP F-14/F-18 e MiG-29 CAP) sono da confermare in DCS: se il Mission
  Editor ne rifiuta uno, correggerlo e annotarlo qui.

## Errori tecnici gia' commessi (e come si evitano)

| Errore | Effetto in DCS | Correzione / prevenzione |
|---|---|---|
| `a_do_script` con una chiave del dizionario | script non eseguito | Usare file di script (`a_do_script_file` + `mapResource`). |
| Nominativi radio numerici per la Siria | **il Mission Editor si pianta al caricamento** (`me_aircraft getNewCallsign: attempt to index field 'callsign'`) | Numerici solo per i paesi orientali (Russia, URSS, Ucraina, Bielorussia, Cina, Jugoslavia, DDR, Abcasia, Ossezia del Sud, Insorti); tutti gli altri, Siria compresa, `{1=nome, 2=gruppo 1-9, 3=aereo, name="Enfield11"}`. AWACS (Overlord...) e cisterne (Texaco...) hanno liste proprie. |
| Navi con un solo punto di rotta o rotta fissa | ferme o con vento in coda | Rotta contro vento in volo (`levante_navi.lua`); nel file di missione `wind.dir` e' la direzione VERSO cui soffia il vento. |
| `luatable.dump` con una lista Python | Lua non valido (sintassi `[...]`) | Usare dizionari con chiavi 1, 2, 3... (le liste non sono supportate). Il test Lua lo rileva. |
| Stesso nome di gruppo per le due parti | gruppi sovrascritti | `_rinomina_doppi` aggiunge (USA)/(SY). |
| Gruppi di terra sovrapposti | veicoli uno dentro l'altro | Il piazzatore tiene almeno 60 m tra veicoli di gruppi diversi (`DIST_VEICOLI`). |
| `piloni.json` incompleto (estratto da una vecchia lettura di pydcs) | mancavano le bombe sul ventre dell'F-14 | Rigenerarlo con `script/tools/estrai_piloni.py <pydcs>`: nuovo elenco superset del vecchio (0 differenze). |
| Risolutore automatico dei piloni per l'F-14 | in G15 i due AIM-54 di scorta erano finiti sulle spalle invece che sui pallet anteriori | Per i carichi indicati dal giocatore usare dizionari {pilone: CLSID} fissati a mano, non il risolutore. |
| Rotta senza punti con orario bloccato (`ETA_locked`) | **il Mission Editor rifiuta di salvare** ("Route has no waypoints with locked time!") | Primo punto di ogni rotta con `ETA_locked=True`. Controllo automatico in `script/tools/verifica_miz.py` (chiamato da C00 e dal costruttore delle giornate: `ERRORE:`), che verifica anche ID e nomi duplicati e nominativi radio per paese. |
| Carichi con CLSID inventati / piloni sbagliati | carico rifiutato o vuoto | `script/tools/carichi.py` (CLSID verificati o risolti su `piloni.json`); `python3 script/tools/carichi.py` deve dare 0 errori. |
| Poligoni non chiusi, riempimento concavo errato | disegni strani | Linee chiuse, poligoni scomposti in pezzi convessi. |
| Poligono di tiro in una foresta | bersagli invisibili | Banca dati della vegetazione (R01) + verifica ravvicinata. |
| Unita' oltre la linea del fronte dopo lo scorrimento | unita' in territorio nemico | Vincoli `dentro`/`fuori` rispettati anche durante lo scorrimento. |
| Giocatore in attesa del proprio orario di decollo | fino a un'ora di attesa | Voli del giocatore sempre a decollo immediato. |
| `zipfile.writestr(ZipInfo)` riusato | CRC errato alla rilettura | Scrivere per nome o rileggere tutto prima. |
| Bersaglio d'artiglieria oltre la portata | il pezzo non spara | Il costruttore lo segnala come AVVISO (va riferito al comandante interessato, non all'altro). |

## Logica dei comandanti (sessione di test, novembre 2026)

Il giocatore ha verificato le logiche dei due comandanti con una serie di domande; le risposte
confermate e le sue correzioni sono diventate le dottrine riservate `blu/dottrina.md` e
`rosso/dottrina.md`, che ogni comandante legge per prima (procedura in `docs/comandanti.md`).
Correzioni del giocatore: portaerei a distanza di sicurezza e squadra navale russa come priorita'
assoluta; AIM-54 da usare con parsimonia (deterrente antinave); blu con poche perdite, rossi con
tolleranza piu' alta; SA-5 da non sottovalutare (riducono l'area operativa e costringono a volare bassi).

## Lavori sul motore e regole proposte (da fare)

- **Script dei radar SAM** — FATTO: `script/lua/levante_iads.lua` (tabella `LEVANTE_IADS` dal costruttore,
  `Costruttore.dati_iads()`; test `script/test/prova_iads.py`). Parametri in testa allo script
  (ciclo 10 s, ritardo rete 8 s, AWACS +20 s e 70%, HARM 65%/30%, silenzio 60-120 s, ricerca da cieca
  30 s ogni 300 s, spostamento 0,8-1,5 km 90 s dopo il tiro). Sensori: gruppi `ewr` (radar), AWACS,
  `aaa`/`contraerea_mobile`/`carri`/`meccanizzata` (a vista). Da verificare in volo. Progetto:
  - radar di tiro spenti finche' il bersaglio non e' vicino; spostamento dopo il tiro;
  - **niente onniscienza**: la rete reagisce solo a cio' che i suoi sensori rilevano davvero
    (`getDetectedTargets` di radar di sorveglianza P-19/P-14, A-50, SAM gia' accesi, osservatori a
    terra a vista); DCS gestisce orizzonte radar e rilievo, quindi chi vola basso dietro le montagne
    non viene visto;
  - **rete accecabile**: distrutti i radar di sorveglianza, le batterie non ricevono l'allarme e devono
    accendersi per cercare (esponendosi agli HARM);
  - **ritardi**: qualche secondo dalla rete alla batteria; piu' lunghi o assenti se cade un posto comando;
  - **reazione agli HARM incerta**: spegnimento solo se il missile e' rilevato, con probabilita'
    ~60-70% e qualche secondo di ritardo;
  - batteria in agguato: radar acceso pochi secondi, solo con il bersaglio gia' segnalato in portata;
  - A-50 sovietico: condivisione parziale con la rete siriana, con piu' ritardo;
  - prestazioni: controllo ogni 5-10 s interrogando solo i sensori della rete, HARM come eventi.
- **Script leggeri** (regole): niente controlli a ogni fotogramma (periodici >= 5 s), niente ricerche
  di oggetti in volo (solo all'avvio), file di stato piccoli e scritti di rado, log solo per eventi
  importanti. Il peso vero e' il numero di unita' IA.
- **Regole approvate dal giocatore** (README, "Risorse e intelligence speciali" e "Piloti abbattuti") —
  FATTE: registrazione in gioco `script/lua/levante_regole.lua`, conseguenze all'importazione
  `script/tools/regole_speciali.py` (stato in `campagna/risorse.json` e `campagna/piloti.json`),
  test `prova_regole.py` e `prova_blocchi.py`. Il magazzino AIM-54 della portaerei si imposta con
  l'API dei magazzini solo se DCS lo consente (da verificare): il limite sicuro e' quello sui carichi.
  CSAR: il pilota a terra compare come soldato nella missione del blocco dopo; recuperato se un
  elicottero amico atterra entro 300 m; catturato dopo la fine della giornata successiva.
  - **AIM-54 contati**: scorta iniziale 48 sulla CVN-71, -1 per ogni lancio (evento `lancio` del
    registro), +4 al giorno; i carichi con AIM-54 solo se la scorta li copre; magazzino della
    portaerei nella missione = scorta (cosi' anche il riarmo in gioco e' limitato);
  - **AN/TPQ-37**: artiglieria e lanciarazzi rossi che sparano entro ~30 km dalla testa di ponte ->
    posizione (errore ~100-300 m) nell'intel blu del blocco dopo;
  - **TARPS**: F-14 con carico `ricognizione TARPS` sotto i 20.000 ft fotografa le unita' entro ~5 km
    dalla rotta; se atterra, posizioni vere nell'intel blu del blocco dopo; se abbattuto, niente.
    Serve uno script che registri la traccia del volo TARPS.
- Costruttore a blocchi, carta intel per blocco dal rapporto del comandante, CSAR, unita' lontane
  fuori dalla missione o dormienti, aerei IA rimossi dopo l'atterraggio, tetto agli aerei in volo
  negli ordini.

## In attesa dal giocatore

- Modelli delle radio di **MiG-29, Su-25** (il Mission Editor scrive la tabella `Radio` solo
  per le unita' di cui si apre la pagina radio): servono per preimpostare i canali quando si vola con
  questi moduli.
- Esito del controllo dei carichi in C00 (l'editor ha salvato senza modificarne nessuno).

## Ciclo a blocchi (costruttore)

1. `python3 script/costruisci_giornata.py <giorno> <blocco>` -> `missioni/GNN_Bk_<data>.miz`,
   `campagna/GNN/costruzione_Bk.json` (unita' messe in missione) e `terra_Bk.json` (forze di terra
   della giornata all'inizio del blocco, compresi i fermi).
2. Il giocatore vola e manda lo stato; `python3 script/tools/importa_stato.py <stato>` scrive
   `campagna/GNN/esiti_Bk.json` (distrutti, fuori servizio, posizioni finali, perdite aeree).
3. `python3 script/tools/rapporto_intel.py <giorno> <k+1>`: rapporti intel riservati
   `blu/intel_GNN_Bk.json` e `rosso/intel_GNN_Bk.json` (dal rapporto precedente: SAM e unita' mobili
   invecchiano confermato -> probabile -> vecchio -> cancellato; gruppi distrutti tolti; osservazioni
   del blocco aggiunte come confermate). Ogni comandante riceve il proprio. La carta intel F10 e la
   tavoletta INTEL si disegnano da qui (piu' certo = piu' opaco), mai dalle posizioni vere.
4. Blocco k+1: si riparte da `terra_Bk.json` + `esiti_Bk.json`; i gruppi distrutti non si ricreano
   dagli ordini (lista `eliminati`); le navi ripartono da dove erano. Correzioni dei comandanti in
   `<parte>/ordini_GNN_Bk.json`. I voli vanno nel blocco indicato (`"blocco"`), o in quello in cui
   cade l'orario di decollo. Test: `script/test/prova_blocchi.py`.
- Danni (README, Perdite): vita < 70% -> fermo il blocco dopo; < 30% -> anche quello successivo.
- JSON trasforma le chiavi intere delle tabelle della missione in stringhe: ricaricarle con
  `chiavi_int` prima di rimetterle in una missione.

## Meteo

- `script/tools/meteo.py`: regimi (sereno, variabile, perturbazione, foschia) con passaggi da un giorno
  all'altro (perturbazioni piu' frequenti con l'avanzare dell'autunno), evoluzione alba / mezzogiorno /
  pomeriggio, preset di nubi DCS 2.9 (Preset1-27, RainyPreset1-3), nebbia all'alba, polvere con vento
  dal deserto, QNH e temperatura plausibili. Una volta per giornata in `campagna/GNN/meteo.json`.
- Preparando una giornata: `python3 script/tools/meteo.py <giorno>` genera il meteo e scrive la
  previsione nella situazione pubblica (la leggono i comandanti). Il costruttore usa il momento del blocco.
- Con vento quasi assente (< 3 m/s) le navi non inseguono il vento: navigano a ovest, lontano dalla
  minaccia (`levante_navi.lua`).
- Da verificare in DCS: che le basi delle nubi scelte stiano nei limiti dei preset (l'editor potrebbe
  correggerle).

## Batterie di riserva
SAM con missione `riserva` (o nome che contiene "riserva"): `levante_iads.lua` le tiene spente e
nascoste finche' la rete non perde una batteria (richiesta emersa dagli ordini rossi del G16).

## Prova G16 blocco 1 (osservatore, 10/11/2026)

- Script caricati senza errori; la rete IADS accende e spegne gli SA-5 secondo i rilevamenti della
  rete, l'Hawk idem; navi contro vento; verifica del piazzatore: 73 veicoli corretti di pochi metri,
  Stinger Baabda senza posto valido (zona urbana: da rivedere).
- **Errore trovato**: la rete poteva spegnere il radar con un missile ancora in volo (guida persa).
  Corretto: dopo un lancio il radar resta acceso per il tempo di guida (`GUIDA`: SA-5 180 s, SA-2 90 s...).
- **Navi con regole d'ingaggio libere**: la fregata della Tarawa ha aperto il fuoco con gli Harpoon su
  Tartus e lo Slava ha risposto con 16 P-500 sulla portaerei, senza ordini. Da decidere col giocatore
  (proposta: navi difensive, attacchi navali solo se ordinati).
- SA-5 e SA-N-6 dello Slava hanno abbattuto la barriera F-14 e una CAP alte sopra il mare: il
  comandante blu ha messo orbite alte dentro portate note (proposta: controllo delle rotte).
- Con l'accelerazione del tempo DCS va in "ANTIFREEZE" (simulazione in ritardo): le prestazioni vanno
  valutate a velocita' normale.

## Missione da osservare

`python3 script/costruisci_giornata.py <giorno> <blocco> --osservatore` -> `..._OSSERVATORE.miz`: tutti i
voli all'IA (nessuno slot), mappa e viste esterne libere con etichette, briefing di entrambe le parti, e
`LEVANTE_DEBUG = true`: gli script scrivono a schermo cosa fanno (`LEVANTE.debug`). Solo su richiesta
del giocatore, come le missioni di test a carte scoperte.

## Diagnosi dei problemi in DCS

- Chiedere `Saved Games\DCS\Logs\dcs.log` **prima di riavviare DCS** (al riavvio diventa `dcs.log.old`).
- Missione che si pianta al caricamento: cercare `ALERT`/`GUI Error` e `traceback` nelle ultime righe.
- Se il log non basta: versioni ridotte della missione (senza aerei / terra / navi / disegni) per isolare la parte.

## Controlli prima di consegnare una missione

0. `python3 script/tools/verifica_miz.py <missione.miz>` senza errori.
1. Test Lua simulati: `script/test/prova_piazzatore.py`, `script/test/prova_navi.py` (e gli altri pertinenti).
2. `python3 script/tools/carichi.py` senza errori.
3. ID di gruppi e unita' unici; nomi di gruppo unici; nominativi radio validi per paese.
4. Nessuna coppia di gruppi di terra con veicoli sotto 60 m (salvo protezioni volute).
5. Navi da aviazione con mare aperto contro vento; portaerei nella zona navale USA.
6. Nessun avviso `PRESTAZIONI:` dal costruttore (o motivato al giocatore).
7. Rileggere questo file.
