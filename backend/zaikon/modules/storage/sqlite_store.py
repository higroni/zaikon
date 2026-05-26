"""SQLite mirror store for persisted canonical documents."""

import json
import sqlite3
from pathlib import Path
from typing import Any


class SQLiteDocumentStore:
    """Stores document summaries and canonical JSON in SQLite."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def upsert_document(self, record: dict[str, Any], canonical_json: dict) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    document_id,
                    corpus_id,
                    source_uri,
                    filename,
                    document_type,
                    title,
                    canonical_json,
                    publication_metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    corpus_id=excluded.corpus_id,
                    source_uri=excluded.source_uri,
                    filename=excluded.filename,
                    document_type=excluded.document_type,
                    title=excluded.title,
                    canonical_json=excluded.canonical_json,
                    publication_metadata=excluded.publication_metadata
                """,
                (
                    record["document_id"],
                    record.get("corpus_id"),
                    record["source_uri"],
                    record["filename"],
                    record["document_type"],
                    record.get("title"),
                    json.dumps(canonical_json, ensure_ascii=False),
                    json.dumps(record.get("publication_metadata", {}), ensure_ascii=False),
                ),
            )

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM documents WHERE document_id = ?",
                (document_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            **dict(row),
            "canonical_json": json.loads(row["canonical_json"]),
            "publication_metadata": json.loads(row["publication_metadata"]),
        }

    def list_documents(self, corpus_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM documents"
        params: tuple[str, ...] = ()
        if corpus_id is not None:
            query += " WHERE corpus_id = ?"
            params = (corpus_id,)
        query += " ORDER BY filename"
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(query, params).fetchall()
        return [
            {
                **dict(row),
                "canonical_json": json.loads(row["canonical_json"]),
                "publication_metadata": json.loads(row["publication_metadata"]),
            }
            for row in rows
        ]

    def _initialize(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    corpus_id TEXT,
                    source_uri TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    title TEXT,
                    canonical_json TEXT NOT NULL,
                    publication_metadata TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_corpus_id ON documents(corpus_id)"
            )
