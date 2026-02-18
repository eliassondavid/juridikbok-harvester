#!/usr/bin/env python3
"""
juridikbok.se Harvester – Fas 1 & 2 (v2)
==========================================
Systematiskt nedladdnings- och metadata-anrikningsverktyg för juridikbok.se.

Fas 1: Crawlar juridikbok.se, laddar ner alla PDF:er med konsekvent namngivning.
Fas 2: Anrikar metadata via LIBRIS (ämnesord, SAB, DDC, författarnamn).

Nyheter i v2:
  - Filnamn matchar befintligt Drive-arkiv: ÅÅÅÅ - typ - författare - titel - upplaga
  - citation_hd: HD:s referensformat (Knut Rodhe, Obligationsrätt, 1956)
  - short_cite: Kortform (Rodhe, Obligationsrätt)
  - aliases: Tom lista för manuell ifyllning
  - Förnamn/efternamn separerade

Licens: Verken på juridikbok.se är publicerade under CC BY-NC 4.0.
        Detta skript är avsett för icke-kommersiellt bruk.

Användning:
    python harvester.py                     # Kör allt (crawl + download + LIBRIS)
    python harvester.py --crawl-only        # Bara crawla metadata (inga PDF:er)
    python harvester.py --enrich-only       # Bara LIBRIS-anrikning (kräver catalog.json)
    python harvester.py --output-dir /path  # Ange utdatamapp
    python harvester.py --delay 2.0         # Fördröjning mellan requests (sekunder)

Författare: David (Access to Justice-projektet)
"""

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installera beroenden: pip install requests beautifulsoup4")
    sys.exit(1)


# ============================================================================
# Konfiguration
# ============================================================================

BASE_URL = "https://www.juridikbok.se"
BOOKS_URL = f"{BASE_URL}/Books/All"
LIBRIS_XSEARCH = "https://libris.kb.se/xsearch"
LIBRIS_BIB = "https://libris.kb.se/bib"
DEFAULT_DELAY = 1.5
USER_AGENT = "JuridikbokHarvester/2.0 (Access to Justice research project)"

# Mappning: juridikbok.se verkstyp -> filnamnsförkortning (matchar Davids arkiv)
BOOK_TYPE_MAP = {
    'Monografi': 'bok',
    'Avhandling': 'avh',
    'Akademisk avhandling': 'avh',
    'akademisk avhandling': 'avh',
    'Festskrift': 'festskrift',
    'Antologi': 'antologi',
    'Kommentar': 'kommentar',
    'Lagkommentar': 'kommentar',
    'Lärobok': 'bok',
    'Rapport': 'rapport',
    'Betänkande': 'betankande',
}


# ============================================================================
# Hjälpfunktioner
# ============================================================================

