# Bidra till Juridikbok Harvester

Tack för ditt intresse att bidra till detta Access to Justice-projekt!

## Projektets syfte

Detta verktyg utvecklas för att förbättra tillgången till juridisk kunskap i Sverige genom:
- Systematisk dokumentation av tillgänglig juridisk litteratur
- Korrekt citatformatering enligt svensk domstolspraxis
- Metadata-anrikning för framtida AI-assisterad juridisk analys

## Hur du kan bidra

### Rapportera buggar

Om du hittar en bugg, skapa ett issue med:
- Tydlig beskrivning av problemet
- Steg för att återskapa buggen
- Förväntad vs. faktisk utfall
- Din miljö (OS, Python-version)

### Föreslå förbättringar

Vi välkomnar förslag på:
- Nya funktioner
- Förbättrad metadata-hantering
- Bättre LIBRIS-integration
- Optimeringar av harvesting-processen

### Kodkvalitet

Om du bidrar med kod, se till att:
- Koden följer PEP 8-riktlinjer
- Funktioner har dokumentstrings
- Felhantering finns på lämpliga ställen
- Ingen känslig information (API-nycklar, lösenord) inkluderas

### Juridiska överväganden

**KRITISKT VIKTIGT:** All harvesting måste respektera:

**CC BY-NC 4.0-licensiering för juridikbok.se-innehåll:**
- ✅ Icke-kommersiell forskning och utbildning
- ✅ Metadata-extrahering och katalogisering  
- ✅ Korrekt attribution till författare
- ❌ Kommersiell användning eller vidaredistribution
- ❌ PDF-distribution (använd länkar till juridikbok.se istället)
- ❌ Användning i kommersiella AI-system utan tillstånd

**Tekniska säkerhetsåtgärder:**
- Rimlig rate limiting (respektera servrar)
- PDF-filer får ALDRIG checkas in i Git (se .gitignore)
- Användarvarningar i dokumentation och kod
- Tydlig separation mellan kod-licens (MIT) och innehålls-licens (CC BY-NC)

**Upphovsrätt och svensk lag:**
- Följ Upphovsrättslagen (1960:729)
- Respektera författarnas moraliska rättigheter
- Vid osäkerhet - kontakta STJL via juridikbok.se

**Access to Justice-fokus:**
- Detta projekt tjänar icke-kommersiella, samhällsnyttiga syften
- Sträva efter att förbättra tillgången till juridisk kunskap
- Respektera balansen mellan öppenhet och upphovsrätt

### Pull Requests

**Före du skickar en Pull Request, säkerställ:**

✅ Kodkvalitet:
- Följer PEP 8-riktlinjer
- Funktioner har dokumentstrings
- Felhantering finns på lämpliga ställen
- Ingen känslig information (API-nycklar, lösenord) inkluderas

✅ Juridisk compliance:
- PDF-filer inkluderas INTE i commits
- Rate limiting respekteras
- Attribution-funktionalitet bevaras
- Användarvarningar om CC BY-NC finns kvar
- LEGAL_NOTICE.md uppdateras vid behov

✅ Git-workflow:
1. Forka repot
2. Skapa en feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit dina ändringar (`git commit -m 'Add some AmazingFeature'`)
4. Push till branchen (`git push origin feature/AmazingFeature`)
5. Öppna en Pull Request

### Dokumentation

Hjälp oss förbättra dokumentationen:
- README-förtydliganden
- Kodkommentarer
- Användningsexempel
- Installationsinstruktioner för olika OS

## Kodstruktur

```python
# Exempel på god kodstruktur med dokumentstrings

def generate_hd_citation(author_first: str, author_last: str, 
                         title: str, edition: int, year: int) -> str:
    """
    Genererar HD-standardcitat enligt Högsta domstolens referensstil.
    
    Args:
        author_first: Författarens förnamn
        author_last: Författarens efternamn
        title: Verkets titel
        edition: Upplaga (1 för första upplagan)
        year: Utgivningsår
        
    Returns:
        Formaterat citat, t.ex. "Christina Ramberg, Köplagen, 4 uppl. 2020"
        
    Note:
        Första upplagan anges inte enligt HD:s praxis.
    """
    pass
```

## Frågor?

Skapa ett issue eller kontakta projektägaren via GitHub.

## Code of Conduct

- Var respektfull och konstruktiv
- Fokusera på Access to Justice-målen
- Respektera upphovsrätt och licenser
- Bidra till en välkomnande miljö

Tack för att du hjälper till att göra juridisk kunskap mer tillgänglig! 🏛️
