from collections import defaultdict

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, now_datetime, nowdate

from it_operations.permissions import can_access_employee, employee_user

ADDRESSED_STATUSES = {"OK", "Fault", "Exception", "Not Applicable"}
ISSUE_STATUSES = {"Fault", "Exception"}
PASSING_DEVICE_VALUES = {
	"online_status": "Online",
	"working_status": "Working",
	"alignment_status": "Aligned",
	"recording_status": "Recording",
	"playback_status": "Working",
}
DEVICE_REQUIREMENTS = {
	"CCTV Camera": tuple(PASSING_DEVICE_VALUES),
	"Network Video Recorder": ("online_status", "working_status", "recording_status", "playback_status"),
	"Television": ("working_status", "alignment_status", "playback_status"),
	"Wireless Access Point": ("online_status", "working_status"),
	"Network Switch": ("online_status", "working_status"),
	"Router": ("online_status", "working_status"),
	"Server": ("online_status", "working_status"),
	"Computer": ("online_status", "working_status"),
	"Printer": ("online_status", "working_status"),
	"Other": ("working_status",),
}


class ITDailyOperationsLog(Document):
	def before_validate(self):
		self._set_identity_fields()
		self._set_device_results()
		self._stamp_check_items()
		self._stamp_activity_entries()
		self._set_summary()

	def validate(self):
		self._validate_identity_is_unchanged()
		self._validate_checklist_integrity()
		self._validate_activity_entries()
		self._validate_issue_remarks()

	def before_submit(self):
		unaddressed = [
			row.idx for row in self.check_items if row.mandatory and row.status not in ADDRESSED_STATUSES
		]
		if unaddressed:
			frappe.throw(
				_("Address all mandatory checklist items before submission. Pending rows: {0}").format(
					", ".join(str(idx) for idx in unaddressed)
				)
			)
		self.status = "Submitted"
		self.submitted_at = now_datetime()
		self.submitted_by = frappe.session.user

	def on_cancel(self):
		self.db_set("status", "Cancelled", update_modified=False)

	def _set_identity_fields(self):
		if not self.operation_date:
			self.operation_date = nowdate()
		if not self.employee:
			self.employee = frappe.db.get_value(
				"Employee", {"user_id": frappe.session.user, "status": "Active"}, "name"
			)
		if not self.employee:
			frappe.throw(_("Employee is required."))

		details = frappe.db.get_value(
			"Employee", self.employee, ["employee_name", "user_id", "reports_to"], as_dict=True
		)
		if not details:
			frappe.throw(_("Employee {0} does not exist.").format(frappe.bold(self.employee)))

		self.employee_name = details.employee_name
		self.assigned_user = details.user_id
		if not self.supervisor:
			self.supervisor = details.reports_to
		self.supervisor_user = employee_user(self.supervisor)
		self.log_key = f"{getdate(self.operation_date).isoformat()}::{self.employee}"

	def _validate_identity_is_unchanged(self):
		if self.is_new():
			if not self.flags.from_generation:
				frappe.throw(_("Create daily logs with Generate / Regenerate Today."))
			if not self.assigned_user:
				frappe.throw(_("The Employee must be linked to a system User."))
			if not can_access_employee(self.employee, supervisor_user=self.supervisor_user):
				frappe.throw(_("You cannot create a daily log for this employee."), frappe.PermissionError)
			return
		old = self.get_doc_before_save()
		if old and (
			old.employee != self.employee
			or getdate(old.operation_date) != getdate(self.operation_date)
			or old.supervisor != self.supervisor
		):
			frappe.throw(_("Employee, Operation Date, and Supervisor cannot be changed after creation."))

	def _validate_checklist_integrity(self):
		source_keys = [row.source_key for row in self.check_items if row.source_key]
		if len(source_keys) != len(set(source_keys)):
			frappe.throw(_("Generated checklist rows must have unique source keys."))

		if self.is_new():
			return
		old = self.get_doc_before_save()
		if not old:
			return
		old_rows = {row.source_key: row for row in old.check_items if row.source_key}
		current_rows = {row.source_key: row for row in self.check_items if row.source_key}
		missing = [row.idx for key, row in old_rows.items() if key not in current_rows]
		if missing:
			frappe.throw(
				_("Generated checklist rows cannot be removed. Missing original rows: {0}").format(
					", ".join(str(idx) for idx in missing)
				)
			)

		definition_fields = (
			"check_title",
			"check_type",
			"device_kind",
			"location",
			"monitoring_point",
			"equipment",
			"device_name",
			"channel_name",
			"ip_address",
			"model",
			"serial_number",
			"mandatory",
			"instructions",
			"responsibility_assignment",
			"checklist_template",
			"source_key",
		)
		for key, row in current_rows.items():
			previous = old_rows.get(key)
			if not previous:
				if not self.flags.from_generation:
					frappe.throw(_("Checklist rows can only be added by regeneration."))
				continue
			if any(row.get(field) != previous.get(field) for field in definition_fields):
				frappe.throw(_("Row {0}: generated checklist details cannot be changed.").format(row.idx))

		if not self.flags.from_generation and len(current_rows) != len(self.check_items):
			frappe.throw(_("Checklist rows can only be added by regeneration."))

	def _validate_activity_entries(self):
		for row in self.activity_entries:
			row.summary = (row.summary or "").strip()
			row.details = (row.details or "").strip() or None
			if row.duration_minutes is not None and row.duration_minutes < 0:
				frappe.throw(_("Row {0}: Duration cannot be negative.").format(row.idx))

			if not row.equipment:
				continue
			equipment_location = frappe.db.get_value("IT Equipment", row.equipment, "location")
			if not equipment_location:
				frappe.throw(
					_("Activity row {0}: Equipment {1} does not exist.").format(row.idx, row.equipment)
				)
			if row.location and row.location != equipment_location:
				frappe.throw(
					_("Activity row {0}: Equipment and Asset Location do not match.").format(row.idx)
				)
			if not row.location:
				row.location = equipment_location

	def _stamp_check_items(self):
		old_rows = {}
		old = None if self.is_new() else self.get_doc_before_save()
		if old:
			old_rows = {row.name: row for row in old.check_items}
		for row in self.check_items:
			previous = old_rows.get(row.name)
			if row.status == "Pending":
				row.checked_at = None
				row.checked_by = None
			elif not previous or previous.status != row.status:
				row.checked_at = now_datetime()
				row.checked_by = frappe.session.user
			else:
				row.checked_at = previous.checked_at
				row.checked_by = previous.checked_by

	def _set_device_results(self):
		for row in self.check_items:
			required_fields = DEVICE_REQUIREMENTS.get(row.device_kind)
			if not required_fields:
				continue
			for field in PASSING_DEVICE_VALUES:
				if field not in required_fields:
					row.set(field, "Not Applicable")
			if any((row.get(field) or "Not Checked") == "Not Checked" for field in required_fields):
				row.status = "Pending"
			elif all(row.get(field) == PASSING_DEVICE_VALUES[field] for field in required_fields):
				row.status = "OK"
			else:
				row.status = "Fault"

	def _stamp_activity_entries(self):
		old_rows = {}
		old = None if self.is_new() else self.get_doc_before_save()
		if old:
			old_rows = {row.name: row for row in old.activity_entries}
		for row in self.activity_entries:
			previous = old_rows.get(row.name)
			if previous:
				row.logged_at = previous.logged_at
				row.logged_by = previous.logged_by
			else:
				row.logged_at = now_datetime()
				row.logged_by = frappe.session.user

	def _validate_issue_remarks(self):
		missing = [
			row.idx
			for row in self.check_items
			if row.status in ISSUE_STATUSES and not (row.remarks or "").strip()
		]
		if missing:
			frappe.throw(
				_("Remarks are required for faults and exceptions. Rows: {0}").format(
					", ".join(str(idx) for idx in missing)
				)
			)

	def _set_summary(self):
		self.total_checks = len(self.check_items)
		self.completed_checks = sum(row.status in ADDRESSED_STATUSES for row in self.check_items)
		self.fault_count = sum(row.status == "Fault" for row in self.check_items)
		self.exception_count = sum(row.status == "Exception" for row in self.check_items)
		self.completion_rate = (
			flt(self.completed_checks * 100 / self.total_checks, 2) if self.total_checks else 0
		)

	@frappe.whitelist()
	def regenerate_from_assignments(self):
		if self.docstatus != 0:
			frappe.throw(_("Only draft logs can be regenerated."))
		if not frappe.has_permission(self.doctype, "write", doc=self):
			frappe.throw(_("You do not have permission to update this log."), frappe.PermissionError)
		generate_logs(self.operation_date, employee=self.employee, regenerate=True)
		return self.name


