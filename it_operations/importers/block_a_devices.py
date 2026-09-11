import ipaddress
import re
from collections import Counter

import frappe


SOURCE_TOTAL = 85
SOURCE_BLOCK_A_TOTAL = 55
SOURCE_OTHER_BLOCK_TOTAL = 30
SOC_CAMPUS = "SOC Campus"
BLOCK_A = "Block A"
BLOCK_A_CODE = "BLOCK-A"

DEVICE_FIELDS = (
	"source_number",
	"source_type",
	"model",
	"ip_address",
	"short_serial",
	"serial_number",
	"device_name",
	"web_version",
	"mac_address",
)

BLOCK_A_DEVICES = (
	(30, "IP Camera", "DS-2CD1047G2-L", "192.168.24.189", "AB3711119", "DS-2CD1047G2-L20230517AAWRAB3711119", "IP CAMERA", "V5.7.11build 230414", "fc:9f:fd:8f:69:3b"),
	(31, "IP Camera", "DS-2CD1143G2-LIU", "192.168.24.194", "GG3006764", "DS-2CD1143G2-LIU20250923AAWRGG3006764", "IP CAMERA", "V5.8.10build 250714", "0c:75:d2:96:92:5e"),
	(32, "IP Camera", "DS-2CD1143G2-LIU", "192.168.24.193", "GG3006762", "DS-2CD1143G2-LIU20250923AAWRGG3006762", "IP CAMERA", "V5.8.10build 250714", "0c:75:d2:96:92:5c"),
	(33, "IP Camera", "DS-2CD1047G2-L", "192.168.24.192", "AB3711276", "DS-2CD1047G2-L20230517AAWRAB3711276", "IP CAMERA", "V5.7.11build 230414", "fc:9f:fd:8f:69:d8"),
	(34, "IP Camera", "DS-2CD1143G2-LIU", "192.168.24.196", "GG3006756", "DS-2CD1143G2-LIU20250923AAWRGG3006756", "IP CAMERA", "V5.8.10build 250714", "0c:75:d2:96:92:56"),
	(35, "IP Camera", "DS-2CD1143G2-LIU", "192.168.24.195", "GG3006754", "DS-2CD1143G2-LIU20250923AAWRGG3006754", "IP CAMERA", "V5.8.10build 250714", "0c:75:d2:96:92:54"),
	(36, "IP Camera", "DS-2CD1143G0E-I", "192.168.24.186", "E58068917", "DS-2CD1143G0E-I20200708AAWRE58068917", "IP CAMERA", "V5.5.114build 200417", "10:12:fb:44:de:ac"),
	(37, "Network Switch", "DS-3E1310P-EI/M", "192.168.24.190", "GF2364281", "DS-3E1310P-EI/M20250905CRRGF2364281", "DS-3E1310P-EI/M", "V3.0.9build 250115", "84:94:59:09:11:a1"),
	(38, "IP Camera", "DS-2CD1143G0-IUF", "192.168.24.175", "J62513771", "DS-2CD1143G0-IUF20220324AAWRJ62513771", "(B01AF0-AR11) 9I (2-028)", "V5.7.2build 211230", "40:ac:bf:91:9c:2f"),
	(39, "IP Camera", "DS-2CD1143G0-IUF", "192.168.24.174", "J62513758", "DS-2CD1143G0-IUF20220324AAWRJ62513758", "(B01AF0-AR12) 9C (2-026)", "V5.7.2build 211230", "40:ac:bf:91:9c:22"),
	(40, "Network Video Recorder", "DS-7616NI-Q2/16P", "192.168.24.183", "G24476887", "DS-7616NI-Q2/16P1620210706CCRRG24476887WCVU", "Network Video Recorder", "V4.75.200build 231110", "24:28:fd:12:3d:37"),
	(41, "IP Camera", "DS-2CD1143G0-IUF", "192.168.24.164", "J62513794", "DS-2CD1143G0-IUF20220324AAWRJ62513794", "(B01F0-AR06) ICT LAB (2-031)", "V5.7.2build 211230", "40:ac:bf:91:9c:46"),
	(42, "IP Camera", "DS-2CD1043G0E-I", "192.168.24.173", "E65851985", "DS-2CD1043G0E-I20200804AAWRE65851985", "GIRLS DORM VIEW (2-036)", "V5.5.114build 200417", "10:12:fb:80:15:24"),
	(43, "IP Camera", "DS-2CD1043G0E-I", "192.168.24.181", "E64770770", "DS-2CD1043G0E-I20200813AAWRE64770770", "Boys Dorm View (2-041)", "V5.5.114build 200417", "10:12:fb:77:e4:b5"),
	(44, "IP Camera", "DS-2CD1147G2H-LIU", "192.168.24.185", "FB2224965", "DS-2CD1147G2H-LIU20240312AAWRFB2224965", "EATING AREA DIASPORA (2-009)", "V5.7.13build 230815", "04:03:12:4d:3e:cc"),
	(45, "IP Camera", "DS-2CD1143G0-IUF", "192.168.24.141", "J62513833", "DS-2CD1143G0-IUF20220324AAWRJ62513833", "(B01AF0-AR14) 9H (2-024)", "V5.7.2build 211230", "40:ac:bf:91:9c:6d"),
	(46, "IP Camera", "DS-2CD1147G2H-LIU", "192.168.24.184", "FB2224983", "DS-2CD1147G2H-LIU20240312AAWRFB2224983", "Staff Eating Area 1 (2-027)", "V5.7.13build 230815", "04:03:12:4d:3e:de"),
	(47, "Network Video Recorder", "DS-7616NI-Q2/16P", "192.168.24.182", "G24498274", "DS-7616NI-Q2/16P1620210705CCRRG24498274WCVU", "Network Video Recorder", "V4.75.200build 231110", "24:28:fd:12:7f:be"),
	(48, "IP Camera", "DS-2CD1143G0-IUF", "192.168.24.146", "J62513827", "DS-2CD1143G0-IUF20220324AAWRJ62513827", "(B01F0-AR02) 8G (2-011)", "V5.7.2build 211230", "40:ac:bf:91:9c:67"),
	(49, "IP Camera", "DS-2CD1143G0-IUF", "192.168.24.170", "J62513765", "DS-2CD1143G0-IUF20220324AAWRJ62513765", "(B01F0-AR04) 9F (2-034)", "V5.7.2build 211230", "40:ac:bf:91:9c:29"),
	(50, "IP Camera", "DS-2CD1143G0-IUF", "192.168.24.176", "J62513783", "DS-2CD1143G0-IUF20220324AAWRJ62513783", "B01AF0-AR9 8S (2-037)", "V5.7.2build 211230", "40:ac:bf:91:9c:3b"),
	(51, "IP Camera", "DS-2CD1143G0-I", "192.168.24.179", "E09904146", "DS-2CD1143G0-I20200113AAWRE09904146", "B01F0-AR22 (8H)", "V5.5.82build 190130", "ac:cb:51:0d:46:b6"),
	(52, "IP Camera", "DS-2CD1143G0-I", "192.168.24.178", "E09904105", "DS-2CD1143G0-I20200113AAWRE09904105", "B01F0-AR24 7S (2-039)", "V5.5.82build 190130", "ac:cb:51:0d:46:8d"),
	(53, "IP Camera", "DS-2CD1143G0-IUF", "192.168.24.140", "J62513802", "DS-2CD1143G0-IUF20220324AAWRJ62513802", "B01F0-AR02 8G (2-045)", "V5.7.2build 211230", "40:ac:bf:91:9c:4e"),
	(54, "IP Camera", "DS-2CD1143G0-IUF", "192.168.24.147", "J62513746", "DS-2CD1143G0-IUF20220324AAWRJ62513746", "(B01F0-AR03) 8C (2-012)", "V5.7.2build 211230", "40:ac:bf:91:9c:16"),
	(55, "IP Camera", "DS-2CD1143G0-IUF", "192.168.24.161", "J62513770", "DS-2CD1143G0-IUF20220324AAWRJ62513770", "(B01AF0-AR13) 9G (2-025)", "V5.7.2build 211230", "40:ac:bf:91:9c:2e"),
	(56, "IP Camera", "DS-2CD1143G0-I", "192.168.24.172", "E09904068", "DS-2CD1143G0-I20200113AAWRE09904068", "BOYS WASH ROOM AREA (2-035)", "V5.5.82build 190130", "ac:cb:51:0d:46:68"),
	(57, "IP Camera", "DS-2CD1143G0-IUF", "192.168.24.159", "J62513793", "DS-2CD1143G0-IUF20220324AAWRJ62513793", "(B01AF0-AR15) 9S (2-023)", "V5.7.2build 211230", "40:ac:bf:91:9c:45"),
	(58, "IP Camera", "DS-2CD1143G0-I", "192.168.24.171", "E09904092", "DS-2CD1143G0-I20200113AAWRE09904092", "B01F0-AR20 SERVER ROOM (2-044)", "V5.5.82build 190130", "ac:cb:51:0d:46:80"),
	(59, "IP Camera", "DS-2CD1143G0E-I", "192.168.24.156", "E58068924", "DS-2CD1143G0E-I20200708AAWRE58068924", "MPH MIDDLE CAM (2-020)", "V5.5.114build 200417", "10:12:fb:44:de:b3"),
	(60, "IP Camera", "DS-2CD1143G0E-I", "192.168.24.136", "E58068901", "DS-2CD1143G0E-I20200708AAWRE58068901", "B01F0-AR18 (2-002)", "V5.5.114build 200417", "10:12:fb:44:de:9c"),
	(61, "IP Camera", "DS-2CD1143G0E-I", "192.168.24.157", "E58068913", "DS-2CD1143G0E-I20200708AAWRE58068913", "MPH BACK CAM (2-021)", "V5.5.114build 200417", "10:12:fb:44:de:a8"),
	(62, "IP Camera", "DS-2CD1143G0-I", "192.168.24.163", "E09904184", "DS-2CD1143G0-I20200113AAWRE09904184", "B01F0-AR05 HOME SCIENCE (2-030)", "V5.5.82build 190130", "ac:cb:51:0d:46:dc"),
	(63, "IP Camera", "DS-2CD1143G0E-I", "192.168.24.145", "E58068925", "DS-2CD1143G0E-I20200708AAWRE58068925", "(B01F0-AR01) JHS STAFF RM(2-010)", "V5.5.114build 200417", "10:12:fb:44:de:b4"),
	(64, "IP Camera", "DS-2CD1143G0E-I", "192.168.24.138", "E58068916", "DS-2CD1143G0E-I20200708AAWRE58068916", "(B01F0-AR19) LIBRARY (2-004)", "V5.5.114build 200417", "10:12:fb:44:de:ab"),
	(65, "IP Camera", "DS-2CD1143G0-I", "192.168.24.165", "F84329765", "DS-2CD1143G0-I20210412AAWRF84329765", "MPT Back View (2-032)", "V5.5.88build 200610", "08:a1:89:d6:85:40"),
	(66, "IP Camera", "DS-2CD1143G0-I", "192.168.24.169", "E09904181", "DS-2CD1143G0-I20200113AAWRE09904181", "B01F0-AR25 7G (2-046)", "V5.5.82build 190130", "ac:cb:51:0d:46:d9"),
	(67, "IP Camera", "DS-2CD1043G0E-I", "192.168.24.149", "E65852003", "DS-2CD1043G0E-I20200804AAWRE65852003", "VIEW FROM PHYSICS LAB (2-014)", "V5.5.114build 200417", "10:12:fb:80:15:36"),
	(68, "IP Camera", "DS-2CD1043G0E-I", "192.168.24.158", "E64770760", "DS-2CD1043G0E-I20200813AAWRE64770760", "VIEW FROM OLD INFIRMARY (2-022)", "V5.5.114build 200417", "10:12:fb:77:e4:ab"),
	(69, "IP Camera", "DS-2CD1147G2H-LIU", "192.168.24.135", "FB2225111", "DS-2CD1147G2H-LIU20240312AAWRFB2225111", "STORES VIEW (2-048)", "V5.7.13build 230815", "04:03:12:4d:3f:5e"),
	(70, "IP Camera", "DS-2CD1043G0E-I", "192.168.24.139", "E65851991", "DS-2CD1043G0E-I20200804AAWRE65851991", "IP CAMERA", "V5.5.114build 200417", "10:12:fb:80:15:2a"),
	(71, "IP Camera", "DS-2CD1143G0E-I", "192.168.24.137", "E58068940", "DS-2CD1143G0E-I20200708AAWRE58068940", "LIBRARY CAM 1", "V5.5.114build 200417", "10:12:fb:44:de:c3"),
	(72, "IP Camera", "DS-2CD1043G0E-I", "192.168.24.132", "E65851992", "DS-2CD1043G0E-I20200804AAWRE65851992", "CAR PARK/FIELD VIEW", "V5.5.114build 200417", "10:12:fb:80:15:2b"),
	(73, "IP Camera", "DS-2CD1143G0E-I", "192.168.24.148", "E58068921", "DS-2CD1143G0E-I20200708AAWRE58068921", "(B01F0-AR04) PHYSICS LAB (2-013)", "V5.5.114build 200417", "10:12:fb:44:de:b0"),
	(74, "IP Camera", "DS-2CD2043G0-I", "192.168.24.144", "E21780075", "DS-2CD2043G0-I20200311AAWRE21780075", "STORES PERIMETER VIEW (2-029)", "V5.6.2build 190701", "ac:cb:51:4d:7d:b5"),
	(75, "IP Camera", "DS-2CD2043G0-I", "192.168.24.142", "E21780212", "DS-2CD2043G0-I20200311AAWRE21780212", "STAFF ROOM COR VIEW (2-007)", "V5.6.2build 190701", "ac:cb:51:4d:7e:3e"),
	(76, "IP Camera", "DS-2CD1143G0-I", "192.168.24.134", "F84329897", "DS-2CD1143G0-I20210412AAWRF84329897", "IP CAMERA", "V5.5.88build 200610", "08:a1:89:d6:85:c4"),
	(77, "IP Camera", "DS-2CD1143G0-I", "192.168.24.133", "E09904041", "DS-2CD1143G0-I20200113AAWRE09904041", "B01F0-AR19 STORE ROOM (2-043)", "V5.5.82build 190130", "ac:cb:51:0d:46:4d"),
	(78, "IP Camera", "DS-2CD2043G0-I", "192.168.24.143", "E21780216", "DS-2CD2043G0-I20200311AAWRE21780216", "JHS ENTRANCE VIEW (2-008)", "V5.6.2build 190701", "ac:cb:51:4d:7e:42"),
	(79, "IP Camera", "DS-2CD1143G0-I", "192.168.24.152", "D63749348", "DS-2CD1143G0-I20190921AAWRD63749348", "KITCHEN COOKING AR2 (2-017)", "V5.5.82build 190130", "bc:ba:c2:f5:17:77"),
	(80, "IP Camera", "DS-2CD1143G0-I", "192.168.24.155", "D63749569", "DS-2CD1143G0-I20190921AAWRD63749569", "MPH FRONT CAM  (2-019)", "V5.5.82build 190130", "bc:ba:c2:f5:18:54"),
	(81, "IP Camera", "DS-2CD1147G2-L", "192.168.24.153", "AB3881546", "DS-2CD1147G2-L20230517AAWRAB3881546", "KITCHEN COOKING AREA (2-006)", "V5.7.11build 230414", "fc:9f:fd:90:b9:37"),
	(82, "Unknown", "DS-7732NI-K4", "192.168.24.130", "E26407509", "DS-7732NI-K41620200402CCRRE26407509WCVU", "JHS NVR 1", "V3.4.108build 200102", "98:df:82:d4:1b:01"),
	(83, "Unknown", "DS-7732NI-K4", "192.168.24.131", "E26407555", "DS-7732NI-K41620200402CCRRE26407555WCVU", "Network Video Recorder", "V3.4.108build 200102", "98:df:82:d4:1b:2f"),
	(84, "IP Camera", "DS-2CD1143G0E-I", "192.168.24.154", "E58068937", "DS-2CD1143G0E-I20200708AAWRE58068937", "(B01F0-AR07) CHEMISTRY (2-018)", "V5.5.114build 200417", "10:12:fb:44:de:c0"),
)

