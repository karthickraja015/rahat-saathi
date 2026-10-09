"""Scenario table. All times are offsets from the accident time ACC."""
from datetime import datetime, timedelta

ACC = datetime(2026, 10, 1, 10, 0)


def H(hours=0, minutes=0):
    return ACC + timedelta(hours=hours, minutes=minutes)


NOW = H(3)
LE, AR, LN, NI = "likely_eligible", "at_risk", "likely_not_eligible", "need_more_information"
COL = "district_collector"

BASE = dict(
    accident_at=ACC, motor_vehicle="yes", life_threatening="no", hospitalised_at=H(1),
    hospital_type="designated", police_informed="yes", police_informed_at=H(2),
    hit_and_run="no", insured="yes", state="Tamil Nadu",
)


def sc(sid, status, route="hospital_and_police", now=NOW, codes=(), absent=(), **facts):
    return {"id": sid, "status": status, "route": route, "now": now,
            "codes": tuple(codes), "absent": tuple(absent), "facts": facts}


SCENARIOS = [
    sc("baseline_all_good", LE, codes=["hospitalised_within_24h", "hospital_designated", "police_in_time"]),
    sc("hosp_23h59", LE, now=H(26), hospitalised_at=H(23, 59), codes=["hospitalised_within_24h"]),
    sc("hosp_exactly_24h00", LE, now=H(26), hospitalised_at=H(24), codes=["hospitalised_within_24h"]),
    sc("hosp_24h01", LN, now=H(26), hospitalised_at=H(24, 1), codes=["hospitalised_after_24h"]),
    sc("hosp_3_days_late", LN, now=H(80), hospitalised_at=H(72), codes=["hospitalised_after_24h"]),
    sc("hosp_24h01_life_threatening", LN, now=H(26), hospitalised_at=H(24, 1), life_threatening="yes"),
    sc("lt_police_47h59", LE, now=H(50), life_threatening="yes", police_informed_at=H(48, 59),
       codes=["police_in_time"], absent=["police_late"]),
    sc("lt_police_48h01", AR, COL, now=H(50), life_threatening="yes", police_informed_at=H(49, 1),
       codes=["police_late"]),
    sc("nlt_police_23h59", LE, now=H(26), police_informed_at=H(24, 59), codes=["police_in_time"]),
    sc("nlt_police_24h01", AR, COL, now=H(26), police_informed_at=H(25, 1), codes=["police_late"]),
    sc("lt_unsure_police_late_uses_24h", AR, COL, now=H(26), life_threatening="unsure",
       police_informed_at=H(25, 1), codes=["life_threatening_unsure", "police_late"]),
    sc("lt_unsure_otherwise_ok", NI, life_threatening="unsure", codes=["life_threatening_unsure"]),
    sc("lt_missing", NI, life_threatening=None, codes=["life_threatening_missing"]),
    sc("lt_yes_ok", LE, life_threatening="yes"),
    sc("no_motor_vehicle", LN, motor_vehicle="no", codes=["no_motor_vehicle"]),
    sc("motor_vehicle_unsure", NI, motor_vehicle="unsure", codes=["motor_vehicle_unsure"]),
    sc("motor_vehicle_missing", NI, motor_vehicle=None, codes=["motor_vehicle_missing"]),
    sc("accident_time_missing", NI, accident_at=None, hospitalised_at=None, police_informed_at=None,
       codes=["accident_time_missing"]),
    sc("hospitalisation_time_missing", NI, hospitalised_at=None, codes=["hospitalisation_time_missing"]),
    sc("hospitalised_before_accident", NI, hospitalised_at=H(-2),
       codes=["hospitalisation_before_accident"], absent=["hospitalised_after_24h"]),
    sc("hit_and_run", LE, COL, hit_and_run="yes", codes=["hit_and_run_collector"]),
    sc("hit_and_run_unsure", LE, hit_and_run="unsure", codes=["hit_and_run_unknown"]),
    sc("uninsured", LE, COL, insured="no", codes=["uninsured_collector"]),
    sc("insured_unsure", LE, insured="unsure", codes=["insured_unknown"]),
    sc("insured_missing", LE, insured=None, absent=["insured_unknown", "uninsured_collector"]),
    sc("non_designated_early", AR, COL, hospital_type="non_designated",
       codes=["non_designated_stabilisation_only"], absent=["stabilisation_window_ended"]),
    sc("non_designated_after_stabilisation", AR, COL, now=H(30), hospital_type="non_designated",
       codes=["stabilisation_window_ended"]),
    sc("hospital_not_sure", NI, hospital_type="not_sure", codes=["hospital_type_unsure"]),
    sc("hospital_missing", NI, hospital_type=None, codes=["hospital_type_missing"]),
    sc("police_no_pending", AR, police_informed="no", police_informed_at=None, codes=["police_pending"]),
    sc("police_no_timeout", AR, COL, now=H(26), police_informed="no", police_informed_at=None,
       codes=["police_timeout"]),
    sc("police_unsure", NI, police_informed="unsure", police_informed_at=None, codes=["police_unsure"]),
    sc("police_missing", NI, police_informed=None, police_informed_at=None, codes=["police_missing"]),
    sc("police_yes_time_missing", NI, police_informed_at=None, codes=["police_time_missing"]),
    sc("cover_ended_8_days", AR, now=H(24 * 8), codes=["cover_window_ended"]),
    sc("cover_boundary_exact_7d", LE, now=H(168), absent=["cover_window_ended"]),
    sc("cover_boundary_7d_plus_1min", AR, now=H(168, 1), codes=["cover_window_ended"]),
    sc("accident_in_future", NI, accident_at=H(4), hospitalised_at=H(5), codes=["accident_in_future"]),
    sc("hospitalisation_in_future", NI, hospitalised_at=H(5), codes=["hospitalisation_in_future"]),
    sc("stacked_collector_triggers", AR, COL, hospital_type="non_designated", hit_and_run="yes",
       insured="no", codes=["non_designated_stabilisation_only", "hit_and_run_collector", "uninsured_collector"]),
    sc("not_eligible_beats_at_risk", LN, now=H(31), hospitalised_at=H(30), police_informed="no",
       police_informed_at=None, codes=["hospitalised_after_24h", "police_pending"]),
    sc("not_eligible_beats_missing_info", LN, now=H(31), hospitalised_at=H(30), life_threatening=None),
    sc("not_eligible_still_routes_collector", LN, COL, now=H(31), hospitalised_at=H(30), insured="no"),
    sc("state_missing_is_fine", LE, state=None),
    sc("lt_police_pending_47h59", AR, now=H(48, 59), life_threatening="yes", police_informed="no",
       police_informed_at=None, codes=["police_pending"], absent=["police_timeout"]),
    sc("lt_police_timeout_48h01", AR, COL, now=H(49, 1), life_threatening="yes", police_informed="no",
       police_informed_at=None, codes=["police_timeout"]),
    sc("nlt_police_pending_23h59", AR, now=H(24, 59), police_informed="no", police_informed_at=None,
       codes=["police_pending"], absent=["police_timeout"]),
    sc("nlt_police_timeout_24h01", AR, COL, now=H(25, 1), police_informed="no", police_informed_at=None,
       codes=["police_timeout"]),
    sc("lt_nondesignated_stab_47h59", AR, COL, now=H(48, 59), life_threatening="yes",
       hospital_type="non_designated", absent=["stabilisation_window_ended"]),
    sc("lt_nondesignated_stab_48h01", AR, COL, now=H(49, 1), life_threatening="yes",
       hospital_type="non_designated", codes=["stabilisation_window_ended"]),
    sc("nlt_nondesignated_stab_23h59", AR, COL, now=H(24, 59), hospital_type="non_designated",
       absent=["stabilisation_window_ended"]),
    sc("nlt_nondesignated_stab_24h01", AR, COL, now=H(25, 1), hospital_type="non_designated",
       codes=["stabilisation_window_ended"]),
    sc("lt_unsure_nondesignated_uses_24h", AR, COL, now=H(25, 1), life_threatening="unsure",
       hospital_type="non_designated", codes=["stabilisation_window_ended", "life_threatening_unsure"]),
]
