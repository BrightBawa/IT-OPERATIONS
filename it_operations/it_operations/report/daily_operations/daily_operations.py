import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate

from it_operations.permissions import can_access_employee
from it_operations.workday import get_non_working_day

NO_SUBMISSION_REQUIRED = "No Submission Required"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	from_date = getdate(filters.from_date or add_days(nowdate(), -7))
	to_date = getdate(filters.to_date or nowdate())
	doc_filters = {"operation_date": ["between", [from_date, to_date]]}
	if filters.employee:
		doc_filters["employee"] = filters.employee
	if filters.employee and not can_access_employee(filters.employee):
		frappe.throw(
			_("You are not permitted to view this employee's operations calendar."), frappe.PermissionError
		)
	if filters.status and filters.status != NO_SUBMISSION_REQUIRED:
		doc_filters["status"] = filters.status
	data = []
	if filters.status != NO_SUBMISSION_REQUIRED:
		data = frappe.get_list(
			"IT Daily Operations Log",
			filters=doc_filters,
			fields=[
				"name",
				"operation_date",
				"employee",
				"employee_name",
				"status",
				"completion_rate",
				"fault_count",
				"exception_count",
				"submitted_at",
			],
		)
	if not filters.status or filters.status == NO_SUBMISSION_REQUIRED:
		data.extend(_non_working_day_rows(from_date, to_date, filters.employee, data))
	data.sort(key=lambda row: (getdate(row.operation_date), row.get("employee_name") or ""), reverse=True)
	return get_columns(), data


def _non_working_day_rows(from_date, to_date, employee, existing_rows):
	employee_name = frappe.db.get_value("Employee", employee, "employee_name") if employee else None
	existing_dates = {getdate(row.operation_date) for row in existing_rows}
	rows = []
	operation_date = from_date
	while operation_date <= to_date:
		non_working_day = get_non_working_day(operation_date, employee)
		if non_working_day and operation_date not in existing_dates:
			rows.append(
				frappe._dict(
					operation_date=operation_date,
					employee=employee,
					employee_name=employee_name,
					status=NO_SUBMISSION_REQUIRED,
					submission_note=_("{0}; no submission is required.").format(non_working_day.reason),
				)
			)
		operation_date = add_days(operation_date, 1)
	return rows


def get_columns():
	return [
		{
			"label": _("Log"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "IT Daily Operations Log",
			"width": 150,
		},
		{"label": _("Date"), "fieldname": "operation_date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 130,
		},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 170},
		{"label": _("Submission Note"), "fieldname": "submission_note", "fieldtype": "Data", "width": 260},
		{"label": _("Completion %"), "fieldname": "completion_rate", "fieldtype": "Percent", "width": 110},
		{"label": _("Faults"), "fieldname": "fault_count", "fieldtype": "Int", "width": 80},
		{"label": _("Exceptions"), "fieldname": "exception_count", "fieldtype": "Int", "width": 90},
		{"label": _("Submitted At"), "fieldname": "submitted_at", "fieldtype": "Datetime", "width": 150},
	]
