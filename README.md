# Juridikbok Harvester

Ett Python-verktyg för systematisk harvesting av juridisk litteratur från juridikbok.se, med automatisk metadata-anrikning via LIBRIS och citatformatering enligt svensk HD-standard.

## ⚠️ VIKTIGT: Juridiska Villkor

**Läs [LEGAL_NOTICE.md](LEGAL_NOTICE.md) innan användning.**

Allt material från juridikbok.se är licensierat under **CC BY-NC 4.0** vilket innebär:
- ✅ Icke-kommersiell forskning och utbildning
- ❌ Kommersiell användning eller vidaredistribution
- **Alltid** korrekt attribution till författare

Detta verktyg är avsett för Access to Justice-forskning, INTE kommersiell exploatering.

## Syfte

Detta verktyg skapades som del av ett Access to Justice-projekt för att:
- Systematiskt dokumentera tillgänglig juridisk litteratur på svenska
- Generera korrekt formaterade HD-standardcitat
- Anrika metadata med ämnesord och klassifikationskoder från LIBRIS
- Möjliggöra framtida AI-assisterad juridisk analys

## Funktioner

- ✅ Crawlar juridikbok.se för tillgängliga juridiska verk
- ✅ Laddar ner PDF-filer med respekt för CC BY-NC 4.0-licensiering
- ✅ Extraherar metadata (författare, titel, år, upplaga, typ)
- ✅ Genererar HD-standardcitat: "Förnamn Efternamn, Titel, X uppl. År"
- ✅ Skapar kortcitat för referenshantering
- ✅ LIBRIS-integration för ämnesord och SAB-klassifikation
- ✅ Filnamnsformat: `ÅÅÅÅ - typ - författare - titel - upplaga.pdf`

## Installation

### Förutsättningar
- Python 3.8 eller senare
- macOS, Linux eller Windows

### Steg-för-steg installation (macOS)

1. **Klona repositoryt**
```bash
git clone https://github.com/eliassondavid/juridikbok-harvester.git
cd juridikbok-harvester
```

2. **Skapa virtuell miljö**
```bash
python3 -m venv venv
source venv/bin/activate  # På Windows: venv\Scripts\activate
```

3. **Installera dependencies**
```bash
pip install -r requirements.txt
```

## Användning

### Grundläggande harvesting

```bash
python harvester.py
```

Detta kommer att:
1. Crawla juridikbok.se efter tillgängliga verk
2. Ladda ner PDF-filer till `downloads/`
3. Generera metadata i `metadata.json`
4. Skapa filnamn enligt standardformat

### Anpassningsalternativ

Se konfiguration i `harvester.py` för:
- Output-kataloger
- Metadata-format
- LIBRIS-integrationsinställningar
- Rate limiting för crawling

## Filnamnsformat

Genererade filer följer formatet:
```
ÅÅÅÅ - typ - författare - titel - upplaga.pdf
```

Exempel:
```
2020 - bok - Christina Ramberg - Köplagen - 4 uppl.pdf
2018 - avh - Anders Victorin - Sakrätt och Inskrivning - 1 uppl.pdf
```

## HD-citatformat

Verktyget genererar citat enligt Högsta domstolens referensstil:

**Standard:**
```
Christina Ramberg, Köplagen, 4 uppl. 2020
```

**Kortcitat:**
```
Ramberg (2020)
```

**Specialfall:**
- Första upplagan: Inget upplagetal anges (följer HD:s praxis)
- Avhandlingar: Ingen särskild markering (HD behandlar som vanliga böcker)
- Flera författare: Samtliga namn inkluderas

## LIBRIS-integration

För varje verk söker verktyget automatiskt i LIBRIS-katalogen för att hämta:
- SAB-klassifikationskoder
- Ämnesord (kontrollerade termer)
- ISBN
- Alternativa titlar/alias

## Licensiering och Användarvillkor

### Juridikbok.se CC BY-NC 4.0 Licens

**VIKTIGT:** Allt innehåll från juridikbok.se är licensierat under Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).

