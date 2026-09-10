import frappe
from frappe.utils import getdate, nowdate

from it_operations.it_operations.doctype.it_daily_operations_log.it_daily_operations_log import generate_logs


def generate_daily_operations_logs(operation_date=None):
	"""Scheduler entry point. Safe to call repeatedly for the same date."""
	if not frappe.db.exists("DocType", "IT Operations Settings"):
		return []
	if not frappe.db.get_single_value("IT Operations Settings", "enable_daily_generation"):
		return []
	return generate_logs(getdate(operation_date or nowdate()))
