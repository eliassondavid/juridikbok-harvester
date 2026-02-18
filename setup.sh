#!/bin/bash
# ============================================================
# juridikbok-harvester – Setup & GitHub push
# Kör detta i Terminal på din Mac
# ============================================================

set -e

echo "=== 1. Packa upp och gå in i mappen ==="
cd ~/Downloads
tar xzf juridikbok-harvester-repo.tar.gz
cd juridikbok-harvester

echo "=== 2. Initiera git-repo ==="
git init
git add .
git commit -m "Initial commit: juridikbok.se harvester v2

- Fas 1: Crawl + PDF-nedladdning (~900 verk)
- Fas 2: LIBRIS-anrikning (SAB, DDC, ämnesord)
- HD-citeringsformat (automatgenererat)
- Resume-funktion
- CC BY-NC 4.0"

echo "=== 3. Skapa repo på GitHub och push ==="
# Alternativ A: Om du har GitHub CLI (gh)
# gh repo create eliassondavid/juridikbok-harvester --public --source=. --push --description "Harvester för juridikbok.se – systematisk nedladdning och LIBRIS-anrikning av svensk juridisk doktrin (Access to Justice)"

# Alternativ B: Manuellt
# 1. Gå till https://github.com/new
# 2. Repo name: juridikbok-harvester
# 3. Description: Harvester för juridikbok.se – systematisk nedladdning och LIBRIS-anrikning av svensk juridisk doktrin (Access to Justice)
# 4. Public
# 5. INTE "Add a README" (vi har redan en)
# 6. Klicka Create repository
# 7. Kör sedan:

git remote add origin https://github.com/eliassondavid/juridikbok-harvester.git
git branch -M main
git push -u origin main

echo "=== 4. Installera Python-beroenden ==="
pip3 install -r requirements.txt

echo "=== 5. Testkörning ==="
python3 src/harvester.py --max-books 3 --output-dir ./test

echo ""
echo "✓ Klart! Repo finns nu på: https://github.com/eliassondavid/juridikbok-harvester"
echo ""
echo "Nästa steg:"
echo "  python3 src/harvester.py --output-dir ./bibliotek    # Full körning (~900 böcker)"
