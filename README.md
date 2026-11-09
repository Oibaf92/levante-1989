# 🔥 Fuoco sul Levante — autunno 1989

Campagna dinamica per **DCS World**, mappa **Syria**, giocatore singolo.
Due comandanti IA separati (blu e rosso) si affrontano giorno dopo giorno;
il giocatore vola a scelta con una delle due parti.

## Situazione
- **Libano**: l'enclave cristiana del generale Aoun (Jounieh – Beirut Est) resiste alle
  forze siriane. Gli USA sbarcano per evacuare i civili e ne diventano i protettori.
- **Siria**: sostenuta da un contingente sovietico; la flotta di Tartus è in allerta.
- **Neutrali**:
  - **Israele**: chi entra nel suo spazio aereo provoca l'intervento della sua aviazione
  - **Giordania**
  - **Turchia**: NATO, concede Incirlik al blu; attaccarla è un'escalation vietata
  - **Cipro**: Akrotiri come base di dirottamento per il blu

## 🔵 Blu — forze statunitensi
| Componente | Base | Mezzi |
|---|---|---|
| CVN-71 Roosevelt + ala imbarcata | Mediterraneo orientale | ✈️ F-14A/B ×20, ✈️ F/A-18C ×20, A-6E ×14, E-2C ×4, S-3B tanker ×6 |
| Scorta della portaerei | | 2 Ticonderoga, 2 Perry |
| LHA-1 Tarawa | Al largo di Jounieh | 🚁 AH-64 ×8, 🚁 CH-47 ×6, AV-8B ×6 (AI) |
| Distaccamento USAF | Incirlik | ✈️ F-4E ×12, KC-135 ×2, E-3A ×1 |
| Testa di ponte dei Marines | Jounieh | LAV-25, AAV-7, M60, SAM Hawk, Stinger |
| Alleati libanesi (Aoun) | Enclave | Fanteria leggera, M113, artiglieria |

## 🔴 Rosso — Siria + contingente sovietico
| Componente | Mezzi |
|---|---|
| Aviazione siriana | ✈️ MiG-29A ×16, MiG-21bis ×24, MiG-23MLD ×24, MiG-25PD ×8, Su-22M4 ×16, Su-24 ×8, 🚁 Mi-24 ×12, 🚁 Mi-8 ×16 |
| Contingente aereo sovietico | ✈️ MiG-29A ×12, ✈️ Su-25 ×12, Tu-22M3 ×8 (da est, fuori mappa), A-50 ×1 |
| Flotta sovietica a Tartus | 1 Slava, 2 Krivak II, 1 Molniya, 1 sottomarino Kilo |
| Difesa aerea integrata | SA-5 ×2, SA-2 ×6, SA-3 ×6, SA-6 ×8, SA-8 ×6, SA-9/13, ZSU-23-4, radar di scoperta |
| Forze di terra (Bekaa e Libano) | 2 divisioni corazzate (T-72, T-62, BMP), artiglieria, BM-21, brigata Scud-B |

✈️🚁 = postazioni pilotabili dal giocatore.
**Le risorse sono limitate**: ogni perdita è permanente; i rinforzi arrivano col contagocce.

## ⚖️ Regole del 1989
- **Blu**: niente AIM-120, armi GPS o pod di puntamento. Bombe a guida laser solo
  con A-6E/TRAM. Ammessi AIM-54, AIM-7, HARM, Harpoon, Maverick, Shrike.
- **Rosso**: niente R-77 né SA-10/11/15 all'inizio. Possono arrivare come rinforzo
  sovietico più avanti.

## 🏆 Condizioni di vittoria
- **Blu**: l'enclave resiste e la difesa aerea siriana è smantellata, fino al cessate il
  fuoco imposto dalle perdite siriane.
- **Rosso**: l'enclave cade, oppure la portaerei è messa fuori uso, oppure le perdite
  USA diventano politicamente insostenibili.

## 🔄 Ciclo di gioco
1. L'arbitro consegna il `.miz` della giornata in `missioni/`.
2. Il giocatore sceglie parte e ruolo e vola la sortita.
3. A fine missione lo script salva lo stato in `Saved Games\DCS\Levante1989\`.
4. Il giocatore carica i file di stato (più eventuali `dcs.log` e Tacview).
5. Ogni comandante riceve **solo il proprio rapporto intel** e decide la giornata seguente.

## 🛠️ Preparazione del PC (una volta sola)
In `<cartella DCS>\Scripts\MissionScripting.lua` commentare solo `io` e `lfs`:
```lua
do
	sanitizeModule('os')
	--sanitizeModule('io')
	--sanitizeModule('lfs')
	_G['require'] = nil
	_G['loadlib'] = nil
	_G['package'] = nil
end
```
Ogni aggiornamento o riparazione di DCS annulla la modifica: va rifatta.
Non aprire missioni scaricate di cui non ci si fida.

## 📁 Struttura
```
campagna/   stato condiviso (giorno di guerra, perdite, risorse)
missioni/   .miz di ogni giornata
script/     motore della campagna (Lua, MOOSE)
blu/        🔒 riservato al comandante blu — non aprire
rosso/      🔒 riservato al comandante rosso — non aprire
```

## 🗺️ Mappa e intelligence di partenza
- **Strato Common** (visibile a tutti): confini e fazioni (`script/tools/confini.py`).
- **Strato Blue / Red** (ognuno visibile solo alla propria parte): basi permanenti e siti
  antiaerei fissi noti al 2 ottobre 1989, come li stima ciascuna parte
  (`script/tools/intel.py`). È la situazione di pace fissata dall'arbitro: i comandanti
  possono spostare i sistemi mobili, quindi in guerra la mappa può essere superata.
