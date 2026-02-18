#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Juridikbok Harvester
====================

Systematisk harvesting av juridisk litteratur från juridikbok.se med:
- LIBRIS-integration för metadata-anrikning
- HD-standardcitatformattering
- Automatisk filnamnsgenerering
- Rate limiting och robust felhantering

Licensiering:
- Kod: MIT License
- Nedladdat innehåll: CC BY-NC 4.0 från juridikbok.se

Författare: David Eliasson
Projekt: Access to Justice - Juridisk AI-forskning
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
import json
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

# ============================================================================
# KONFIGURATION
# ============================================================================

# Base URLs
JURIDIKBOK_BASE_URL = "https://juridikbok.se"
LIBRIS_API_BASE = "http://libris.kb.se/xsearch"

# Katalogstruktur
OUTPUT_DIR = Path("downloads")
METADATA_FILE = Path("metadata.json")
LOG_FILE = Path("harvester.log")

# Rate limiting (sekunder mellan requests)
JURIDIKBOK_DELAY = 2.0  # Respektera servern
LIBRIS_DELAY = 1.0

# User agent för requests
USER_AGENT = "JuridikbokHarvester/1.0 (Access to Justice Research; david.eliasson@example.com)"

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# HJÄLPFUNKTIONER
# ============================================================================

def sanitize_filename(text: str) -> str:
    """
    Sanera text för användning i filnamn.
    
    Args:
        text: Text att sanera
        
    Returns:
        Sanerad text säker för filnamn
    """
    # Ta bort ogiltiga tecken
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    # Komprimera whitespace
    text = re.sub(r'\s+', ' ', text)
    # Ta bort leading/trailing whitespace
    text = text.strip()
    return text

def parse_author_name(full_name: str) -> Tuple[str, str]:
    """
    Dela upp författarnamn i förnamn och efternamn.
    
    Args:
        full_name: Fullständigt namn (t.ex. "Christina Ramberg")
        
    Returns:
        Tuple med (förnamn, efternamn)
        
    Example:
        >>> parse_author_name("Christina Ramberg")
        ("Christina", "Ramberg")
    """
    parts = full_name.strip().split()
    if len(parts) == 0:
        return ("", "")
    elif len(parts) == 1:
        return ("", parts[0])
    else:
        # Sista delen är efternamn, resten är förnamn
        first_name = " ".join(parts[:-1])
        last_name = parts[-1]
        return (first_name, last_name)

def format_hd_citation(author_first: str, author_last: str, 
                       title: str, edition: int, year: int) -> str:
    """
    Generera HD-standardcitat enligt Högsta domstolens referensstil.
    
    Args:
        author_first: Författarens förnamn
        author_last: Författarens efternamn
        title: Verkets titel
        edition: Upplaga (1 för första upplagan)
        year: Utgivningsår
        
    Returns:
        Formaterat citat enligt HD-standard
        
    Example:
        >>> format_hd_citation("Christina", "Ramberg", "Köplagen", 4, 2020)
        "Christina Ramberg, Köplagen, 4 uppl. 2020"
        
    Note:
        Första upplagan anges inte enligt HD:s praxis.
    """
    author = f"{author_first} {author_last}".strip()
    
    if edition == 1:
        # HD anger inte "1 uppl." för första upplagan
        return f"{author}, {title}, {year}"
    else:
        return f"{author}, {title}, {edition} uppl. {year}"

def format_short_citation(author_last: str, year: int) -> str:
    """
    Generera kortcitat för referenser.
    
    Args:
        author_last: Författarens efternamn
        year: Utgivningsår
        
    Returns:
        Kortcitat
        
    Example:
        >>> format_short_citation("Ramberg", 2020)
        "Ramberg (2020)"
    """
    return f"{author_last} ({year})"

