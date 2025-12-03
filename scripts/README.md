# Quality Gate Script

Script automatico per eseguire l'analisi della complessità ciclomatica e generare report HTML.

## Utilizzo

### Metodo 1: Make (consigliato)

```bash
make quality-gate
```

### Metodo 2: Esecuzione diretta

```bash
./scripts/quality-gate.sh
```

## Cosa fa lo script

1. **Esegue ESLint** con le regole di complessità configurate
2. **Analizza i risultati** conteggiando:
   - Violazioni di complessità (CCN > 15)
   - Errori totali
   - Warning totali
3. **Determina lo stato** del Quality Gate:
   - ✅ **PASSED**: Nessuna violazione di complessità
   - ❌ **FAILED**: Una o più violazioni di complessità
4. **Genera report HTML** con:
   - Dashboard visuale dello stato
   - Metriche dettagliate
   - Tabella delle violazioni
   - Output completo di ESLint
5. **Apre il report** nel browser automaticamente (se disponibile)

## Output

I report vengono salvati in:

```
frontend/quality-gate-report/
├── report_2025-12-01_18-45-39.html  # Report con timestamp
├── report_2025-12-01_18-46-14.html
└── latest.html                       # Symlink all'ultimo report
```

### Aprire un report manualmente

```bash
# Linux
xdg-open frontend/quality-gate-report/latest.html

# macOS
open frontend/quality-gate-report/latest.html

# Windows
start frontend/quality-gate-report/latest.html
```

## Configurazione

### Soglia di complessità

La soglia è configurata nel file `frontend/eslint.config.mjs`:

```javascript
rules: {
  'complexity': ['error', { max: 15 }]
}
```

Per modificare la soglia, cambia il valore `max` nel file di configurazione ESLint.

### Personalizzazione script

Variabili configurabili in `quality-gate.sh`:

```bash
MAX_COMPLEXITY=15        # Soglia di complessità
FRONTEND_DIR="..."       # Directory frontend
REPORT_DIR="..."         # Directory per i report
```

## Interpretazione risultati

### Status Badge

- 🟢 **PASSED**: Tutti i componenti rispettano la soglia CCN ≤ 15
- 🔴 **FAILED**: Uno o più componenti superano la soglia

### Metriche

- **Complexity Violations**: Numero di funzioni/componenti che superano la soglia
- **Total Errors**: Errori ESLint totali (include complessità + altri errori)
- **Total Warnings**: Warning ESLint (import inutilizzati, ecc.)
- **Total Issues**: Somma di errori e warning

### Exit Code

Lo script restituisce:

- `0` se Quality Gate passa (nessuna violazione di complessità)
- `1` se Quality Gate fallisce (una o più violazioni)

Questo permette di usarlo in CI/CD:

```bash
./scripts/quality-gate.sh || exit 1
```

## Integrazione CI/CD

### GitHub Actions

```yaml
- name: Quality Gate
  run: make quality-gate

- name: Upload Report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: quality-gate-report
    path: frontend/quality-gate-report/latest.html
```

### GitLab CI

```yaml
quality-gate:
  script:
    - make quality-gate
  artifacts:
    paths:
      - frontend/quality-gate-report/
    when: always
```

## Troubleshooting

### Lo script non si avvia

Verifica i permessi:

```bash
chmod +x scripts/quality-gate.sh
```

### Il report non si apre nel browser

Apri manualmente:

```bash
xdg-open frontend/quality-gate-report/latest.html
```

### ESLint non trovato

Installa le dipendenze:

```bash
cd frontend && npm install
```

## Feature del report HTML

- 📊 **Dashboard responsive** con stato visuale
- 📈 **Metriche in tempo reale** con card colorate
- 📋 **Tabella violazioni** con file, linea e messaggio
- 🎨 **Design moderno** con gradiente e animazioni
- 📱 **Mobile-friendly** con layout adattivo
- 🌙 **Output ESLint** formattato con syntax highlighting
- 🔗 **Cronologia report** con timestamp

## Esempi di output

### Quality Gate PASSED

```
========================================
  Quality Gate - Complexity Analysis
========================================

Running ESLint with complexity analysis...

========================================
  Results
========================================

Status: PASSED
Complexity Violations: 0
Total Errors: 2
Total Warnings: 19
Total Problems: 21

Report generated: .../report_2025-12-01_18-46-14.html
Latest report: .../latest.html
```

### Quality Gate FAILED

```
========================================
  Quality Gate - Complexity Analysis
========================================

Running ESLint with complexity analysis...

========================================
  Results
========================================

Status: FAILED
Complexity Violations: 3
Total Errors: 5
Total Warnings: 19
Total Problems: 24

Report generated: .../report_2025-12-01_18-46-14.html
Latest report: .../latest.html
```