def _active_assignments(operation_date, employee=None):
	filters = {"is_active": 1, "start_date": ("<=", operation_date)}
	if employee:
		filters["employee"] = employee
	assignments = frappe.get_all(
		"IT Responsibility Assignment",
		filters=filters,
		fields=["name", "employee", "supervisor", "location", "checklist_template", "end_date"],
		order_by="employee asc, creation asc",
	)
	return [row for row in assignments if not row.end_date or getdate(row.end_date) >= operation_date]


def _employee_is_active(employee):
	details = frappe.db.get_value("Employee", employee, ["status", "user_id"], as_dict=True)
	return bool(
		details
		and details.status == "Active"
		and details.user_id
		and frappe.db.get_value("User", details.user_id, "enabled")
	)


def _rows_for_assignment(assignment):
	if not frappe.db.get_value("IT Checklist Template", assignment.checklist_template, "is_active"):
		return []
	template = frappe.get_doc("IT Checklist Template", assignment.checklist_template)
	rows = []
	for item in template.items:
		point = (
			frappe.db.get_value(
				"IT Monitoring Point",
				item.monitoring_point,
				["location", "camera_identifier", "camera_model", "ip_address", "nvr_channel"],
				as_dict=True,
			)
			if item.monitoring_point
			else None
		)
		equipment = (
			frappe.db.get_value(
				"IT Equipment",
				item.equipment,
				["equipment_name", "equipment_type", "serial_number"],
				as_dict=True,
			)
			if item.equipment
			else None
		)
		device_kind = equipment.equipment_type if equipment else None
		row = {
			"check_title": item.check_title,
			"check_type": item.check_type,
			"device_kind": device_kind,
			"location": point.location if point and point.location else assignment.location,
			"monitoring_point": item.monitoring_point,
			"equipment": item.equipment,
			"device_name": equipment.equipment_name
			if equipment
			else (point.camera_identifier if point else None),
			"channel_name": point.nvr_channel if point else None,
			"ip_address": point.ip_address if point else None,
			"model": point.camera_model if point else None,
			"serial_number": equipment.serial_number if equipment else None,
			"mandatory": item.mandatory,
			"status": "Pending",
			"instructions": item.instructions,
			"responsibility_assignment": assignment.name,
			"checklist_template": assignment.checklist_template,
			"source_key": f"{assignment.name}::{item.name}",
		}
		if device_kind in DEVICE_REQUIREMENTS:
			required_fields = DEVICE_REQUIREMENTS[device_kind]
			row.update(
				{
					field: "Not Checked" if field in required_fields else "Not Applicable"
					for field in PASSING_DEVICE_VALUES
				}
			)
		rows.append(row)
	return rows


