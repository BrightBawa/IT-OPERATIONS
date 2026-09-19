import frappe
from frappe import _
from frappe.utils import add_months, getdate, nowdate

from it_operations.permissions import daily_log_query


def execute(filters=None):
	filters = frappe._dict(filters or {})
	conditions = ["operation_date between %(from_date)s and %(to_date)s"]
	values = {
		"from_date": getdate(filters.from_date or add_months(nowdate(), -1)),
		"to_date": getdate(filters.to_date or nowdate()),
	}
	if filters.employee:
		conditions.append("employee = %(employee)s")
		values["employee"] = filters.employee
	access = daily_log_query()
	if access:
		conditions.append(access)
	data = frappe.db.sql(
		f"""
			select date_format(operation_date, '%%Y-%%m') as month, employee, employee_name,
				count(*) as expected_logs,
				sum(case when status = 'Submitted' then 1 else 0 end) as submitted_logs,
				round(avg(completion_rate), 2) as average_completion,
				sum(fault_count) as faults, sum(exception_count) as exceptions
			from `tabIT Daily Operations Log`
			where {" and ".join(conditions)}
			group by date_format(operation_date, '%%Y-%%m'), employee, employee_name
			order by month desc, employee_name asc
		""",
		values,
		as_dict=True,
	)
	return get_columns(), data


def get_columns():
	return [
		{"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 90},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 130,
		},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Generated Logs"), "fieldname": "expected_logs", "fieldtype": "Int", "width": 110},
		{"label": _("Submitted"), "fieldname": "submitted_logs", "fieldtype": "Int", "width": 90},
		{
			"label": _("Avg Completion %"),
			"fieldname": "average_completion",
			"fieldtype": "Percent",
			"width": 130,
		},
		{"label": _("Faults"), "fieldname": "faults", "fieldtype": "Int", "width": 80},
		{"label": _("Exceptions"), "fieldname": "exceptions", "fieldtype": "Int", "width": 90},
	]
