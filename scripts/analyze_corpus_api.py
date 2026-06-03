#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skripta za statističku analizu korpusa kroz API.
"""

import io
import json
import sys
import requests
from uuid import UUID

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

API_BASE = "http://localhost:8100/api/v1"


def analyze_corpus(corpus_id: str):
    """Analizira korpus kroz API."""
    
    print(f"\n{'='*80}")
    print(f"ANALIZA KORPUSA")
    print(f"{'='*80}\n")
    
    # Get corpus info
    print("📊 Dohvatam informacije o korpusu...")
    resp = requests.get(f"{API_BASE}/corpora/{corpus_id}")
    if resp.status_code != 200:
        print(f"❌ Greška: {resp.status_code} - {resp.text}")
        return
    
    corpus = resp.json()
    print(f"\n✅ Korpus: {corpus['name']}")
    print(f"   ID: {corpus['corpus_id']}")
    print(f"   Opis: {corpus.get('description', 'N/A')}")
    print(f"   Jezik: {corpus['language_code']}")
    print(f"   Kreiran: {corpus['created_at']}")
    
    # Get import jobs
    print(f"\n📦 Dohvatam import job-ove...")
    resp = requests.get(f"{API_BASE}/corpora/{corpus_id}/import-jobs")
    if resp.status_code != 200:
        print(f"❌ Greška: {resp.status_code} - {resp.text}")
        return
    
    import_jobs = resp.json()
    print(f"✅ Pronađeno {len(import_jobs)} import job(ova)")
    
    if not import_jobs:
        print("\n⚠️  Nema import job-ova za ovaj korpus")
        return
    
    # Analyze each import job
    total_stats = {
        "total_files": 0,
        "supported_files": 0,
        "unsupported_files": 0,
        "document_types": {},
        "file_types": {},
    }
    
    for job in import_jobs:
        print(f"\n{'='*80}")
        print(f"Import Job: {job['import_job_id']}")
        print(f"{'='*80}")
        print(f"Status: {job['status']}")
        print(f"Total files: {job['total_files']}")
        print(f"Supported: {job['supported_files']}")
        print(f"Unsupported: {job['unsupported_files']}")
        print(f"Started: {job['started_at']}")
        print(f"Completed: {job.get('completed_at', 'N/A')}")
        
        # Get detailed report
        print(f"\n📄 Dohvatam detaljan report...")
        resp = requests.get(f"{API_BASE}/import-jobs/{job['import_job_id']}/report")
        if resp.status_code != 200:
            print(f"⚠️  Greška pri dohvatanju reporta: {resp.status_code}")
            continue
        
        report_data = resp.json()
        report = report_data['report']
        
        # Summary
        if 'summary' in report:
            print(f"\n📈 Summary:")
            for key, value in report['summary'].items():
                print(f"   {key}: {value}")
        
        # Source files
        source_files = report.get('source_files', [])
        print(f"\n📚 Source Files: {len(source_files)}")
        
        for sf in source_files:
            doc_type = sf.get('document_type') or 'unknown'
            total_stats["document_types"][doc_type] = (
                total_stats["document_types"].get(doc_type, 0) + 1
            )
            
            file_type = sf.get('file_type', 'unknown')
            total_stats["file_types"][file_type] = (
                total_stats["file_types"].get(file_type, 0) + 1
            )
        
        # Index reports
        if 'index_reports' in report and report['index_reports']:
            print(f"\n🔍 Index Reports:")
            for index_name, index_data in report['index_reports'].items():
                print(f"   {index_name}:")
                if isinstance(index_data, dict):
                    for key, value in index_data.items():
                        print(f"      {key}: {value}")
        
        # Storage report
        if 'storage_report' in report and report['storage_report']:
            print(f"\n💾 Storage Report:")
            for key, value in report['storage_report'].items():
                print(f"   {key}: {value}")
        
        total_stats["total_files"] += job['total_files']
        total_stats["supported_files"] += job['supported_files']
        total_stats["unsupported_files"] += job['unsupported_files']
    
    # Get documents from catalog
    print(f"\n{'='*80}")
    print("📚 DOCUMENT CATALOG")
    print(f"{'='*80}\n")
    
    resp = requests.get(f"{API_BASE}/documents", params={"corpus_id": corpus_id})
    if resp.status_code == 200:
        documents = resp.json()
        print(f"✅ Total documents in catalog: {len(documents)}")
        
        if documents:
            total_chars = sum(doc.get('char_count', 0) for doc in documents)
            avg_chars = total_chars / len(documents) if documents else 0
            
            print(f"\n📊 Document Statistics:")
            print(f"   Total characters: {total_chars:,}")
            print(f"   Average characters per document: {avg_chars:,.0f}")
            
            # Document type distribution from catalog
            catalog_doc_types = {}
            for doc in documents:
                doc_type = doc.get('document_type') or 'unknown'
                catalog_doc_types[doc_type] = catalog_doc_types.get(doc_type, 0) + 1
            
            print(f"\n📋 Document Type Distribution (from catalog):")
            for doc_type, count in sorted(catalog_doc_types.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(documents)) * 100
                print(f"   {doc_type}: {count} ({percentage:.1f}%)")
    else:
        print(f"⚠️  Greška pri dohvatanju dokumenata: {resp.status_code}")
        documents = []
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"Corpus: {corpus['name']}")
    print(f"Total Import Jobs: {len(import_jobs)}")
    print(f"Total Files Processed: {total_stats['total_files']}")
    print(f"Supported Files: {total_stats['supported_files']}")
    print(f"Unsupported Files: {total_stats['unsupported_files']}")
    print(f"Documents in Catalog: {len(documents)}")
    
    if total_stats["file_types"]:
        print(f"\n📋 File Type Distribution:")
        for file_type, count in sorted(total_stats["file_types"].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_stats["total_files"]) * 100 if total_stats["total_files"] > 0 else 0
            print(f"   {file_type}: {count} ({percentage:.1f}%)")
    
    if total_stats["document_types"]:
        print(f"\n📄 Document Type Distribution (from import):")
        for doc_type, count in sorted(total_stats["document_types"].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_stats["supported_files"]) * 100 if total_stats["supported_files"] > 0 else 0
            print(f"   {doc_type}: {count} ({percentage:.1f}%)")
    
    # Save to JSON
    output = {
        "corpus": corpus,
        "import_jobs_count": len(import_jobs),
        "total_files": total_stats["total_files"],
        "supported_files": total_stats["supported_files"],
        "unsupported_files": total_stats["unsupported_files"],
        "documents_count": len(documents),
        "file_types": total_stats["file_types"],
        "document_types": total_stats["document_types"],
    }
    
    output_file = f"corpus_analysis_{corpus_id}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Analysis saved to: {output_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_corpus_api.py <corpus_id>")
        sys.exit(1)
    
    corpus_id = sys.argv[1]
    
    try:
        UUID(corpus_id)
    except ValueError:
        print(f"❌ Invalid UUID: {corpus_id}")
        sys.exit(1)
    
    try:
        analyze_corpus(corpus_id)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
