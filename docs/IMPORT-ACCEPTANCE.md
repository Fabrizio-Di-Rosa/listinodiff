# ListinoDiff — Accettazione importazione CSV / XLSX / PDF

## Fixture sintetiche (nessun dato aziendale)
Due listini con colonne `SKU;Descrizione;Prezzo;Quantita`:

Precedente:
- A100;Vite;10;100
- B200;Bullone;25;60
- C300;Rondella;4.5;80
- D400;Dado;12;40
- F600;Cerniera;8;15

Aggiornato:
- A100;Vite;12;90
- B200;Bullone;40;60
- C300;Rondella;4.5;0
- E500;Molla;6;20
- E500;Molla duplicata;6;20
- F600;Cerniera rinforzata;8;15

## Risultato atteso a soglia 15%
7 anomalie: A100 +20%, B200 +60%, C300 scorta azzerata, D400 scomparso, E500 nuovo, E500 duplicato, F600 descrizione modificata.

## Casi minimi prima del merge
1. CSV + CSV: 7 anomalie, 5 SKU precedenti, 5 SKU aggiornati.
2. XLSX + XLSX: stessi risultati.
3. CSV + XLSX: stessi risultati.
4. PDF digitale tabellare + PDF digitale tabellare: stessi risultati **solo se l'estrazione è verificabile**.
5. PDF scansionato: rifiuto chiaro.
6. PDF con righe incomplete, intestazioni ambigue o colonne disallineate: rifiuto.
7. XLSX senza SKU: rifiuto.
8. File sopra 15 MB: rifiuto.
9. Confronto con dati di esempio senza librerie esterne: 7 anomalie.

## Vincoli di rilascio
- I test sui campioni e sui formati misti vanno **eseguiti in browser**, non dedotti dalla sola lettura del codice.
- Le librerie da CDN vanno valutate, versionate e preferibilmente ospitate localmente con integrità verificata.
- Prima del merge aggiornare homepage, privacy e istruzioni secondo le capacità effettivamente collaudate.
- Non pubblicare il supporto PDF se non supera i controlli: il risultato deve essere affidabile, non solo plausibile.
- Non modificare Caddy né gli altri servizi della VPS.
