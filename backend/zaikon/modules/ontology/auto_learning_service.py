"""Auto-learning ontology service that learns from NER extractions."""

import logging
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from zaikon.core.config import settings
from zaikon.modules.ner.schemas import NERSlot

logger = logging.getLogger(__name__)


class AutoLearningOntologyService:
    """Service that automatically learns ontology terms from NER extractions."""
    
    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            artifact_dir = Path(settings.artifact_dir)
            if not artifact_dir.is_absolute():
                artifact_dir = settings.base_dir / artifact_dir
            self.db_path = artifact_dir / "zaikon.db"
        else:
            self.db_path = db_path
        self._ensure_tables()
    
    def _ensure_tables(self) -> None:
        """Create ontology tables if they don't exist."""
        migration_file = Path(__file__).parent / "migrations" / "001_create_ontology_tables.sql"
        if migration_file.exists():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executescript(migration_file.read_text(encoding="utf-8"))
            conn.commit()
            conn.close()
            logger.info("Ontology tables created/verified")
    
    def learn_from_ner_slot(
        self,
        slot: NERSlot,
        term_type: str,  # 'actor', 'action', 'object'
        min_confidence: float = 0.75,
        min_frequency: int = 3,
    ) -> bool:
        """Learn a new term from NER extraction.
        
        Args:
            slot: NER slot with text, lemma, confidence
            term_type: Type of term (actor, action, object)
            min_confidence: Minimum confidence to add term
            min_frequency: Minimum frequency before promoting to ontology
            
        Returns:
            True if term was added/updated, False otherwise
        """
        if slot.confidence < min_confidence:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if term already exists
            cursor.execute(
                """
                SELECT term_id, frequency, confidence 
                FROM ontology_terms 
                WHERE term_type = ? AND canonical = ? AND label = ?
                """,
                (term_type, slot.lemma, slot.text)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update frequency and confidence
                term_id, frequency, old_confidence = existing
                new_frequency = frequency + 1
                # Weighted average of confidences
                new_confidence = (old_confidence * frequency + slot.confidence) / new_frequency
                
                cursor.execute(
                    """
                    UPDATE ontology_terms 
                    SET frequency = ?, confidence = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE term_id = ?
                    """,
                    (new_frequency, new_confidence, term_id)
                )
                
                logger.debug(
                    f"Updated {term_type} '{slot.lemma}' (freq: {new_frequency}, conf: {new_confidence:.2f})"
                )
            else:
                # Insert new term
                term_id = str(uuid4())
                cursor.execute(
                    """
                    INSERT INTO ontology_terms 
                    (term_id, term_type, canonical, label, confidence, frequency, source)
                    VALUES (?, ?, ?, ?, ?, 1, 'ner')
                    """,
                    (term_id, term_type, slot.lemma, slot.text, slot.confidence)
                )
                
                logger.info(
                    f"Learned new {term_type} '{slot.lemma}' from NER (conf: {slot.confidence:.2f})"
                )
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to learn term from NER: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_term(self, term_type: str, label: str) -> dict[str, Any] | None:
        """Get term from ontology by label.
        
        Args:
            term_type: Type of term (actor, action, object)
            label: Label to search for
            
        Returns:
            Term dict or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT term_id, canonical, label, confidence, frequency, source
            FROM ontology_terms
            WHERE term_type = ? AND label = ?
            ORDER BY frequency DESC, confidence DESC
            LIMIT 1
            """,
            (term_type, label)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "term_id": row[0],
                "canonical": row[1],
                "label": row[2],
                "confidence": row[3],
                "frequency": row[4],
                "source": row[5],
            }
        return None
    
    def get_top_terms(
        self,
        term_type: str,
        min_frequency: int = 3,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get top terms by frequency.
        
        Args:
            term_type: Type of term (actor, action, object)
            min_frequency: Minimum frequency threshold
            limit: Maximum number of terms to return
            
        Returns:
            List of term dicts sorted by frequency
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT term_id, canonical, label, confidence, frequency, source
            FROM ontology_terms
            WHERE term_type = ? AND frequency >= ?
            ORDER BY frequency DESC, confidence DESC
            LIMIT ?
            """,
            (term_type, min_frequency, limit)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "term_id": row[0],
                "canonical": row[1],
                "label": row[2],
                "confidence": row[3],
                "frequency": row[4],
                "source": row[5],
            }
            for row in rows
        ]
    
    def export_to_json(self, output_path: Path, min_frequency: int = 5) -> dict[str, Any]:
        """Export learned ontology to JSON format.
        
        Args:
            output_path: Path to save JSON file
            min_frequency: Minimum frequency to include term
            
        Returns:
            Exported ontology dict
        """
        import json
        
        ontology = {
            "version": "auto-learned",
            "language": "sr",
            "actors": {},
            "actions": {},
            "objects": {},
            "domains": {},
        }
        
        for term_type in ["actor", "action", "object"]:
            terms = self.get_top_terms(term_type, min_frequency=min_frequency)
            
            # Group by canonical
            canonical_groups: dict[str, list[str]] = {}
            for term in terms:
                canonical = term["canonical"]
                label = term["label"]
                if canonical not in canonical_groups:
                    canonical_groups[canonical] = []
                if label not in canonical_groups[canonical]:
                    canonical_groups[canonical].append(label)
            
            # Add to ontology
            term_key = f"{term_type}s"
            for canonical, labels in canonical_groups.items():
                ontology[term_key][canonical] = {
                    "labels": labels,
                    "source": "auto-learned"
                }
        
        # Save to file
        output_path.write_text(json.dumps(ontology, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Exported ontology to {output_path}")
        
        return ontology
    
    def get_statistics(self) -> dict[str, Any]:
        """Get ontology learning statistics.
        
        Returns:
            Statistics dict with counts and frequencies
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        for term_type in ["actor", "action", "object"]:
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN frequency >= 5 THEN 1 END) as high_freq,
                    COUNT(CASE WHEN frequency >= 10 THEN 1 END) as very_high_freq,
                    AVG(frequency) as avg_freq,
                    AVG(confidence) as avg_conf
                FROM ontology_terms
                WHERE term_type = ?
                """,
                (term_type,)
            )
            
            row = cursor.fetchone()
            stats[term_type] = {
                "total": row[0],
                "high_frequency": row[1],  # >= 5
                "very_high_frequency": row[2],  # >= 10
                "avg_frequency": round(row[3], 2) if row[3] else 0,
                "avg_confidence": round(row[4], 2) if row[4] else 0,
            }
        
        conn.close()
        return stats


def get_auto_learning_service() -> AutoLearningOntologyService:
    """Get singleton auto-learning ontology service."""
    return AutoLearningOntologyService()

# Made with Bob
