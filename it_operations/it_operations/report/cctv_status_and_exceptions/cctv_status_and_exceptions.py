import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate

from it_operations.permissions import daily_log_query


def execute(filters=None):
	filters = frappe._dict(filters or {})
	conditions = [
		"parent.operation_date between %(from_date)s and %(to_date)s",
		"item.check_type = 'Camera'",
	]
	values = {
		"from_date": getdate(filters.from_date or add_days(nowdate(), -7)),
		"to_date": getdate(filters.to_date or nowdate()),
	}
	if filters.location:
		conditions.append("item.location = %(location)s")
		values["location"] = filters.location
	if filters.status:
		conditions.append("item.status = %(status)s")
		values["status"] = filters.status
	if filters.exceptions_only:
		conditions.append("item.status in ('Fault', 'Exception')")
	access = daily_log_query()
	if access:
		conditions.append(access.replace("`tabIT Daily Operations Log`", "parent"))
	data = frappe.db.sql(
		f"""
			select parent.name as log, parent.operation_date, parent.employee_name,
				item.location, item.monitoring_point, point.camera_identifier,
				point.ip_address, item.status, item.remarks, item.checked_at, item.checked_by
			from `tabIT Daily Check Item` item
			join `tabIT Daily Operations Log` parent on parent.name = item.parent
			left join `tabIT Monitoring Point` point on point.name = item.monitoring_point
			where {" and ".join(conditions)}
			order by parent.operation_date desc, item.location asc, item.idx asc
		""",
		values,
		as_dict=True,
	)
	return get_columns(), data


def get_columns():
	return [
		{"label": _("Log"), "fieldname": "log", "fieldtype": "Link", "options": "IT Daily Operations Log", "width": 145},
		{"label": _("Date"), "fieldname": "operation_date", "fieldtype": "Date", "width": 95},
		{"label": _("Employee"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{"label": _("Location"), "fieldname": "location", "fieldtype": "Link", "options": "IT Location", "width": 140},
		{"label": _("Monitoring Point"), "fieldname": "monitoring_point", "fieldtype": "Link", "options": "IT Monitoring Point", "width": 170},
		{"label": _("Camera ID"), "fieldname": "camera_identifier", "fieldtype": "Data", "width": 110},
		{"label": _("IP Address"), "fieldname": "ip_address", "fieldtype": "Data", "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 95},
		{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 220},
		{"label": _("Checked At"), "fieldname": "checked_at", "fieldtype": "Datetime", "width": 150},
		{"label": _("Checked By"), "fieldname": "checked_by", "fieldtype": "Link", "options": "User", "width": 160},
	]
