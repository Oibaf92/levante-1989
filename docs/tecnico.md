# Fuoco sul Levante 1989 — note tecniche

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
script/     motore della campagna (Python e Lua)
blu/        🔒 riservato al comandante blu — non aprire
rosso/      🔒 riservato al comandante rosso — non aprire
```

## 🗺️ Mappa e intelligence di partenza
- **Nessuna scritta sulla mappa**: ogni installazione è un simbolo (quadrato = base aerea,
  quadrato con croce = elicotteri, rombo = navale, pentagono = forze di terra; SAM: doppio
  triangolo = SA-2, triangolo rovesciato = SA-3, esagono = SA-6, cerchio con
  croce = SA-8, triangolo con barra = Hawk; il colore indica la fazione). La legenda è disegnata
  in mare a sud di Cipro; nomi e velivoli sono sulla tavoletta INTEL
  (`script/tools/simboli.py`, `legenda.py`).
- **Strato Common** (visibile a tutti): confini, fazioni e legenda (`script/tools/confini.py`).
- **Strato Blue / Red** (ognuno visibile solo alla propria parte): basi permanenti e siti
  antiaerei fissi noti al 2 ottobre 1989, come li stima ciascuna parte
  (`script/tools/intel.py`). È la situazione di pace fissata dall'arbitro: i comandanti
  possono spostare i sistemi mobili, quindi in guerra la mappa può essere superata.

## 🌍 Banca dati del terreno (`campagna/terreno/`)
- `rilievo_terreno.txt`: rilievo fatto in DCS (missione R00): quota, pendenza, superficie,
  edifici entro 400 m, distanza dalla strada; griglia da 2 km su tutta l'area e da 1 km su
  Libano, Golan e Siria occidentale.
- `vegetazione_250m.npz`: vegetazione ricavata dagli screenshot SAT del Mission Editor
  (missione R01, crocette di calibrazione), copre la fascia costiera e montuosa; il deserto
  interno, senza alberi, non e' rilevato.
- `terreno_completo.npz`: le due cose unite, usate dal piazzatore delle unita'.
- Strumenti: `script/tools/rilievo.py`, `foreste.py`, `crea_mappa_foreste.py`, `mappe_rilievo.py`.

## 🎯 Piazzatore delle unita'
I comandanti esprimono intenzioni ("SA-6 a protezione di Rayak, copertura verso ovest");
`script/tools/piazzatore.py` sceglie il punto sul terreno rilevato (pendenza, edifici,
vegetazione, strade, visibilita' radar) e dispone i veicoli secondo lo schema del sistema.
In gioco `levante_piazzatore.lua` verifica ogni veicolo e, con un segno F10 **SPOSTA**,
trasferisce una batteria nella posizione alternativa successiva. Prova: missione P00.

## Alberi e verifiche ravvicinate
La vegetazione da satellite (80 m) non vede frutteti e filari piccoli. Per una batteria in zona
agricola o costiera: screenshot ravvicinato dal Mission Editor (vista SAT, zoom massimo, scala ~200 ft)
acquisito con `script/tools/aggiungi_verifiche.py <missione.miz> <screenshot...>` (alberi in
`campagna/terreno/alberi_noti.npz`). Dopo ogni volo `script/tools/importa_stato.py <stato>` importa i
segni BOSCO/SPOSTA come zone da evitare. Nella missione `levante_piazzatore.lua` verifica ogni veicolo
all'avvio (tabella `LEVANTE_PIAZZAMENTI`).
