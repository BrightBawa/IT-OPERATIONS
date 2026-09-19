import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from it_operations.it_operations.doctype.it_daily_operations_log.it_daily_operations_log import (
	generate_logs_with_status,
)
from it_operations.permissions import can_access_employee, is_manager, is_supervisor
from it_operations.workday import no_submission_message


def _response(result):
	if result.non_working_day:
		message = no_submission_message(result.operation_date, result.non_working_day)
	elif result.logs and result.skipped:
		message = _(
			"{0} operations log(s) are ready. {1} employee(s) were skipped because no submission is required on their holiday."
		).format(len(result.logs), len(result.skipped))
	elif result.logs:
		message = _("{0} operations log(s) are ready.").format(len(result.logs))
	elif result.skipped:
		reasons = ", ".join(dict.fromkeys(row.reason for row in result.skipped))
		message = _("No operations logs were generated because {0}. No submission is required.").format(
			reasons
		)
	else:
		message = _("No active responsibility assignments were found.")
	return {
		"logs": result.logs,
		"skipped": result.skipped,
		"non_working_day": result.non_working_day,
		"message": message,
	}


def _merge_results(results, operation_date):
	merged = frappe._dict(operation_date=operation_date, logs=[], skipped=[], non_working_day=None)
	for result in results:
		merged.logs.extend(result.logs)
		merged.skipped.extend(result.skipped)
		merged.non_working_day = merged.non_working_day or result.non_working_day
	merged.logs = list(dict.fromkeys(merged.logs))
	return merged


@frappe.whitelist()
def regenerate_daily_log(employee=None, operation_date=None):
	"""Create a missing log or add missing assignment/template rows without duplicating work."""
	operation_date = getdate(operation_date or nowdate())
	if not employee:
		if is_manager():
			return _response(generate_logs_with_status(operation_date, regenerate=True))
		if is_supervisor():
			employees = frappe.get_all(
				"IT Responsibility Assignment",
				filters={"is_active": 1},
				or_filters={"employee_user": frappe.session.user, "supervisor_user": frappe.session.user},
				pluck="employee",
			)
			results = []
			for employee_name in dict.fromkeys(employees):
				results.append(
					generate_logs_with_status(operation_date, employee=employee_name, regenerate=True)
				)
			return _response(_merge_results(results, operation_date))
		employee = frappe.db.get_value(
			"Employee", {"user_id": frappe.session.user, "status": "Active"}, "name"
		)
	if not employee:
		frappe.throw(_("Your user account is not linked to an active Employee record."))
	if not can_access_employee(employee):
		frappe.throw(
			_("You are not permitted to generate this employee's operations log."), frappe.PermissionError
		)
	return _response(generate_logs_with_status(operation_date, employee=employee, regenerate=True))