**✅ Tillåten användning:**
- Ladda ner och lagra på egen dator för forsknings-/utbildningssyfte
- Citera med korrekt källhänvisning till författare och verk
- Använda i icke-kommersiellt undervisningsmaterial eller kompendier
- Metadata-extrahering och systematisk katalogisering
- Dela genom länkar till juridikbok.se (föredraget framför fildelning)
- Kopiera till självkostnadspris

**❌ INTE tillåten användning:**
- Kommersiell återutgivning eller försäljning
- Vidaredistribution av PDF-filer utan korrekt attribution
- Användning i kommersiella AI-system utan särskilt tillstånd
- Kommersiell försäljning av kompendier innehållande dessa texter
- Användning utan att ange upphovsman/författare

### Detta verktygs licensiering

**Koden** i detta repo är licensierad under MIT License (se LICENSE-fil).

**Nedladdat innehåll** från juridikbok.se förblir under CC BY-NC 4.0 och:
- Får INTE inkluderas i detta Git-repository (se .gitignore)
- Får INTE vidaredistribueras kommersiellt
- Måste ALLTID åtföljas av korrekt författar-attribution
- Är avsett för personligt forsknings-/utbildningsbruk

### Ansvarsfullt bruk

**Använd detta verktyg endast för:**
- Icke-kommersiell juridisk forskning
- Utbildningsändamål
- Access to Justice-initiativ
- Personlig kunskapsuppbyggnad

**Undvik:**
- Massiv harvesting som belastar juridikbok.se:s servrar
- Kommersiell exploatering av nedladdat material
- Vidaredistribution utan tillstånd
- AI-träning för kommersiella system (kräver särskild överenskommelse)

**Vid osäkerhet:** Kontakta Stiftelsen för juridisk litteratur på nätet (STJL) via juridikbok.se

**Använd verktyget ansvarsfullt och respektera upphovsrätt.**

## Projektstruktur

```
juridikbok-harvester/
├── harvester.py           # Huvudskript
├── requirements.txt       # Python dependencies
├── README.md             # Projektdokumentation
├── LICENSE               # MIT License för koden
├── LEGAL_NOTICE.md       # VIKTIGT: Juridiska villkor och användaransvar
├── CONTRIBUTING.md       # Bidragsriktlinjer
├── .gitignore           # Git-exkluderingar
└── downloads/           # Nedladdade PDF-filer (skapas automatiskt, INTE i Git)
```

**⚠️ LÄS LEGAL_NOTICE.md INNAN ANVÄNDNING**

## Teknisk dokumentation

### Dependencies
- `requests` - HTTP-förfrågningar
- `beautifulsoup4` - HTML-parsing
- `lxml` - XML-parser för LIBRIS
- `urllib3` - URL-hantering

### Rate Limiting
Verktyget inkluderar rate limiting för att:
- Respektera juridikbok.se:s serverresurser
- Undvika att blockeras av anti-scraping-mekanismer
- Möjliggöra säker harvesting av ~900 verk

## Framtida utveckling

Planerade funktioner:
- [ ] Google Drive-integration för automatisk uppladdning
- [ ] Sidmappning för citatreferenser
- [ ] Deduplikering mot befintlig samling
- [ ] Progress tracking med resumption vid avbrott
- [ ] Export till BibTeX/RIS-format
- [ ] Integration med juridiskt AI-projekt

## Bidrag

Detta är ett forskningsprojekt inom Access to Justice. För frågor eller förslag:
- Skapa ett issue på GitHub
- Kontakta: David Eliasson (se GitHub-profil)

## Erkännanden

Projektet utvecklades som del av Access to Justice-initiativ för att förbättra tillgången till juridisk kunskap i Sverige.

Tack till:
- juridikbok.se för tillgängliggörande av juridisk litteratur under CC BY-NC 4.0
- LIBRIS för öppen tillgång till biblioteksmetadata
- Anthropic för utvecklingsstöd

## Licens

[Välj lämplig licens - förslag: MIT License]

---

**OBS:** Detta verktyg är för forsknings- och utbildningsändamål. Respektera alltid upphovsrätt och licensvillkor.
