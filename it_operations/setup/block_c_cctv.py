import re

import frappe


BLOCK_LOCATION = "Block C"
TEMPLATE_NAME = "Block C IT Equipment Daily Inspection"
RESPONSIBILITY_TYPE = "Block IT Equipment Inspection"

NVRS = (
	{"ip_address": "10.143.150.3", "model": "DS-7732NI-K4/16P"},
	{"ip_address": "10.143.150.2", "model": "DS-7732NI-K4/16P"},
)

CAMERAS = (
	("10.143.150.6", "DS-2CD1043G0E-I", "F02743320", "24CR-1C-04 (1-009)", "24CR-1C-04 (1-009)"),
	("10.143.150.7", "DS-2CD1043G0E-I", "E64770366", "24CR-0C-03 (1-016)", "24CR-0C-03 (1-016)"),
	("10.143.150.9", "DS-2CD1043G0E-I", "E94567099", "24CR-1C-01 (1-017)", "24CR-1C-01 (1-017)"),
	("10.143.150.13", "DS-2CD1143G0-IUF", "J62513781", "B05F0-AR02 (1-002)", "11C1-B10F2CR02 (1-002)"),
	("10.143.150.12", "DS-2CD1043G0E-I", "E94567294", "24CR-1C-02 (1-014)", "24CR-1C-02 (1-014)"),
	("10.143.150.11", "DS-2CD1043G0E-I", "E94566757", "24CR-0C-02 (1-004)", "24CR-0C-02 (1-004)"),
	("10.143.150.10", "DS-2CD1043G0E-I", "E65986258", "24CR-0C-04 (1-001)", "24CR-0C-04 (1-001)"),
	("10.143.150.14", "DS-2CD1143G0-IUF", "J62513804", "B05F0-AR03 (1-013)", "11C2-B08F0CR03 (1-013)"),
	("10.143.150.31", "DS-2CD1143G0-IUF", "J62513760", "B05F1-AR05 (1-024)", "10C1-B08F1CR05 (1-024)"),
	("10.143.150.29", "DS-2CD1043G0E-I", "E65986241", "24CR-1C-03 (1-022)", "24CR-1C-03 (1-022)"),
	("10.143.150.27", "DS-2CD1143G0-IUF", "J62513809", "B05F1-AR06 (1-020)", "10C2-B08F1CR06 (1-020)"),
	("10.143.150.26", "DS-2CD1143G0-IUF", "J62513797", "B05F0-AR05 (1-019)", "11C4-B08F0CR05 (1-019)"),
	("10.143.150.25", "DS-2CD1143G0-IUF", "J62513756", "B05F1-AR07 (1-021)", "11S5-B08F1CR07 (1-021)"),
	("10.143.150.24", "DS-2CD1143G0-IUF", "J62513817", "B05F0-AR07 (1-012)", "11S2-B08F0CR07 (1-012)"),
	("10.143.150.23", "DS-2CD1143G0-IUF", "J62513755", "B05F1-AR08 (1-015)", "11S4-B08F1CR08 (1-015)"),
	("10.143.150.22", "DS-2CD1143G0-IUF", "J62513774", "B05F0-AR04 (1-008)", "11C3-B08F0CR04 (1-008)"),
	("10.143.150.21", "DS-2CD1143G0-IUF", "J62513748", "B05F01-AR02 (1-010)", "10S3-B08F1CR02 (1-010)"),
	("10.143.150.20", "DS-2CD1143G0-IUF", "J62513769", "B05F0-AR08 (1-023)", "11S3-B08F0CR08 (1-023)"),
	("10.143.150.19", "DS-2CD1143G0-I", "F88078203", "B05F1-AR04 (1-006)", "10S1-B08F1CR04 (1-006)"),
	("10.143.150.18", "DS-2CD1143G0-IUF", "J62513766", "B05F0-AR01 OFFICE (1-003)", "OFFICE-B08F0CR01 (1-003)"),
	("10.143.150.17", "DS-2CD2143G0-IU", "F29672448", "B05F1-AR01 (1-005)", "10S4-B08F1CR01 (1-005)"),
	("10.143.150.16", "DS-2CD1143G0-IUF", "J62513753", "B05F1-AR03 (1-007)", "10S2-B08F1CR03 (1-007)"),
	("10.143.150.15", "DS-2CD1143G0-IUF", "J62513754", "B05F0-AR06 (1-011)", "11S1-B08F0CR06 (1-011)"),
)


def seed():
	"""Create the initial Block C CCTV inventory and reusable daily checklist."""
	block = _ensure_location(BLOCK_LOCATION, "BLOCK-C", "Block")
	template = _get_or_create_template()
	template_changed = template.is_new()

	for nvr in NVRS:
		name = f"Block C NVR {nvr['ip_address']}"
		point, equipment = _ensure_device(
			device_name=name,
			device_type="Network Video Recorder",
			location=block,
			ip_address=nvr["ip_address"],
			model=nvr["model"],
		)
		template_changed |= _append_template_item(template, point, equipment, "Equipment")

	for ip_address, model, serial_number, device_name, channel_name in CAMERAS:
		location = _camera_location(block, channel_name)
		point, equipment = _ensure_device(
			device_name=device_name,
			device_type="CCTV Camera",
			location=location,
			ip_address=ip_address,
			model=model,
			serial_number=serial_number,
			channel_name=channel_name,
		)
		template_changed |= _append_template_item(template, point, equipment, "Camera")

	if template_changed:
		template.save(ignore_permissions=True)
	return template.name


