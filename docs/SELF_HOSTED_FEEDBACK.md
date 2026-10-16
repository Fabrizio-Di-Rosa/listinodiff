# ListinoDiff — migrazione questionario proprietario (staging)

## Stato
Codice sorgente pronto per revisione; **non distribuito sulla VPS**. La homepage pubblica continua a collegarsi a Tally fino al collaudo completo.

## Architettura
- `interesse.html`: questionario accessibile, quattro domande, email e consenso facoltativi.
- `backend/app.py`: API Python standard library, endpoint `POST /feedback` e `GET /healthz`.
- SQLite in `/opt/antefide/listinodiff/data/feedback.sqlite3`, non pubblico.
- Nginx statico invariato, Caddy deve inoltrare solo `/api/feedback` (riscrivendo il percorso in `/feedback`) e opzionalmente `/api/healthz`.
- Nessuna API per leggere/esportare le risposte pubblicamente.

## Vincoli prima del go-live
1. Verificare la rete Docker e i permessi di scrittura della directory data per l'utente non privilegiato del container.
2. Testare `python -m unittest discover -s backend -p 'test_*.py'` dalla directory `backend`, oppure `cd backend && python -m unittest`.
3. Eseguire test end-to-end di invio e persistenza in SQLite, inclusi consenso, errori, limite richieste e riavvio container.
4. Predisporre pulizia periodica autonoma dei dati dopo 90 giorni (la pulizia su avvio/invio da sola non garantisce il limite temporale).
5. Proteggere backup SQLite con accesso ristretto, cifratura ove applicabile e cancellazione coerente con la retention.
6. Riesaminare l'informativa GDPR (titolare, base giuridica, destinatari, hosting, log tecnici e tempi) e aggiornare il testo prima del go-live.
7. Aggiornare link homepage a `./interesse.html`, verificare invio reale, poi dismettere Tally e disabilitare GitHub Pages.

## Avvertenza
Il limite richieste nell'app usa l'indirizzo IP della connessione al backend: dietro Caddy tutti gli utenti possono apparire con lo stesso IP. Configurare rate limiting all'edge o un inoltro autenticato di IP verificato prima di mettere il form in produzione. Non fidarsi di header IP inviati direttamente dal client.
