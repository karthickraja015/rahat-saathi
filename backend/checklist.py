"""Document checklist (common documents, not an official list)."""
from __future__ import annotations


def build_checklist(facts, result=None) -> list:
    return [
        {"group": "hospital", "items": ["id_proof", "admission_papers", "bills", "medical_records"]},
        {"group": "police", "items": ["ack_112", "police_report", "accident_id", "other_vehicle"]},
        {"group": "insurance", "items": ["policy", "licence_rc", "scene_photos", "bank_details"]},
    ]
