"""Document checklist (common documents, not an official list)."""
from __future__ import annotations


def build_checklist(facts, result=None) -> list:
    groups = [
        {"group": "hospital", "items": ["id_proof", "admission_papers", "bills", "medical_records"]},
        {"group": "police", "items": ["police_report", "accident_id", "other_vehicle"]},
        {"group": "insurance", "items": ["policy", "licence_rc", "scene_photos", "bank_details"]},
    ]
    collector = (
        (result is not None and result.escalation.route == "district_collector")
        or facts.hit_and_run == "yes"
        or facts.insured == "no"
    )
    if collector:
        groups.append({"group": "collector", "items": ["written_application", "copies", "witness"]})
    return groups