MAC_PATTERN = re.compile(r"^(?:[0-9a-f]{2}:){5}[0-9a-f]{2}$", re.IGNORECASE)


def import_block_a_devices(dry_run=True):
	"""Safely import the supplied SOC Block A inventory without updating existing records."""
	dry_run = _as_bool(dry_run)
	_validate_structure()
	campus = _get_soc_campus()
	block = _get_block_a(campus.name)
	location_status = "Existing" if block else ("Would Create" if dry_run else "Created")

	rows = [_device_dict(values) for values in BLOCK_A_DEVICES]
	result = {
		"title": "SOC BLOCK A DEVICE IMPORT",
		"dry_run": dry_run,
		"source_rows_examined": SOURCE_TOTAL,
		"block_a_rows_selected": SOURCE_BLOCK_A_TOTAL,
		"other_block_rows_ignored": SOURCE_OTHER_BLOCK_TOTAL,
		"campus": {"name": campus.name, "status": "Existing"},
		"location": {"name": BLOCK_A, "status": location_status},
		"equipment": {
			"would_create": 0,
			"created": 0,
			"already_existed": 0,
			"skipped": 0,
			"errors": 0,
		},
		"by_equipment_type": dict(Counter(_equipment_type(row) for row in rows)),
		"skipped_rows": [],
	}

	try:
		if not dry_run and not block:
			block = _create_block_a(campus.name)

		for row in rows:
			error = _validate_device(row)
			if error:
				result["equipment"]["skipped"] += 1
				result["equipment"]["errors"] += 1
				result["skipped_rows"].append(
					{"source_number": row["source_number"], "reason": error}
				)
				continue

			existing, matched_by = _find_existing_equipment(row, block.name if block else None)
			if existing:
				result["equipment"]["already_existed"] += 1
				result["equipment"]["skipped"] += 1
				result["skipped_rows"].append(
					{
						"source_number": row["source_number"],
						"reason": f"Already exists as {existing} (matched by {matched_by})",
					}
				)
				continue

			if dry_run:
				result["equipment"]["would_create"] += 1
			else:
				_create_equipment(row, block.name)
				result["equipment"]["created"] += 1

		if not dry_run:
			frappe.db.commit()
	except Exception:
		if not dry_run:
			frappe.db.rollback()
		raise

	return result