def generate_logs(operation_date=None, employee=None, regenerate=False):
	"""Generate or refresh one draft log per active staff member, without duplicate rows."""
	operation_date = getdate(operation_date or nowdate())
	grouped = defaultdict(list)
	for assignment in _active_assignments(operation_date, employee):
		if _employee_is_active(assignment.employee):
			grouped[assignment.employee].append(assignment)

	result = []
	for employee_name, assignments in grouped.items():
		new_rows = [row for assignment in assignments for row in _rows_for_assignment(assignment)]
		if not new_rows:
			continue
		log_key = f"{operation_date.isoformat()}::{employee_name}"
		name = frappe.db.get_value("IT Daily Operations Log", {"log_key": log_key}, "name")
		if name:
			doc = frappe.get_doc("IT Daily Operations Log", name)
			if doc.docstatus == 0:
				existing = {row.source_key for row in doc.check_items}
				for row in new_rows:
					if row["source_key"] not in existing:
						doc.append("check_items", row)
						existing.add(row["source_key"])
				doc.flags.from_generation = True
				doc.save(ignore_permissions=True)
			result.append(name)
			continue

		doc = frappe.get_doc(
			{
				"doctype": "IT Daily Operations Log",
				"operation_date": operation_date,
				"employee": employee_name,
				"supervisor": assignments[0].supervisor,
				"status": "Draft",
				"check_items": new_rows,
			}
		)
		doc.flags.from_generation = True
		try:
			doc.insert(ignore_permissions=True)
		except frappe.DuplicateEntryError:
			doc = frappe.get_doc(
				"IT Daily Operations Log",
				frappe.db.get_value("IT Daily Operations Log", {"log_key": log_key}, "name"),
			)
		result.append(doc.name)
	return result


def on_doctype_update():
	frappe.db.add_index("IT Daily Operations Log", ["operation_date", "docstatus"])
	frappe.db.add_index("IT Daily Operations Log", ["assigned_user", "operation_date"])
	frappe.db.add_index("IT Daily Operations Log", ["supervisor_user", "operation_date"])
	frappe.db.add_index("IT Daily Operations Log", ["employee", "operation_date"])