def sanitize_filename(text: str, max_length: int = 80) -> str:
    """Omvandla text till ett säkert filnamn, bevara läsbarhet."""
    replacements = {
        'å': 'a', 'ä': 'ae', 'ö': 'oe', 'Å': 'A', 'Ä': 'Ae', 'Ö': 'Oe',
        'é': 'e', 'è': 'e', 'ü': 'u', 'ß': 'ss',
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    # Behåll mellanslag, bindestreck, komma och punkt
    text = re.sub(r'[^\w\s,.\-]', '', text)
    text = re.sub(r'\s+', ' ', text.strip())
    return text[:max_length].rstrip(' .-,')


def parse_author_name(full_name: str) -> dict:
    """Dela upp författarnamn i förnamn och efternamn.
    
    Hanterar:
      'Knut Rodhe' -> {'first': 'Knut', 'last': 'Rodhe', 'full': 'Knut Rodhe'}
      'Hugo Tiberg' -> {'first': 'Hugo', 'last': 'Tiberg', 'full': 'Hugo Tiberg'}
      'Antonina Bakardjieva Engelbrekt' -> {'first': 'Antonina', 'last': 'Bakardjieva Engelbrekt', ...}
    """
    parts = full_name.strip().split()
    if len(parts) == 0:
        return {'first': '', 'last': 'Okänd', 'full': 'Okänd'}
    elif len(parts) == 1:
        return {'first': '', 'last': parts[0], 'full': parts[0]}
    else:
        # Förnamn = första ordet, efternamn = resten
        # (fungerar för de flesta svenska akademiska namn)
        return {
            'first': parts[0],
            'last': ' '.join(parts[1:]),
            'full': full_name.strip()
        }


def parse_libris_author(libris_name: str) -> dict:
    """Tolka LIBRIS-format: 'Rodhe, Knut, 1909-1999' -> förnamn/efternamn."""
    # Ta bort årtal
    clean = re.sub(r',\s*\d{4}-\d{0,4}\.?\.?\.?\s*$', '', libris_name).strip()
    parts = [p.strip() for p in clean.split(',', 1)]
    if len(parts) == 2:
        return {'first': parts[1], 'last': parts[0], 'full': f"{parts[1]} {parts[0]}"}
    else:
        return parse_author_name(clean)


def make_filename(book: dict) -> str:
    """Skapa filnamn som matchar Davids befintliga arkiv:
    ÅÅÅÅ - typ - författare - titel - Xuppl.pdf
    
    Exempel:
      1956 - bok - Rodhe - Obligationsratt.pdf
      1995 - bok - Tiberg, Lennhammer - Skuldebrev vaxel och check - 7uppl.pdf
      2023 - avhandling - Gothlin - Prioritet och avtal.pdf
    """
    year = book.get('year', '0000')
    
    # Verkstyp (case-insensitive lookup)
    raw_type = book.get('book_type', 'bok')
    book_type = BOOK_TYPE_MAP.get(raw_type, None)
    if not book_type:
        book_type = BOOK_TYPE_MAP.get(raw_type.lower(), raw_type.lower())
    book_type = sanitize_filename(book_type, 15)
    
    # Författare: efternamn, kommaseparerade
    authors = book.get('authors_parsed', [])
    if not authors:
        raw = book.get('authors', ['Okand'])
        authors = [parse_author_name(a) for a in raw]
    author_str = ', '.join(a['last'] for a in authors)
    author_str = sanitize_filename(author_str, 40)
    
    # Titel
    title = sanitize_filename(book.get('title', 'Utan titel'), 60)
    
    parts = [year, book_type, author_str, title]
    
    # Upplaga (bara om det finns en)
    edition = book.get('edition')
    if edition:
        parts.append(f"{edition}uppl")
    
    return ' - '.join(parts) + '.pdf'


def build_citation_hd(book: dict) -> str:
    """Bygg HD:s referensformat.
    
    Format: [Förnamn] [Efternamn], [Titel], [X uppl.] [År]
    
    Exempel:
      Knut Rodhe, Obligationsrätt, 1956
      Stefan Lindskog, Betalning, 2 uppl. 2018
      Hugo Tiberg och Dan Lennhammer, Skuldebrev, växel och check, 7 uppl. 1995
    """
    # Författare
    authors = book.get('authors_parsed', [])
    if not authors:
        raw = book.get('authors', ['Okänd'])
        authors = [parse_author_name(a) for a in raw]
    
    if len(authors) == 1:
        author_str = authors[0]['full']
    elif len(authors) == 2:
        author_str = f"{authors[0]['full']} och {authors[1]['full']}"
    else:
        author_str = ', '.join(a['full'] for a in authors[:-1]) + f" och {authors[-1]['full']}"
    
    # Titel (originalform med svenska tecken)
    title = book.get('title', 'Utan titel')
    
    # Upplaga + år
    edition = book.get('edition')
    year = book.get('year', '')
    
    if edition and edition != '1':
        year_part = f"{edition} uppl. {year}"
    else:
        year_part = year
    
    return f"{author_str}, {title}, {year_part}"


def build_short_cite(book: dict) -> str:
    """Bygg kortcitat: Efternamn, Titel.
    
    Exempel:
      Rodhe, Obligationsrätt
      Lindskog, Betalning
      Tiberg och Lennhammer, Skuldebrev, växel och check
    """
    authors = book.get('authors_parsed', [])
    if not authors:
        raw = book.get('authors', ['Okänd'])
        authors = [parse_author_name(a) for a in raw]
    
    if len(authors) == 1:
        author_str = authors[0]['last']
    elif len(authors) == 2:
        author_str = f"{authors[0]['last']} och {authors[1]['last']}"
    else:
        author_str = ', '.join(a['last'] for a in authors[:-1]) + f" och {authors[-1]['last']}"
    
    title = book.get('title', 'Utan titel')
    return f"{author_str}, {title}"


def polite_get(session: requests.Session, url: str, delay: float = DEFAULT_DELAY, **kwargs) -> requests.Response:
    """GET med fördröjning och felhantering."""
    time.sleep(delay)
    try:
        resp = session.get(url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        print(f"  ⚠ Fel vid hämtning av {url}: {e}")
        return None


# ============================================================================
# Fas 1: Crawla juridikbok.se
# ============================================================================

def crawl_book_list(session: requests.Session, delay: float) -> list[dict]:
    """Hämta alla böcker från juridikbok.se:s katalog."""
    books = []
    page = 0
    
    while True:
        url = f"{BOOKS_URL}?p={page}&ps=24&s=0"
        print(f"  Hämtar sida {page + 1}...")
        resp = polite_get(session, url, delay)
        if not resp:
            break
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        book_divs = soup.find_all('div', class_='book')
        
        if not book_divs:
            break
        
        for div in book_divs:
            book = {}
            
            # Titel och länk
            title_tag = div.find('h3', class_='title')
            if title_tag and title_tag.find('a'):
                link = title_tag.find('a')
                book['title_raw'] = link.get_text(strip=True)
                book['detail_url'] = BASE_URL + link['href']
                
                year_match = re.search(r'\((\d{4})\)\s*$', book['title_raw'])
                if year_match:
                    book['year'] = year_match.group(1)
                    book['title'] = re.sub(r'\s*\(\d{4}\)\s*$', '', book['title_raw'])
                else:
                    book['title'] = book['title_raw']
            
            # Undertitel
            subtitle = div.find('p', class_='subtitle')
            if subtitle:
                book['subtitle'] = subtitle.get_text(strip=True)
            
            # Författare (råformat)
            author_links = div.find_all('a', class_='author')
            if author_links:
                book['authors'] = [a.get_text(strip=True) for a in author_links]
                book['authors_parsed'] = [parse_author_name(a.get_text(strip=True)) for a in author_links]
            
            if book.get('title'):
                books.append(book)
        
        # Pagination
        pagination = soup.find('ul', class_='pagination')
        if pagination:
            all_pages = pagination.find_all('a', class_='page-link')
            page_nums = [int(a.get_text(strip=True)) for a in all_pages 
                        if a.get_text(strip=True).isdigit()]
            if page_nums and (page + 1) < max(page_nums):
                page += 1
            else:
                break
        else:
            break
    
    print(f"  Hittade {len(books)} böcker i katalogen.")
    return books


def crawl_book_details(session: requests.Session, books: list[dict], delay: float) -> list[dict]:
    """Hämta detaljerad metadata för varje bok."""
    total = len(books)
    
    for i, book in enumerate(books):
        url = book.get('detail_url')
        if not url:
            continue
        
        print(f"  [{i+1}/{total}] {book.get('title', '?')[:50]}...")
        resp = polite_get(session, url, delay)
        if not resp:
            continue
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # PDF-länk
        pdf_link = soup.find('a', href=re.compile(r'/books/pdf\?'))
        if pdf_link:
            book['pdf_url'] = BASE_URL + pdf_link['href']
        
        # Metadata från definitionslistan
        dl = soup.find('dl', class_='details')
        if dl:
            current_key = None
            for child in dl.children:
                if child.name == 'dt':
                    current_key = child.get_text(strip=True)
                elif child.name == 'dd' and current_key:
                    value = child.get_text(strip=True)
                    
                    if current_key == 'ISBN':
                        book['isbn'] = value
                    elif current_key == 'URN':
                        urn_link = child.find('a')
                        if urn_link:
                            book['urn'] = urn_link.get_text(strip=True)
                            book['urn_url'] = urn_link['href']
                    elif current_key == 'Upplaga':
                        book['edition'] = value
                    elif current_key == 'Förlag & år':
                        book['publisher_raw'] = value
                        if not book.get('year'):
                            y = re.search(r'\((\d{4})\)', value)
                            if y:
                                book['year'] = y.group(1)
                    elif current_key == 'Serie':
                        book['series'] = value
                    elif current_key == 'Typ av verk':
                        book['book_type'] = value
                    elif current_key == 'Ämnen':
                        book['subjects_juridikbok'] = [
                            a.get_text(strip=True) for a in child.find_all('a')
                        ] if child.find_all('a') else [value]
                    
                    current_key = None
        
        # Generera alla referensfält
        book['filename'] = make_filename(book)
        book['citation_hd'] = build_citation_hd(book)
        book['short_cite'] = build_short_cite(book)
        book['aliases'] = []  # Tom lista – fylls i manuellt vid behov
        
        # Juridikbok-URL för referens
        book_id_match = re.search(r'/book/(.+)$', url)
        if book_id_match:
            book['juridikbok_id'] = book_id_match.group(1)
        book['juridikbok_url'] = url
    
    return books


def download_pdfs(session: requests.Session, books: list[dict], output_dir: Path, delay: float) -> None:
    """Ladda ner alla PDF:er."""
    pdf_dir = output_dir / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    total = len([b for b in books if b.get('pdf_url')])
    downloaded = 0
    skipped = 0
    failed = 0
    
    for book in books:
        pdf_url = book.get('pdf_url')
        if not pdf_url:
            continue
        
        filename = book.get('filename', 'unknown.pdf')
        filepath = pdf_dir / filename
        
        if filepath.exists() and filepath.stat().st_size > 10000:
            skipped += 1
            book['pdf_path'] = str(filepath)
            book['pdf_downloaded'] = True
            continue
        
        downloaded += 1
        print(f"  ⬇ [{downloaded}/{total}] {filename[:60]}...")
        
        try:
            time.sleep(delay)
            resp = session.get(pdf_url, timeout=120, stream=True)
            resp.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            size_mb = filepath.stat().st_size / (1024 * 1024)
            book['pdf_path'] = str(filepath)
            book['pdf_size_mb'] = round(size_mb, 1)
            book['pdf_downloaded'] = True
            print(f"    ✓ {size_mb:.1f} MB")
            
        except Exception as e:
            failed += 1
            book['pdf_downloaded'] = False
            book['pdf_error'] = str(e)
            print(f"    ✗ Fel: {e}")
    
    print(f"\n  Nedladdning klar: {downloaded} nya, {skipped} redan nedladdade, {failed} misslyckade.")


# ============================================================================
# Fas 2: LIBRIS-anrikning
# ============================================================================

def lookup_libris_by_isbn(session: requests.Session, isbn: str, delay: float) -> dict | None:
    """Sök i LIBRIS via ISBN och hämta bib-ID."""
    url = f"{LIBRIS_XSEARCH}?query=isbn:{isbn}&format=json"
    resp = polite_get(session, url, delay * 0.5)
    if not resp:
        return None
    
    try:
        data = resp.json()
        results = data.get('xsearch', {}).get('list', [])
        for r in results:
            if r.get('type') == 'book':
                bib_match = re.search(r'/bib/(\w+)', r.get('identifier', ''))
                if bib_match:
                    return {
                        'bib_id': bib_match.group(1),
                        'libris_url': r['identifier'],
                        'libris_creator': r.get('creator', '')
                    }
        if results:
            bib_match = re.search(r'/bib/(\w+)', results[0].get('identifier', ''))
            if bib_match:
                return {
                    'bib_id': bib_match.group(1),
                    'libris_url': results[0]['identifier'],
                    'libris_creator': results[0].get('creator', '')
                }
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def lookup_libris_by_title_author(session: requests.Session, title: str, author: str, delay: float) -> dict | None:
    """Sök i LIBRIS via titel och författare."""
    clean_title = re.sub(r'[^\w\s]', '', title)[:50]
    author_last = author.split(' ')[-1] if author else ''
    
    query = f'title:({clean_title})'
    if author_last:
        query += f' author:({author_last})'
    
    url = f"{LIBRIS_XSEARCH}?query={query}&format=json&n=5"
    resp = polite_get(session, url, delay * 0.5)
    if not resp:
        return None
    
    try:
        data = resp.json()
        results = data.get('xsearch', {}).get('list', [])
        for r in results:
            if r.get('type') == 'book':
                bib_match = re.search(r'/bib/(\w+)', r.get('identifier', ''))
                if bib_match:
                    return {
                        'bib_id': bib_match.group(1),
                        'libris_url': r['identifier'],
                        'libris_creator': r.get('creator', '')
                    }
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def fetch_libris_classification(session: requests.Session, bib_id: str, delay: float) -> dict:
    """Hämta ämnesord och klassifikation från LIBRIS fullvy."""
    url = f"{LIBRIS_BIB}/{bib_id}?vw=full"
    resp = polite_get(session, url, delay * 0.5)
    if not resp:
        return {}
    
    result = {}
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Ämnesord
    subjects_section = soup.find('h3', string=re.compile(r'Ämnesord och genre'))
    if subjects_section:
        parent = subjects_section.find_next('div')
        if parent:
            subject_links = parent.find_all('a')
            subjects = []
            for link in subject_links:
                term = link.get_text(strip=True)
                system_span = link.find_next_sibling('span', class_='beskrivning')
                system = system_span.get_text(strip=True) if system_span else ''
                subjects.append({'term': term, 'system': system})
            if subjects:
                result['subjects_libris'] = subjects
    
    # Klassifikation
    class_section = soup.find('h3', string=re.compile(r'Klassifikation'))
    if class_section:
        parent = class_section.find_next('div')
        if parent:
            classifications = {}
            
            ddc_label = parent.find('span', string=re.compile(r'DDC'))
            if ddc_label:
                ddc_link = ddc_label.find_next('a')
                if ddc_link:
                    classifications['ddc'] = ddc_link.get_text(strip=True)
            
            udk_label = parent.find('span', string=re.compile(r'UDK'))
            if udk_label:
                udk_link = udk_label.find_next('a')
                if udk_link:
                    classifications['udk'] = udk_link.get_text(strip=True)
            
            sab_links = parent.find_all('a', title=re.compile(r'SAB:'))
            for link in sab_links:
                classifications['sab'] = link.get_text(strip=True)
                sab_rubrik = soup.find('h3', string=re.compile(r'SAB-rubrik'))
                if sab_rubrik:
                    sab_desc_div = sab_rubrik.find_next('div')
                    if sab_desc_div:
                        desc = sab_desc_div.get_text(strip=True)
                        if desc:
                            classifications['sab_description'] = desc
            
            if classifications:
                result['classification'] = classifications
    
    return result


def enrich_with_libris(session: requests.Session, books: list[dict], delay: float) -> None:
    """Anrika alla böcker med LIBRIS-metadata."""
    total = len(books)
    found = 0
    not_found = 0
    
    for i, book in enumerate(books):
        title = book.get('title', '?')[:50]
        print(f"  [{i+1}/{total}] LIBRIS: {title}...")
        
        libris_info = None
        isbn = book.get('isbn')
        if isbn:
            libris_info = lookup_libris_by_isbn(session, isbn, delay)
        
        if not libris_info:
            authors = book.get('authors', [''])
            libris_info = lookup_libris_by_title_author(
                session, book.get('title', ''), authors[0], delay
            )
        
        if not libris_info:
            not_found += 1
            book['libris_found'] = False
            print(f"    ⚠ Ej funnen i LIBRIS")
            continue
        
        book['libris_bib_id'] = libris_info['bib_id']
        book['libris_url'] = libris_info['libris_url']
        
        # Komplettera författarnamn från LIBRIS om vi har bättre data
        libris_creator = libris_info.get('libris_creator', '')
        if libris_creator:
            libris_parsed = parse_libris_author(libris_creator)
            # Uppdatera authors_parsed med LIBRIS-data om den har förnamn
            if libris_parsed.get('first') and book.get('authors_parsed'):
                existing = book['authors_parsed'][0]
                if not existing.get('first') or len(libris_parsed['first']) > len(existing.get('first', '')):
                    book['authors_parsed'][0] = libris_parsed
                    # Regenerera citeringar med bättre namn
                    book['citation_hd'] = build_citation_hd(book)
                    book['short_cite'] = build_short_cite(book)
        
        # Hämta klassifikation
        class_data = fetch_libris_classification(session, libris_info['bib_id'], delay)
        book.update(class_data)
        
        found += 1
        subjects = [s['term'] for s in book.get('subjects_libris', [])]
        sab = book.get('classification', {}).get('sab', '-')
        print(f"    ✓ SAB: {sab}, Ämnen: {', '.join(subjects[:3]) if subjects else '-'}")
    
    print(f"\n  LIBRIS-anrikning klar: {found} funna, {not_found} ej funna.")


# ============================================================================
# Katalogfil
# ============================================================================

def save_catalog(books: list[dict], output_dir: Path) -> Path:
    """Spara katalogen som JSON."""
    catalog_path = output_dir / "catalog.json"
    
    catalog = {
        'metadata': {
            'source': 'juridikbok.se',
            'license': 'CC BY-NC 4.0',
            'harvested_at': datetime.now().isoformat(),
            'total_books': len(books),
            'books_with_pdf': len([b for b in books if b.get('pdf_url')]),
            'books_with_libris': len([b for b in books if b.get('libris_bib_id')]),
            'version': '2.0',
            'citation_format_note': 'citation_hd följer HD:s referensformat, t.ex. "Knut Rodhe, Obligationsrätt, 1956"',
        },
        'books': books
    }
    
    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    
    print(f"\n  Katalog sparad: {catalog_path}")
    print(f"  Totalt: {catalog['metadata']['total_books']} böcker")
    print(f"  Med PDF: {catalog['metadata']['books_with_pdf']}")
    print(f"  Med LIBRIS-data: {catalog['metadata']['books_with_libris']}")
    
    return catalog_path


def load_catalog(output_dir: Path) -> list[dict] | None:
    """Ladda befintlig katalog."""
    catalog_path = output_dir / "catalog.json"
    if not catalog_path.exists():
        return None
    with open(catalog_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('books', [])


# ============================================================================
# Huvudprogram
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Harvester för juridikbok.se – ladda ner och anrika juridisk litteratur (v2)'
    )
    parser.add_argument('--output-dir', type=str, default='./juridikbok_bibliotek',
                        help='Mapp för nedladdade filer och katalog')
    parser.add_argument('--delay', type=float, default=DEFAULT_DELAY,
                        help=f'Fördröjning mellan requests i sekunder (default: {DEFAULT_DELAY})')
    parser.add_argument('--crawl-only', action='store_true',
                        help='Bara crawla metadata, ladda inte ner PDF:er')
    parser.add_argument('--enrich-only', action='store_true',
                        help='Bara kör LIBRIS-anrikning (kräver befintlig catalog.json)')
    parser.add_argument('--download-only', action='store_true',
                        help='Bara ladda ner PDF:er (kräver befintlig catalog.json)')
    parser.add_argument('--max-books', type=int, default=None,
                        help='Begränsa antal böcker (för testning)')
    
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    
    print("=" * 60)
    print("  juridikbok.se Harvester v2")
    print("  Licens: CC BY-NC 4.0")
    print("  Referensformat: HD-standard")
    print("=" * 60)
    
    if args.enrich_only:
        books = load_catalog(output_dir)
        if not books:
            print("✗ Ingen catalog.json hittad.")
            sys.exit(1)
        print(f"\n▶ Fas 2: LIBRIS-anrikning ({len(books)} böcker)")
        enrich_with_libris(session, books, args.delay)
        save_catalog(books, output_dir)
        return
    
    if args.download_only:
        books = load_catalog(output_dir)
        if not books:
            print("✗ Ingen catalog.json hittad.")
            sys.exit(1)
        print(f"\n▶ Laddar ner PDF:er ({len(books)} böcker)")
        download_pdfs(session, books, output_dir, args.delay)
        save_catalog(books, output_dir)
        return
    
    # Full körning
    print(f"\n▶ Fas 1a: Crawlar juridikbok.se boklista...")
    books = crawl_book_list(session, args.delay)
    
    if args.max_books:
        books = books[:args.max_books]
        print(f"  (Begränsat till {args.max_books} böcker)")
    
    print(f"\n▶ Fas 1b: Hämtar detaljerad metadata för {len(books)} böcker...")
    books = crawl_book_details(session, books, args.delay)
    save_catalog(books, output_dir)
    
    if not args.crawl_only:
        print(f"\n▶ Fas 1c: Laddar ner PDF:er...")
        download_pdfs(session, books, output_dir, args.delay)
        save_catalog(books, output_dir)
    
    print(f"\n▶ Fas 2: LIBRIS-anrikning...")
    enrich_with_libris(session, books, args.delay)
    save_catalog(books, output_dir)
    
    # Visa exempel på genererade citeringar
    print("\n" + "-" * 60)
    print("  Exempel på genererade citeringar:")
    for book in books[:5]:
        if book.get('citation_hd'):
            print(f"  HD:    {book['citation_hd']}")
            print(f"  Kort:  {book['short_cite']}")
            print(f"  Fil:   {book['filename']}")
            print()
    
    print("=" * 60)
    print("  Klart!")
    print("=" * 60)


if __name__ == '__main__':
    main()
