# juridikbok.se Harvester – Installationsguide (macOS)

## Förutsättningar

Du behöver Python 3.10 eller nyare. Kontrollera i Terminal:

```bash
python3 --version
```

Om du inte har Python, installera via Homebrew:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python
```

---

## Steg 1: Skapa projektmapp

```bash
mkdir -p ~/juridikbok_harvester
cd ~/juridikbok_harvester
```

## Steg 2: Lägg in skriptet

Kopiera `harvester_v2.py` (som du laddat ner från Claude) till mappen:

```bash
cp ~/Downloads/harvester_v2.py ~/juridikbok_harvester/harvester.py
```

## Steg 3: Installera beroenden

```bash
pip3 install requests beautifulsoup4
```

Om du får ett felmeddelande om "externally managed environment" (vanligt i nyare macOS):

```bash
pip3 install --user requests beautifulsoup4
```

Eller skapa en virtuell miljö (renare lösning):

```bash
python3 -m venv venv
source venv/bin/activate
pip install requests beautifulsoup4
```

> Om du använder venv måste du köra `source venv/bin/activate` varje gång du öppnar ett nytt terminalfönster.

## Steg 4: Testkörning (5 böcker)

```bash
cd ~/juridikbok_harvester
python3 harvester.py --max-books 5 --output-dir ./test
```

Du bör se ungefär:

```
▶ Fas 1a: Crawlar juridikbok.se boklista...
  Hittade 902 böcker i katalogen.
  (Begränsat till 5 böcker)
▶ Fas 1b: Hämtar detaljerad metadata...
▶ Fas 1c: Laddar ner PDF:er...
  ⬇ [1/5] 2003 - avh - Bakardjieva Engelbrekt - Fair trading law in flux.pdf...
    ✓ 2.3 MB
...
▶ Fas 2: LIBRIS-anrikning...
  [1/5] LIBRIS: Fair trading law in flux?...
    ✓ SAB: Oeaae-c
```

Kontrollera resultatet:

```bash
ls test/pdf/
cat test/catalog.json | python3 -m json.tool | head -50
```

## Steg 5: Full körning

När testet ser bra ut – kör hela katalogen (~900 böcker, uppskattningsvis 5–15 GB, tar 1–3 timmar):

```bash
python3 harvester.py --output-dir ./bibliotek
```

Skriptet har resume-funktion. Om det avbryts kan du köra samma kommando igen – redan nedladdade PDF:er hoppas över.

### Alternativ: Kör i steg

Om du vill ha mer kontroll:

```bash
# Steg A: Bara crawla metadata (inga nedladdningar, tar ~30 min)
python3 harvester.py --crawl-only --output-dir ./bibliotek

# Steg B: Ladda ner PDF:er (kräver catalog.json från steg A)
python3 harvester.py --download-only --output-dir ./bibliotek

# Steg C: LIBRIS-anrikning (kräver catalog.json)
python3 harvester.py --enrich-only --output-dir ./bibliotek
```

## Steg 6: Flytta till Google Drive

Kopiera PDF-mappen till din Drive-synkmapp:

```bash
cp -r ./bibliotek/pdf/ ~/Google\ Drive/Min\ enhet/Juridiskt\ bibliotek/juridikbok.se/
cp ./bibliotek/catalog.json ~/Google\ Drive/Min\ enhet/Juridiskt\ bibliotek/juridikbok.se/
```

Anpassa sökvägen efter din Drive-mappstruktur.

---

## Filstruktur efter körning

```
bibliotek/
├── catalog.json          ← All metadata (citeringar, LIBRIS, ämnesord)
└── pdf/
    ├── 1956 - bok - Rodhe - Obligationsratt.pdf
    ├── 1995 - bok - Tiberg, Lennhammer - Skuldebrev, vaexel och check - 7uppl.pdf
    ├── 2023 - avh - Goethlin - Prioritet och avtal.pdf
    └── ...
```

## catalog.json – viktiga fält

Varje bok i `catalog.json` har bland annat:

| Fält | Exempel | Beskrivning |
|------|---------|-------------|
| `citation_hd` | `Knut Rodhe, Obligationsrätt, 1956` | HD:s referensformat |
| `short_cite` | `Rodhe, Obligationsrätt` | Kortform för löptext |
| `aliases` | `[]` | Tom lista – fyll i manuellt vid behov |
| `authors_parsed` | `[{"first": "Knut", "last": "Rodhe"}]` | Förnamn/efternamn separat |
| `classification.sab` | `Oeaa-c` | SAB-kod från LIBRIS |
| `subjects_libris` | `[{"term": "Obligationsrätt"}]` | Ämnesord från LIBRIS |
| `filename` | `1956 - bok - Rodhe - Obligationsratt.pdf` | Filnamn i pdf-mappen |

---

## Felsökning

**"ModuleNotFoundError: No module named 'requests'"**
→ Kör `pip3 install requests beautifulsoup4` igen, eller aktivera din venv.

**Skriptet stannar mitt i**
→ Kör samma kommando igen. Resume-funktionen hoppar över redan nedladdade PDF:er.

**"Connection error" eller timeout**
→ Öka fördröjningen: `python3 harvester.py --delay 3.0`

**Vill köra i bakgrunden**
→ Använd `nohup` så att det fortsätter om du stänger Terminal:
```bash
nohup python3 harvester.py --output-dir ./bibliotek > harvester.log 2>&1 &
tail -f harvester.log
```
