#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lista sve korpuse u sistemu."""

import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from zaikon.modules.corpus.service import get_corpus_service


def main():
    """List all corpora."""
    service = get_corpus_service()
    corpora = service.list_corpora()
    
    if not corpora:
        print("❌ Nema korpusa u sistemu")
        return
    
    print(f"\n📚 Pronađeno {len(corpora)} korpusa:\n")
    
    for corpus in corpora:
        print(f"{'='*80}")
        print(f"Naziv: {corpus.name}")
        print(f"ID: {corpus.corpus_id}")
        print(f"Opis: {corpus.description or 'N/A'}")
        print(f"Jezik: {corpus.language_code.value}")
        print(f"Domen: {corpus.domain or 'N/A'}")
        print(f"Status: {corpus.status}")
        print(f"Kreiran: {corpus.created_at}")
        
        # Get import jobs
        import_jobs = service.list_import_jobs(corpus.corpus_id)
        print(f"Import Jobs: {len(import_jobs)}")
        
        if import_jobs:
            for job in import_jobs:
                print(f"  - Job ID: {job.import_job_id}")
                print(f"    Status: {job.status.value}")
                print(f"    Files: {job.total_files} (supported: {job.supported_files})")
    
    print(f"\n{'='*80}\n")
    
    if corpora:
        print("Za analizu korpusa, koristi:")
        print(f"  python scripts/analyze_pilot_corpus.py {corpora[0].corpus_id}")


if __name__ == "__main__":
    main()

# Made with Bob