def _validate_structure():
	required_location_fields = {"location_name", "location_code", "location_type", "parent_location"}
	required_equipment_fields = {
		"equipment_name",
		"equipment_type",
		"serial_number",
		"location",
		"status",
		"is_active",
		"notes",
	}
	for doctype, required_fields in (
		("IT Location", required_location_fields),
		("IT Equipment", required_equipment_fields),
	):
		if not frappe.db.exists("DocType", doctype):
			frappe.throw(f"Required DocType {doctype} does not exist.")
		available = {field.fieldname for field in frappe.get_meta(doctype).fields}
		missing = required_fields - available
		if missing:
			frappe.throw(f"{doctype} is missing required fields: {', '.join(sorted(missing))}")


def _get_soc_campus():
	campuses = frappe.get_all(
		"IT Location",
		filters={"location_name": SOC_CAMPUS, "location_type": "Campus"},
		fields=["name", "campus"],
	)
	if len(campuses) != 1:
		frappe.throw(f"Expected exactly one {SOC_CAMPUS} IT Location; found {len(campuses)}.")
	return campuses[0]


def _get_block_a(campus):
	name = frappe.db.get_value(
		"IT Location",
		{"location_name": BLOCK_A, "location_type": "Block", "parent_location": campus},
		"name",
	)
	return frappe.get_doc("IT Location", name) if name else None


