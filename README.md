# juridikbok-harvester

Systematiskt nedladdnings- och metadata-anrikningsverktyg för [juridikbok.se](https://www.juridikbok.se) – Sveriges öppna bibliotek för juridisk litteratur.

## Syfte

Projektet är en del av ett icke-kommersiellt **Access to Justice**-projekt som syftar till att göra svensk juridisk doktrin tillgänglig och sökbar för privatpersoner. Harvestern laddar ner PDF:er från juridikbok.se och anrikar metadata via LIBRIS för att möjliggöra citatmatchning mot rättspraxis.

## Funktioner

- **Fas 1**: Crawlar juridikbok.se:s katalog (~900 verk), extraherar metadata och laddar ner PDF:er
- **Fas 2**: Anrikar med LIBRIS-data (SAB-klassifikation, DDC, ämnesord, författarnamn)
- **HD-citeringsformat**: Genererar automatiskt referensformat enligt Högsta domstolens praxis, t.ex. `Knut Rodhe, Obligationsrätt, 1956`
- **Resume-funktion**: Redan nedladdade PDF:er hoppas över vid omstart
- **Artigt crawlande**: Konfigurerbar fördröjning mellan requests (default 1.5s)

## Snabbstart

```bash
# Installera beroenden
pip install requests beautifulsoup4

# Testkörning (5 böcker)
python src/harvester.py --max-books 5 --output-dir ./test

# Full körning (~900 böcker, 1-3 timmar)
python src/harvester.py --output-dir ./bibliotek
```

Se [docs/INSTRUKTION.md](docs/INSTRUKTION.md) för detaljerad installationsguide (macOS).

## Filnamnkonvention

Filnamn matchar svensk juridisk praxis och är optimerade för mänsklig igenkänning:

```
ÅÅÅÅ - typ - författare - titel [- Xuppl].pdf
```

| Exempel | Typ |
|---------|-----|
| `1956 - bok - Rodhe - Obligationsratt.pdf` | Monografi |
| `1995 - bok - Tiberg, Lennhammer - Skuldebrev, vaexel och check - 7uppl.pdf` | Flerfalsbok |
| `2023 - avh - Goethlin - Prioritet och avtal.pdf` | Avhandling |

## Metadata (catalog.json)

Varje verk får bl.a.:

| Fält | Exempel | Källa |
|------|---------|-------|
| `citation_hd` | `Knut Rodhe, Obligationsrätt, 1956` | Genererat (HD:s format) |
| `short_cite` | `Rodhe, Obligationsrätt` | Genererat |
| `classification.sab` | `Oeaa-c` | LIBRIS |
| `subjects_libris` | `[{"term": "Obligationsrätt"}]` | LIBRIS |
| `authors_parsed` | `[{"first": "Knut", "last": "Rodhe"}]` | juridikbok.se + LIBRIS |

## Licens

Källkoden i detta repo är licensierad under **CC BY-NC 4.0** – samma licens som verken på juridikbok.se.

Verken på juridikbok.se publiceras av **Stiftelsen för tillgängliggörande av juridisk litteratur** under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/deed.sv). De nedladdade PDF:erna får **inte** användas i kommersiella tjänster utan separat överenskommelse med stiftelsen.

## Bakgrund

Projektet grundar sig i en analys av hur Högsta domstolen (HD) refererar till juridisk doktrin. HD använder ett konsekvent format:

> *Knut Rodhe, Obligationsrätt, 1956, s. 134*

Harvestern genererar detta format automatiskt utifrån metadata, inklusive korrekt hantering av upplageangivelser (anges bara vid ≥2 uppl.) och flerfalsförfattare ("och"-konjunktion).

Se [docs/HD-CITERINGSANALYS.md](docs/HD-CITERINGSANALYS.md) för den fullständiga analysen.

## Relaterat

- [juridikbok.se](https://www.juridikbok.se) – Stiftelsens öppna bibliotek
- [LIBRIS](https://libris.kb.se) – Kungliga bibliotekets söktjänst
- [lagen.nu](https://lagen.nu) – Öppen svensk rättsinformation
