#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Single Book - Juridikbok Harvester
========================================

Testskript för att verifiera harvester-funktionalitet på EN bok
innan fullständig harvesting körs.

Detta skript:
1. Testar anslutning till juridikbok.se
2. Extraherar metadata från en testbok
3. Testar LIBRIS-integration
4. Genererar HD-citat
5. Skapar filnamn
6. (Optional) Testar PDF-nedladdning

Kör detta INNAN du kör fullständig harvesting!
"""

import sys
from pathlib import Path

# Lägg till src/ i Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from harvester import (
    JuridikbokHarvester,
    format_hd_citation,
    format_short_citation,
    generate_filename,
    parse_author_name,
    search_libris
)

# ============================================================================
# TEST KONFIGURATION
# ============================================================================

# Testbok: Lärobok i obligationsrätt av Knut Rodhe
TEST_BOOK_URL = "https://juridikbok.se/book/9118676421"
TEST_BOOK_EXPECTED = {
    'title': 'Lärobok i obligationsrätt',
    'author': 'Knut Rodhe',
    'isbn': '9118676421',
    'year': 1986,
    'edition': 6
}

# ============================================================================
# TESTFUNKTIONER
# ============================================================================

def print_section(title: str):
    """Skriv ut en sektionsrubrik."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(test_name: str, passed: bool, details: str = ""):
    """Skriv ut testresultat."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"     {details}")

def test_helper_functions():
    """Testa hjälpfunktioner."""
    print_section("TEST 1: Hjälpfunktioner")
    
    # Test parse_author_name
    first, last = parse_author_name("Christina Ramberg")
    passed = (first == "Christina" and last == "Ramberg")
    print_result("parse_author_name('Christina Ramberg')", passed, 
                 f"Resultat: {first} {last}")
    
    # Test format_hd_citation
    citation = format_hd_citation("Christina", "Ramberg", "Köplagen", 4, 2020)
    expected = "Christina Ramberg, Köplagen, 4 uppl. 2020"
    passed = (citation == expected)
    print_result("format_hd_citation (upplaga 4)", passed, f"'{citation}'")
    
    # Test format_hd_citation för första upplagan (ingen upplaga-markering)
    citation_1st = format_hd_citation("Knut", "Rodhe", "Testbok", 1, 2000)
    expected_1st = "Knut Rodhe, Testbok, 2000"
    passed = (citation_1st == expected_1st)
    print_result("format_hd_citation (upplaga 1 - ingen markering)", passed, 
                 f"'{citation_1st}'")
    
    # Test format_short_citation
    short = format_short_citation("Ramberg", 2020)
    expected_short = "Ramberg (2020)"
    passed = (short == expected_short)
    print_result("format_short_citation", passed, f"'{short}'")
    
    # Test generate_filename
    filename = generate_filename(2020, "bok", "Ramberg", "Köplagen", 4)
    expected_fn = "2020 - bok - Ramberg - Köplagen - 4 uppl.pdf"
    passed = (filename == expected_fn)
    print_result("generate_filename", passed, f"'{filename}'")

def test_harvester_initialization():
    """Testa harvester-initialisering."""
    print_section("TEST 2: Harvester Initialisering")
    
    try:
        harvester = JuridikbokHarvester()
        print_result("Skapa JuridikbokHarvester-instans", True, 
                     f"Output dir: {harvester.output_dir}")
        return harvester
    except Exception as e:
        print_result("Skapa JuridikbokHarvester-instans", False, f"Error: {e}")
        return None

def test_metadata_extraction(harvester):
    """Testa metadata-extrahering från juridikbok.se."""
    print_section("TEST 3: Metadata-extrahering")
    
    if not harvester:
        print_result("Metadata-extrahering", False, "Harvester ej initialiserad")
        return None
    
    print(f"Hämtar metadata från: {TEST_BOOK_URL}")
    metadata = harvester.extract_book_metadata(TEST_BOOK_URL)
    
    if not metadata:
        print_result("Metadata-extrahering", False, "Ingen metadata returnerad")
        return None
    
    print("\n--- Extraherad metadata ---")
    for key, value in metadata.items():
        print(f"{key:20s}: {value}")
    
    # Verifiera förväntad data
    tests = [
        ("Titel", metadata['title'] == TEST_BOOK_EXPECTED['title']),
        ("Författare", metadata['author'] == TEST_BOOK_EXPECTED['author']),
        ("ISBN", metadata['isbn'] == TEST_BOOK_EXPECTED['isbn']),
        ("År", metadata['year'] == TEST_BOOK_EXPECTED['year']),
        ("Upplaga", metadata['edition'] == TEST_BOOK_EXPECTED['edition'])
    ]
    
    print("\n--- Verifiering mot förväntad data ---")
    all_passed = True
    for test_name, passed in tests:
        print_result(test_name, passed)
        if not passed:
            all_passed = False
    
    return metadata if all_passed else None

def test_libris_integration(metadata):
    """Testa LIBRIS-integration."""
    print_section("TEST 4: LIBRIS Integration")
    
    if not metadata:
        print_result("LIBRIS-sökning", False, "Ingen metadata tillgänglig")
        return None
    
    print(f"Söker i LIBRIS efter: {metadata['title']}")
    libris_data = search_libris(
        title=metadata['title'],
        author=metadata['author'],
        year=metadata['year']
    )
    
    if libris_data:
        print_result("LIBRIS-sökning", True, "Data hittad")
        print("\n--- LIBRIS-data ---")
        for key, value in libris_data.items():
            print(f"{key:20s}: {value}")
        return libris_data
    else:
        print_result("LIBRIS-sökning", False, 
                     "Ingen data från LIBRIS (kan vara OK om boken ej finns där)")
        return None

def test_citation_generation(metadata):
    """Testa HD-citatgenerering."""
    print_section("TEST 5: HD-Citatgenerering")
    
    if not metadata:
        print_result("Citatgenerering", False, "Ingen metadata tillgänglig")
        return
    
    hd_citation = format_hd_citation(
        metadata['author_first'],
        metadata['author_last'],
        metadata['title'],
        metadata['edition'],
        metadata['year']
    )
    
    short_citation = format_short_citation(
        metadata['author_last'],
        metadata['year']
    )
    
    print_result("HD-standardcitat", True, f"'{hd_citation}'")
    print_result("Kortcitat", True, f"'{short_citation}'")

def test_filename_generation(metadata):
    """Testa filnamnsgenerering."""
    print_section("TEST 6: Filnamnsgenerering")
    
    if not metadata:
        print_result("Filnamnsgenerering", False, "Ingen metadata tillgänglig")
        return
    
    filename = generate_filename(
        metadata['year'],
        metadata['work_type'],
        metadata['author_last'],
        metadata['title'],
        metadata['edition']
    )
    
    print_result("Generera filnamn", True, f"'{filename}'")
    
    # Verifiera att filnamnet följer standardformat
    import re
    pattern = r'^\d{4} - .+ - .+ - .+ - \d+ uppl\.pdf$'
    matches_format = bool(re.match(pattern, filename))
    print_result("Format-validering", matches_format, 
                 "Följer format: ÅÅÅÅ - typ - författare - titel - upplaga.pdf")

def test_pdf_url(metadata):
    """Testa om PDF-URL hittades."""
    print_section("TEST 7: PDF-URL")
    
    if not metadata:
        print_result("PDF-URL check", False, "Ingen metadata tillgänglig")
        return
    
    if metadata.get('pdf_url'):
        print_result("PDF-URL hittad", True, f"'{metadata['pdf_url']}'")
        
        # Fråga användare om test-nedladdning
        response = input("\nVill du testa PDF-nedladdning? (ja/nej): ").strip().lower()
        if response in ['ja', 'j', 'yes', 'y']:
            test_pdf_download(metadata)
    else:
        print_result("PDF-URL hittad", False, 
                     "Ingen PDF-URL - kan kräva JavaScript eller inloggning")

def test_pdf_download(metadata):
    """Testa PDF-nedladdning."""
    print("\n--- Testar PDF-nedladdning ---")
    
    harvester = JuridikbokHarvester()
    filename = generate_filename(
        metadata['year'],
        metadata['work_type'],
        metadata['author_last'],
        metadata['title'],
        metadata['edition']
    )
    
    success = harvester.download_pdf(metadata['pdf_url'], filename)
    
    if success:
        print_result("PDF-nedladdning", True, f"Sparad som: {filename}")
        filepath = harvester.output_dir / filename
        filesize = filepath.stat().st_size if filepath.exists() else 0
        print(f"     Filstorlek: {filesize / 1024:.1f} KB")
    else:
        print_result("PDF-nedladdning", False, "Nedladdning misslyckades")

# ============================================================================
# HUVUDPROGRAM
# ============================================================================

def main():
    """Kör alla tester."""
    print("\n" + "=" * 70)
    print("  JURIDIKBOK HARVESTER - SINGLE BOOK TEST")
    print("=" * 70)
    print(f"\nTestbok: {TEST_BOOK_URL}")
    print(f"Förväntat: {TEST_BOOK_EXPECTED['title']} av {TEST_BOOK_EXPECTED['author']}")
    
    # Kör tester i ordning
    test_helper_functions()
    
    harvester = test_harvester_initialization()
    
    metadata = test_metadata_extraction(harvester)
    
    if metadata:
        libris_data = test_libris_integration(metadata)
        test_citation_generation(metadata)
        test_filename_generation(metadata)
        test_pdf_url(metadata)
    
    # Sammanfattning
    print_section("SAMMANFATTNING")
    print("\nOm alla tester ovan passerade (✓ PASS) är harvester.py redo!")
    print("\nNästa steg:")
    print("1. Kör 'python src/harvester.py' för fullständig harvesting")
    print("2. Eller testa på fler enskilda böcker först")
    print("\n⚠️  PÅMINNELSE: Respektera CC BY-NC 4.0 licensen!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
