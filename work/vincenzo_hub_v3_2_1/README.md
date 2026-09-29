# VA Digital Hub 5.0

Gestionale Streamlit modulare per clienti, commesse, attività, pagamenti, agenda, documenti, GIS, tecnologia e analisi.

## Avvio

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

I dati sono salvati nel database locale SQLite `data/va_hub.sqlite3`. Al primo avvio, gli eventuali dati presenti in `data/workspace.json` vengono importati automaticamente. I file caricati dalla sezione Documenti sono conservati in `data/uploads`.

La sezione Documenti permette di consultare i modelli del kit commerciale VA Digital, compilarne i campi direttamente dalla dashboard e scaricare il nuovo file Word. I documenti generati sono salvati in `data/generated` e registrati automaticamente nell'archivio locale.

La sezione Clienti & Progetti comprende scheda cliente completa, commesse, attività, scadenzario pagamenti, prima nota gestionale e calendario appuntamenti. La prima nota serve al controllo dell'attività e non sostituisce la contabilità fiscale.

## Accesso riservato

In locale la dashboard può essere usata senza password. Prima di esporla su una rete o su Internet, configurare la variabile d'ambiente:

```powershell
$env:VA_HUB_PASSWORD = "una-password-lunga-e-unica"
python -m streamlit run app.py
```

Per una pubblicazione stabile è consigliato aggiungere autenticazione tramite reverse proxy o provider di identità, HTTPS e backup della cartella `data`.

## Struttura

- `app.py`: shell della dashboard e navigazione.
- `assets/va_style.css`: interfaccia coordinata VA Digital.
- `core/storage.py`: archivio SQLite locale, migrazione dati, backup e caricamenti.
- `modules.json`: registro dei moduli.
- `modules/<id>/module.py`: implementazione indipendente di ogni modulo.
- `settings/module_manager.py`: gestione moduli.

Ogni modulo interno deve esporre:

```python
def render(module):
    ...
```
