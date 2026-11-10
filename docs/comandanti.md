# Come l'arbitro prepara i comandanti

Ogni comandante lavora in un agente separato (vedi CLAUDE.md, separazione delle informazioni).

## Cosa riceve il comandante di una parte (e nient'altro)
1. `README.md` (scenario, regole, intensita', perdite, CSAR, nomi dei voli in inglese).
2. Lo stato pubblico del blocco (`campagna/GNN/situazione_pubblica.md`, `parametri.json`,
   `formato_ordini.md`).
3. Il proprio rapporto intel del blocco.
4. La propria cartella (`blu/` oppure `rosso/`), **compresa la propria `dottrina.md`, da leggere
   per prima**, il diario e gli ordini precedenti.

## Istruzioni da dare all'agente
- Applicare la propria dottrina; se se ne discosta, spiegarlo nel diario.
- Rispettare i limiti del blocco (voli, **aerei in volo contemporaneamente: 14 per parte, AWACS e
  cisterne compresi**, gruppi di terra), i
  carichi ammessi (`parametri.json`) e l'era 1989.
- Nomi dei voli in inglese, una parola breve e univoca.
- Scrivere gli ordini nel formato richiesto e aggiornare il diario.
- Non leggere mai la cartella dell'altra parte.

## Dottrine
- `blu/dottrina.md` e `rosso/dottrina.md`: principi concordati con il giocatore. Si aggiornano solo
  su sua indicazione; ogni modifica va anche annotata in `docs/lezioni.md` (senza copiarne il
  contenuto: le dottrine restano riservate a ciascuna parte).
