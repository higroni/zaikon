#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skripta za statističku analizu pilot korpusa.

Koristi import report podatke da generiše detaljnu analizu:
- Broj dokumenata
- Prosečna dužina dokumenta
- Broj normativnih tvrdnji
- Distribucija po tipu akta
- Performanse importa
"""

import io
import json
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from zaikon.modules.corpus.service import get_corpus_service
from zaikon.modules.documents.catalog import DocumentCatalogService


def analyze_corpus(corpus_id: UUID) -> dict[str, Any]:
    """Analizira korpus i vraća statistiku."""
    
    corpus_service = get_corpus_service()
    doc_catalog = DocumentCatalogService()
    
    # Osnovne informacije o korpusu
    corpus = corpus_service.get_corpus(corpus_id)
    if not corpus:
        raise ValueError(f"Corpus not found: {corpus_id}")
    
    print(f"\n{'='*80}")
    print(f"ANALIZA KORPUSA: {corpus.name}")
    print(f"{'='*80}\n")
    
    # Import jobs
    import_jobs = corpus_service.list_import_jobs(corpus_id)
    if not import_jobs:
        print("⚠️  Nema import job-ova za ovaj korpus")
        return {}
    
    print(f"📊 Broj import job-ova: {len(import_jobs)}")
    
    # Analiziraj svaki import job
    total_stats = {
        "total_files": 0,
        "supported_files": 0,
        "unsupported_files": 0,
        "total_size_bytes": 0,
        "document_types": {},
        "file_types": {},
        "import_duration_seconds": [],
    }
    
    for job in import_jobs:
        print(f"\n📦 Import Job: {job.import_job_id}")
        print(f"   Status: {job.status.value}")
        print(f"   Total files: {job.total_files}")
        print(f"   Supported: {job.supported_files}")
        print(f"   Unsupported: {job.unsupported_files}")
        
        # Get detailed report
        try:
            report_response = corpus_service.get_import_report(job.import_job_id)
            report = report_response.report
            
            # Summary statistics
            summary = report.summary
            print(f"\n   📈 Summary:")
            for key, value in summary.items():
                print(f"      {key}: {value}")
            
            # Source files analysis
            print(f"\n   📄 Source Files: {len(report.source_files)}")
            
            for source_file in report.source_files:
                total_stats["total_size_bytes"] += source_file.size_bytes
                
                # Document type distribution
                doc_type = source_file.document_type or "unknown"
                total_stats["document_types"][doc_type] = (
                    total_stats["document_types"].get(doc_type, 0) + 1
                )
                
                # File type distribution
                file_type = source_file.file_type
                total_stats["file_types"][file_type] = (
                    total_stats["file_types"].get(file_type, 0) + 1
                )
            
            # Index reports (Qdrant statistics)
            if report.index_reports:
                print(f"\n   🔍 Index Reports:")
                for index_name, index_data in report.index_reports.items():
                    print(f"      {index_name}:")
                    if isinstance(index_data, dict):
                        for key, value in index_data.items():
                            print(f"         {key}: {value}")
            
            # Storage report
            if report.storage_report:
                print(f"\n   💾 Storage Report:")
                for key, value in report.storage_report.items():
                    print(f"      {key}: {value}")
            
            # Import duration
            if job.started_at and job.completed_at:
                duration = (job.completed_at - job.started_at).total_seconds()
                total_stats["import_duration_seconds"].append(duration)
                print(f"\n   ⏱️  Import Duration: {duration:.2f} seconds")
            
            total_stats["total_files"] += job.total_files
            total_stats["supported_files"] += job.supported_files
            total_stats["unsupported_files"] += job.unsupported_files
            
        except Exception as e:
            print(f"   ⚠️  Error getting report: {e}")
    
    # Documents from catalog
    print(f"\n{'='*80}")
    print("📚 DOCUMENT CATALOG ANALYSIS")
    print(f"{'='*80}\n")
    
    documents = doc_catalog.list_documents(corpus_id=corpus_id)
    print(f"Total documents in catalog: {len(documents)}")
    
    if documents:
        # Document statistics
        total_chars = sum(doc.char_count or 0 for doc in documents)
        avg_chars = total_chars / len(documents) if documents else 0
        
        print(f"\n📊 Document Statistics:")
        print(f"   Total characters: {total_chars:,}")
        print(f"   Average characters per document: {avg_chars:,.0f}")
        
        # Document type distribution from catalog
        catalog_doc_types = {}
        for doc in documents:
            doc_type = doc.document_type or "unknown"
            catalog_doc_types[doc_type] = catalog_doc_types.get(doc_type, 0) + 1
        
        print(f"\n📋 Document Type Distribution (from catalog):")
        for doc_type, count in sorted(catalog_doc_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(documents)) * 100
            print(f"   {doc_type}: {count} ({percentage:.1f}%)")
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"Corpus: {corpus.name}")
    print(f"Total Import Jobs: {len(import_jobs)}")
    print(f"Total Files Processed: {total_stats['total_files']}")
    print(f"Supported Files: {total_stats['supported_files']}")
    print(f"Unsupported Files: {total_stats['unsupported_files']}")
    print(f"Total Size: {total_stats['total_size_bytes'] / (1024*1024):.2f} MB")
    print(f"Documents in Catalog: {len(documents)}")
    
    if total_stats["import_duration_seconds"]:
        avg_duration = sum(total_stats["import_duration_seconds"]) / len(total_stats["import_duration_seconds"])
        print(f"Average Import Duration: {avg_duration:.2f} seconds")
    
    print(f"\n📋 File Type Distribution:")
    for file_type, count in sorted(total_stats["file_types"].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_stats["total_files"]) * 100 if total_stats["total_files"] > 0 else 0
        print(f"   {file_type}: {count} ({percentage:.1f}%)")
    
    print(f"\n📄 Document Type Distribution (from import):")
    for doc_type, count in sorted(total_stats["document_types"].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_stats["supported_files"]) * 100 if total_stats["supported_files"] > 0 else 0
        print(f"   {doc_type}: {count} ({percentage:.1f}%)")
    
    return {
        "corpus": corpus.model_dump(),
        "import_jobs_count": len(import_jobs),
        "total_files": total_stats["total_files"],
        "supported_files": total_stats["supported_files"],
        "unsupported_files": total_stats["unsupported_files"],
        "total_size_mb": total_stats["total_size_bytes"] / (1024*1024),
        "documents_count": len(documents),
        "avg_chars_per_document": avg_chars if documents else 0,
        "file_types": total_stats["file_types"],
        "document_types": total_stats["document_types"],
        "catalog_document_types": catalog_doc_types if documents else {},
    }


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_pilot_corpus.py <corpus_id>")
        print("\nTo find corpus_id, use:")
        print("  python -c \"from zaikon.modules.corpus.service import get_corpus_service; print([c.model_dump() for c in get_corpus_service().list_corpora()])\"")
        sys.exit(1)
    
    corpus_id_str = sys.argv[1]
    try:
        corpus_id = UUID(corpus_id_str)
    except ValueError:
        print(f"❌ Invalid UUID: {corpus_id_str}")
        sys.exit(1)
    
    try:
        stats = analyze_corpus(corpus_id)
        
        # Save to JSON
        output_file = Path(__file__).parent.parent / "DOCUMENTS" / "pilot_radni_odnosi" / "analysis_report.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ Analysis saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