def _create_block_a(campus):
	return frappe.get_doc(
		{
			"doctype": "IT Location",
			"location_name": BLOCK_A,
			"location_code": BLOCK_A_CODE,
			"location_type": "Block",
			"parent_location": campus,
			"is_active": 1,
		}
	).insert(ignore_permissions=True)


def _device_dict(values):
	return dict(zip(DEVICE_FIELDS, values, strict=True))


def _equipment_type(row):
	if row["source_type"] == "IP Camera":
		return "CCTV Camera"
	if row["source_type"] == "Network Switch":
		return "Network Switch"
	if row["source_type"] == "Network Video Recorder" or row["model"].startswith("DS-77"):
		return "Network Video Recorder"
	return "Other"


def _validate_device(row):
	for field in ("model", "ip_address", "short_serial", "serial_number", "device_name", "mac_address"):
		if not row[field]:
			return f"Missing required source value: {field}"
	try:
		ipaddress.ip_address(row["ip_address"])
	except ValueError:
		return "Invalid IP address"
	if not MAC_PATTERN.fullmatch(row["mac_address"]):
		return "Invalid MAC address"
	if _equipment_type(row) == "Other":
		return f"Unsupported equipment type: {row['source_type']}"
	return None


def _find_existing_equipment(row, location):
	for serial_field, label in (("serial_number", "full serial"), ("short_serial", "short serial")):
		existing = frappe.db.get_value("IT Equipment", {"serial_number": row[serial_field]}, "name")
		if existing:
			return existing, label

	existing = frappe.db.get_value(
		"IT Equipment", {"notes": ("like", f"%MAC: {row['mac_address']}%")}, "name"
	)
	if existing:
		return existing, "MAC address"
	if location:
		existing = frappe.db.get_value(
			"IT Equipment",
			{"location": location, "notes": ("like", f"%IP: {row['ip_address']} |%")},
			"name",
		)
		if existing:
			return existing, "IP address and location"
	return None, None


def _create_equipment(row, location):
	return frappe.get_doc(
		{
			"doctype": "IT Equipment",
			"equipment_name": row["device_name"],
			"equipment_type": _equipment_type(row),
			"serial_number": row["serial_number"],
			"location": location,
			"status": "Operational",
			"is_active": 1,
			"notes": _equipment_notes(row),
		}
	).insert(ignore_permissions=True)


def _equipment_notes(row):
	return " | ".join(
		(
			"Source Device Group: BLOCK A",
			f"Source Row: {row['source_number']}",
			f"IP: {row['ip_address']}",
			f"Model: {row['model']}",
			f"Short Serial: {row['short_serial']}",
			f"Web Version: {row['web_version']}",
			f"MAC: {row['mac_address']}",
		)
	)


def _as_bool(value):
	if isinstance(value, str):
		return value.strip().lower() not in {"0", "false", "no", "off"}
	return bool(value)