def _ensure_location(location_name, location_code, location_type, parent_location=None):
	existing = frappe.db.get_value("IT Location", {"location_code": location_code}, "name")
	if existing:
		return existing
	return frappe.get_doc(
		{
			"doctype": "IT Location",
			"location_name": location_name,
			"location_code": location_code,
			"location_type": location_type,
			"parent_location": parent_location,
			"is_active": 1,
		}
	).insert(ignore_permissions=True).name


def _camera_location(block, channel_name):
	room_match = re.search(r"(B\d+F\d+CR\d+)", channel_name)
	if not room_match:
		return block
	room_code = room_match.group(1)
	floor_code = re.match(r"(B\d+F\d+)", room_code).group(1)
	floor = _ensure_location(f"Block C - {floor_code}", floor_code, "Floor", block)
	return _ensure_location(f"Block C - {room_code}", room_code, "Room", floor)


def _ensure_device(
	device_name,
	device_type,
	location,
	ip_address,
	model,
	serial_number=None,
	channel_name=None,
):
	equipment_filters = {"serial_number": serial_number} if serial_number else {"equipment_name": device_name}
	equipment = frappe.db.get_value("IT Equipment", equipment_filters, "name")
	if not equipment:
		equipment = frappe.get_doc(
			{
				"doctype": "IT Equipment",
				"equipment_name": device_name,
				"equipment_type": device_type,
				"serial_number": serial_number,
				"location": location,
				"status": "Operational",
				"is_active": 1,
				"notes": _device_notes(ip_address, model, channel_name),
			}
		).insert(ignore_permissions=True).name

	legacy_point_name = f"Block C - {device_name}"
	point_name = device_name if device_type == "Network Video Recorder" else legacy_point_name
	point = frappe.db.get_value("IT Monitoring Point", {"point_name": point_name}, "name")
	if not point and point_name != legacy_point_name and frappe.db.exists("IT Monitoring Point", legacy_point_name):
		point = frappe.rename_doc("IT Monitoring Point", legacy_point_name, point_name, force=True)
	if not point:
		point = frappe.get_doc(
			{
				"doctype": "IT Monitoring Point",
				"point_name": point_name,
				"location": location,
				"point_type": "Camera" if device_type == "CCTV Camera" else "Network Video Recorder",
				"is_active": 1,
				"camera_identifier": device_name,
				"camera_model": model,
				"ip_address": ip_address,
				"nvr_channel": channel_name,
				"equipment": equipment,
				"view_description": f"Block C CCTV view: {channel_name}" if channel_name else "Block C recorder",
			}
		).insert(ignore_permissions=True).name

	if not frappe.db.get_value("IT Equipment", equipment, "monitoring_point"):
		frappe.db.set_value("IT Equipment", equipment, "monitoring_point", point, update_modified=False)
	return point, equipment


def _device_notes(ip_address, model, channel_name):
	details = [f"IP: {ip_address}", f"Model: {model}"]
	if channel_name:
		details.append(f"Channel: {channel_name}")
	return " | ".join(details)


def _get_or_create_template():
	if frappe.db.exists("IT Checklist Template", TEMPLATE_NAME):
		return frappe.get_doc("IT Checklist Template", TEMPLATE_NAME)
	return frappe.get_doc(
		{
			"doctype": "IT Checklist Template",
			"template_name": TEMPLATE_NAME,
			"responsibility_type": RESPONSIBILITY_TYPE,
			"is_active": 1,
			"description": (
				"Daily Block C IT equipment inspection. It currently includes CCTV cameras and NVRs; "
				"add televisions and wireless access points as their inventories become available."
			),
		}
	)


def _append_template_item(template, point, equipment, check_type):
	if any(row.monitoring_point == point or row.equipment == equipment for row in template.items):
		return False
	device = frappe.db.get_value("IT Equipment", equipment, ["equipment_name", "equipment_type"], as_dict=True)
	is_nvr = device.equipment_type == "Network Video Recorder"
	instructions = (
		"Confirm the NVR is online and working, then verify recording and playback. Record storage or hard-drive "
		"failures in Remarks."
		if is_nvr
		else "Confirm the camera is online and working, aligned, recording, and passes playback. Add Remarks for any failure."
	)
	template.append(
		"items",
		{
			"check_title": device.equipment_name,
			"check_type": check_type,
			"monitoring_point": point,
			"equipment": equipment,
			"mandatory": 1,
			"instructions": instructions,
		},
	)
	return True
