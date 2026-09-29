# VA Digital Hub 5.7

Versione di consolidamento con Agenda e Contabilità come moduli autonomi ma collegati allo stesso database di Clienti & Progetti.

- Home: clic sul numero del giorno apre Agenda in vista Giorno.
- Agenda Giorno: fasce 07:00–20:00 e inserimento appuntamento sullo slot.
- Ogni appuntamento mostra link distinti alla scheda Cliente e alla scheda Progetto.
- Agenda e Contabilità sono voci separate nella sidebar.
- I drawer si chiudono dopo il salvataggio con rerun completo dell'app.
- Database SQLite e dati della 5.6 conservati.

## Versione 5.7.2
- Calendario Home navigabile: clic sul numero del giorno apre Agenda direttamente in vista Giorno.
- Sincronizzazione robusta della data/vista con `session_state`, anche se Agenda era già stata aperta.
- La giornata mantiene fasce orarie 07:00–20:00 e collegamenti Cliente/Progetto dagli appuntamenti.

## Versione 5.8 - CRUD completo
- Modifica ed eliminazione con conferma per appuntamenti.
- Modifica ed eliminazione per pagamenti e costi.
- Modifica/eliminazione per attività.
- Eliminazione protetta di clienti e progetti con controllo dei record collegati.
- Gestione modifica/elimina di assistenze e note cliente.
- Gestione modifica/elimina per dispositivi, software e licenze.
- Eliminazione protetta delle opportunità CRM quando esistono preventivi/follow-up collegati.
- Tutti i dati restano nel database SQLite esistente.

## 5.8.2
- Calendario Home nuovamente compatto, con celle uniformi e cliccabili.
- Click sulla cella: apertura diretta Agenda > Giorno sulla data selezionata.
- Eventi principali mostrati direttamente nella cella.
- Verificati i target dei pulsanti Dashboard/Sidebar/accessi rapidi.
- Rimossi i rerun manuali ridondanti dalla navigazione principale per ridurre i doppi refresh.


## Versione 5.9 – VA Digital UI
Interfaccia riallineata al design system VA Digital: navy #06223d, accento azzurro, card/pannelli/input/tabelle/drawer/calendario uniformati. Il file assets/core_reference.css conserva il CSS di riferimento fornito.

## Versione 6.0 - Centro operativo
- Ricerca globale di clienti, progetti, opportunità e documenti dalla Dashboard.
- Coda di lavoro unica con scaduti, attività di oggi, appuntamenti, incassi e follow-up.
- Agenda con comandi Precedente, Oggi e Successivo coerenti con la vista scelta.
- Contabilità organizzata in Scadenziario, Prima nota, Flusso mensile e Per cliente.
- Collegamenti diretti tra scadenze, schede cliente e schede progetto.
- I dati continuano a risiedere nel database SQLite locale esistente.
- Utility Password: generatore deterministico Argon2id integrato, senza salvataggio della chiave principale o dell'output.
