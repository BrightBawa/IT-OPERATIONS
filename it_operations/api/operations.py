import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from it_operations.it_operations.doctype.it_daily_operations_log.it_daily_operations_log import generate_logs
from it_operations.permissions import can_access_employee, is_manager, is_supervisor


@frappe.whitelist()
def regenerate_daily_log(employee=None, operation_date=None):
	"""Create a missing log or add missing assignment/template rows without duplicating work."""
	operation_date = getdate(operation_date or nowdate())
	if not employee:
		if is_manager():
			return generate_logs(operation_date, regenerate=True)
		if is_supervisor():
			employees = frappe.get_all(
				"IT Responsibility Assignment",
				filters={"is_active": 1},
				or_filters={"employee_user": frappe.session.user, "supervisor_user": frappe.session.user},
				pluck="employee",
			)
			logs = []
			for employee_name in dict.fromkeys(employees):
				logs.extend(generate_logs(operation_date, employee=employee_name, regenerate=True))
			return list(dict.fromkeys(logs))
		employee = frappe.db.get_value(
			"Employee", {"user_id": frappe.session.user, "status": "Active"}, "name"
		)
	if not employee:
		frappe.throw(_("Your user account is not linked to an active Employee record."))
	if not can_access_employee(employee):
		frappe.throw(_("You are not permitted to generate this employee's operations log."), frappe.PermissionError)
	return generate_logs(operation_date, employee=employee, regenerate=True)
