import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	from_date = getdate(filters.from_date or add_days(nowdate(), -7))
	to_date = getdate(filters.to_date or nowdate())
	doc_filters = {"operation_date": ["between", [from_date, to_date]]}
	if filters.employee:
		doc_filters["employee"] = filters.employee
	if filters.status:
		doc_filters["status"] = filters.status
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
		order_by="operation_date desc, employee_name asc",
	)
	return get_columns(), data


def get_columns():
	return [
		{"label": _("Log"), "fieldname": "name", "fieldtype": "Link", "options": "IT Daily Operations Log", "width": 150},
		{"label": _("Date"), "fieldname": "operation_date", "fieldtype": "Date", "width": 100},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Completion %"), "fieldname": "completion_rate", "fieldtype": "Percent", "width": 110},
		{"label": _("Faults"), "fieldname": "fault_count", "fieldtype": "Int", "width": 80},
		{"label": _("Exceptions"), "fieldname": "exception_count", "fieldtype": "Int", "width": 90},
		{"label": _("Submitted At"), "fieldname": "submitted_at", "fieldtype": "Datetime", "width": 150},
	]