def generate_filename(year: int, work_type: str, author_last: str, 
                     title: str, edition: int) -> str:
    """
    Generera filnamn enligt standardformat.
    
    Format: ÅÅÅÅ - typ - författare - titel - upplaga.pdf
    
    Args:
        year: Utgivningsår
        work_type: Typ av verk (bok, avh, etc.)
        author_last: Författarens efternamn
        title: Verkets titel
        edition: Upplaga
        
    Returns:
        Formaterat filnamn
        
    Example:
        >>> generate_filename(2020, "bok", "Ramberg", "Köplagen", 4)
        "2020 - bok - Ramberg - Köplagen - 4 uppl.pdf"
    """
    safe_type = sanitize_filename(work_type)
    safe_author = sanitize_filename(author_last)
    safe_title = sanitize_filename(title)
    
    if edition == 1:
        edition_str = "1 uppl"
    else:
        edition_str = f"{edition} uppl"
    
    filename = f"{year} - {safe_type} - {safe_author} - {safe_title} - {edition_str}.pdf"
    return filename

# ============================================================================
# LIBRIS-INTEGRATION
# ============================================================================

def search_libris(title: str, author: str = None, year: int = None) -> Optional[Dict]:
    """
    Sök i LIBRIS efter metadata för ett verk.
    
    Args:
        title: Verkets titel
        author: Författarens namn (optional)
        year: Utgivningsår (optional)
        
    Returns:
        Dictionary med metadata eller None om inget hittas
    """
    try:
        # Bygg sökquery
        query_parts = [f'title:"{title}"']
        if author:
            query_parts.append(f'author:"{author}"')
        if year:
            query_parts.append(f'year:{year}')
        
        query = " AND ".join(query_parts)
        
        params = {
            'query': query,
            'format': 'json',
            'n': 1  # Bara första resultatet
        }
        
        headers = {'User-Agent': USER_AGENT}
        
        logger.info(f"Söker i LIBRIS: {query}")
        response = requests.get(LIBRIS_API_BASE, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        time.sleep(LIBRIS_DELAY)  # Rate limiting
        
        data = response.json()
        
        if 'xsearch' in data and 'list' in data['xsearch']:
            records = data['xsearch']['list']
            if records:
                record = records[0]
                return {
                    'isbn': record.get('identifier', {}).get('isbn', ''),
                    'sab_code': record.get('classification', {}).get('sab', ''),
                    'subjects': record.get('subject', []),
                    'libris_id': record.get('identifier', {}).get('libris_id', '')
                }
        
        logger.warning(f"Inget LIBRIS-resultat för: {title}")
        return None
        
    except requests.RequestException as e:
        logger.error(f"LIBRIS API-fel: {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"LIBRIS parsning-fel: {e}")
        return None

# ============================================================================
# JURIDIKBOK.SE SCRAPING
# ============================================================================

class JuridikbokHarvester:
    """
    Huvudklass för harvesting av juridikbok.se
    """
    
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        """
        Initialisera harvester.
        
        Args:
            output_dir: Katalog för nedladdade filer
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        
        self.metadata = []
        
        logger.info(f"Harvester initialiserad. Output: {self.output_dir}")
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Hämta och parsa en webbsida.
        
        Args:
            url: URL att hämta
            
        Returns:
            BeautifulSoup-objekt eller None vid fel
        """
        try:
            logger.info(f"Hämtar: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            time.sleep(JURIDIKBOK_DELAY)  # Rate limiting
            
            return BeautifulSoup(response.text, 'html.parser')
            
        except requests.RequestException as e:
            logger.error(f"Kunde inte hämta {url}: {e}")
            return None
    
    def extract_book_metadata(self, book_page_url: str) -> Optional[Dict]:
        """
        Extrahera metadata från en boksida.
        
        Args:
            book_page_url: URL till boksidan
            
        Returns:
            Dictionary med bokmetadata eller None vid fel
        """
        soup = self.fetch_page(book_page_url)
        if not soup:
            return None
        
        try:
            # DENNA FUNKTION MÅSTE ANPASSAS TILL JURIDIKBOK.SE:s FAKTISKA HTML-STRUKTUR
            # Nedan är en mallimplementation som behöver justeras
            
            metadata = {
                'source_url': book_page_url,
                'title': '',
                'author': '',
                'author_first': '',
                'author_last': '',
                'year': 0,
                'edition': 1,
                'work_type': 'bok',
                'pdf_url': '',
                'isbn': '',
                'description': '',
                'publisher': ''
            }
            
            # Extrahera titel
            title_elem = soup.find('h1')  # Anpassa selector
            if title_elem:
                metadata['title'] = title_elem.get_text(strip=True)
            
            # Extrahera författare
            author_elem = soup.find('span', class_='author')  # Anpassa selector
            if author_elem:
                full_name = author_elem.get_text(strip=True)
                metadata['author'] = full_name
                first, last = parse_author_name(full_name)
                metadata['author_first'] = first
                metadata['author_last'] = last
            
            # Extrahera år och upplaga från metadata eller text
            # Detta måste anpassas till faktisk struktur
            year_match = re.search(r'(\d{4})', str(soup))
            if year_match:
                metadata['year'] = int(year_match.group(1))
            
            edition_match = re.search(r'(\d+)\s*uppl', str(soup), re.IGNORECASE)
            if edition_match:
                metadata['edition'] = int(edition_match.group(1))
            
            # Hitta PDF-länk
            pdf_link = soup.find('a', href=re.compile(r'\.pdf$', re.I))
            if pdf_link:
                metadata['pdf_url'] = urljoin(book_page_url, pdf_link['href'])
            
            return metadata
            
        except Exception as e:
            logger.error(f"Fel vid metadata-extrahering från {book_page_url}: {e}")
            return None
    
    def download_pdf(self, pdf_url: str, filename: str) -> bool:
        """
        Ladda ner PDF-fil.
        
        Args:
            pdf_url: URL till PDF
            filename: Målfilnamn
            
        Returns:
            True vid framgång, False vid fel
        """
        filepath = self.output_dir / filename
        
        # Kontrollera om filen redan finns
        if filepath.exists():
            logger.info(f"Filen finns redan: {filename}")
            return True
        
        try:
            logger.info(f"Laddar ner PDF: {filename}")
            response = self.session.get(pdf_url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            time.sleep(JURIDIKBOK_DELAY)  # Rate limiting
            
            logger.info(f"PDF nedladdad: {filename}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Kunde inte ladda ner {pdf_url}: {e}")
            return False
        except IOError as e:
            logger.error(f"Kunde inte spara {filename}: {e}")
            return False
    
    def process_book(self, book_url: str) -> Optional[Dict]:
        """
        Bearbeta en bok fullständigt: metadata + nedladdning + LIBRIS.
        
        Args:
            book_url: URL till boksidan
            
        Returns:
            Komplett metadata-dictionary eller None vid fel
        """
        logger.info(f"Bearbetar bok: {book_url}")
        
        # Extrahera grundmetadata
        metadata = self.extract_book_metadata(book_url)
        if not metadata:
            return None
        
        # Anrika med LIBRIS-data
        libris_data = search_libris(
            title=metadata['title'],
            author=metadata['author'],
            year=metadata['year']
        )
        
        if libris_data:
            metadata.update(libris_data)
            logger.info(f"LIBRIS-data tillagd för: {metadata['title']}")
        
        # Generera HD-citat
        metadata['hd_citation'] = format_hd_citation(
            metadata['author_first'],
            metadata['author_last'],
            metadata['title'],
            metadata['edition'],
            metadata['year']
        )
        
        metadata['short_citation'] = format_short_citation(
            metadata['author_last'],
            metadata['year']
        )
        
        # Generera filnamn
        filename = generate_filename(
            metadata['year'],
            metadata['work_type'],
            metadata['author_last'],
            metadata['title'],
            metadata['edition']
        )
        metadata['filename'] = filename
        
        # Ladda ner PDF om URL finns
        if metadata['pdf_url']:
            success = self.download_pdf(metadata['pdf_url'], filename)
            metadata['downloaded'] = success
        else:
            logger.warning(f"Ingen PDF-URL hittades för: {metadata['title']}")
            metadata['downloaded'] = False
        
        return metadata
    
    def get_all_books(self) -> List[str]:
        """
        Hämta lista över alla bokURLer från huvudsidan.
        
        Returns:
            Lista med bok-URLer
            
        Note:
            Denna funktion måste anpassas till juridikbok.se:s faktiska struktur.
        """
        logger.info("Hämtar lista över alla böcker...")
        
        soup = self.fetch_page(f"{JURIDIKBOK_BASE_URL}/bocker")  # Anpassa URL
        if not soup:
            return []
        
        book_urls = []
        
        # ANPASSA DETTA TILL FAKTISK HTML-STRUKTUR
        # Exempel: hitta alla länkar till bokdetaljsidor
        for link in soup.find_all('a', href=re.compile(r'/bok/')):  # Anpassa selector
            book_url = urljoin(JURIDIKBOK_BASE_URL, link['href'])
            if book_url not in book_urls:
                book_urls.append(book_url)
        
        logger.info(f"Hittade {len(book_urls)} böcker")
        return book_urls
    
    def harvest_all(self):
        """
        Kör fullständig harvesting av alla böcker.
        """
        logger.info("===== STARTAR FULLSTÄNDIG HARVESTING =====")
        
        book_urls = self.get_all_books()
        
        if not book_urls:
            logger.error("Inga böcker hittades!")
            return
        
        total = len(book_urls)
        successful = 0
        failed = 0
        
        for i, book_url in enumerate(book_urls, 1):
            logger.info(f"\n--- Bok {i}/{total} ---")
            
            metadata = self.process_book(book_url)
            
            if metadata:
                self.metadata.append(metadata)
                successful += 1
                logger.info(f"✓ Framgång: {metadata['title']}")
            else:
                failed += 1
                logger.error(f"✗ Misslyckades: {book_url}")
        
        # Spara sammanställd metadata
        self.save_metadata()
        
        logger.info(f"\n===== HARVESTING KLAR =====")
        logger.info(f"Total: {total} böcker")
        logger.info(f"Lyckade: {successful}")
        logger.info(f"Misslyckade: {failed}")
        logger.info(f"Metadata sparad i: {METADATA_FILE}")
    
    def save_metadata(self):
        """
        Spara metadata till JSON-fil.
        """
        try:
            with open(METADATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"Metadata sparad: {METADATA_FILE}")
        except IOError as e:
            logger.error(f"Kunde inte spara metadata: {e}")

# ============================================================================
# HUVUDPROGRAM
# ============================================================================

def main():
    """
    Huvudfunktion för att köra harvester.
    """
    print("=" * 70)
    print("JURIDIKBOK HARVESTER")
    print("=" * 70)
    print()
    print("⚠️  VIKTIGT: CC BY-NC 4.0 LICENS")
    print("Detta verktyg laddar ner material från juridikbok.se som är")
    print("licensierat under CC BY-NC 4.0. Materialet får endast användas")
    print("för icke-kommersiella ändamål.")
    print()
    print("Se LEGAL_NOTICE.md för fullständiga villkor.")
    print("=" * 70)
    print()
    
    # Bekräftelse från användare
    response = input("Fortsätt med harvesting? (ja/nej): ").strip().lower()
    if response not in ['ja', 'j', 'yes', 'y']:
        print("Avbryter.")
        return
    
    # Starta harvesting
    harvester = JuridikbokHarvester()
    harvester.harvest_all()

if __name__ == "__main__":
    main()
