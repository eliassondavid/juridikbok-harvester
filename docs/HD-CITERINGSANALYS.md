# HD:s doktrinreferensformat – Analys

## Sammanfattning

Högsta domstolen (HD) använder ett konsekvent format för hänvisningar till juridisk doktrin. Denna analys, baserad på genomgång av bl.a. NJA 2021 s. 173, dokumenterar mönstret och ligger till grund för harvester-skriptets automatiska generering av `citation_hd`-fältet.

## HD:s standardformat

```
[Förnamn] [Efternamn], [Titel], [X uppl.] [År], s. [sida]
```

### Exempel ur rättspraxis

| Källa | HD:s referens |
|-------|---------------|
| NJA 2021 s. 173 | *Knut Rodhe, Obligationsrätt, 1956, s. 134* |
| NJA 2021 s. 173 | *Stefan Lindskog, Betalning, 2 uppl. 2018, s. 219 f.* |

### Regler

1. **Förnamn** anges vid första hänvisningen i en dom. Vid upprepning i samma dom används bara efternamn.
2. **Upplaga** anges bara om verket har ≥2 upplagor. HD skriver aldrig "1 uppl."
3. **Flera författare** separeras med "och" (ej "&"): *Hugo Tiberg och Dan Lennhammer, Skuldebrev, växel och check, 7 uppl. 1995*
4. **Avhandlingar** citeras identiskt med böcker – HD anger inte "akad. avh." eller "diss." i sina domar. Verkstypen är bibliografisk metadata, inte del av referensformatet.
5. **Sidangivelse** avslutar alltid referensen vid citering av specifikt avsnitt.

## Kortcitat

I löpande domskäl förekommer kortformer efter att verket introducerats:

- *Rodhe, Obligationsrätt, s. 134*
- *Lindskog, Betalning, s. 219 f.*
- *Rodhe a.a. s. 721* (vid upprepad hänvisning)

## Separata verk vs. upplagor

Rodhes *Obligationsrätt* (1956, 818 s., ofta kallad "Handbok") och *Lärobok i obligationsrätt* (1966–1986, 6 upplagor) är **separata verk** som citeras oberoende av varandra. HD anger alltid vilken titel som avses.

## Alias-register

Vissa klassiska verk har vedertagna kortformer i doktrin och rättspraxis:

| Fullständig titel | Alias |
|-------------------|-------|
| Rodhe, Obligationsrätt (1956) | "Rodhe, Handbok", "Obl." |
| Rodhe, Lärobok i obligationsrätt | "Rodhe, Lärobok" |

Alias-registret underhålls manuellt i `catalog.json` under fältet `aliases`.

## Metod

Analysen bygger på:

- Fullständig genomläsning av NJA 2021 s. 173 (Ö 1733-20), samtliga instanser
- Christer Danielsson, "Utformningen av Högsta domstolens avgöranden nu och då", SvJT 2022 s. 513
- Christina Rambergs forskning om litteraturhänvisningar i HD:s förmögenhetsrättsliga avgöranden 2006–2015
- Stickprov ur NJA 2018–2023
