import frappe
from frappe.utils import cint

from it_operations.permissions import require_manager


def _card(value):
	return {"value": cint(value), "fieldtype": "Int", "route": ["dashboard-view", "IT Operations Manager Dashboard"]}


def _count(where, values=None):
	return frappe.db.sql(
		f"select count(*) from `tabIT Daily Operations Log` where {where}",
		values or {},
	)[0][0]


@frappe.whitelist()
def get_today_logs():
	require_manager()
	return _card(_count("operation_date = curdate() and docstatus < 2"))


@frappe.whitelist()
def get_today_submitted():
	require_manager()
	return _card(_count("operation_date = curdate() and docstatus = 1"))


@frappe.whitelist()
def get_today_faults():
	require_manager()
	value = frappe.db.sql(
		"""select count(*) from `tabIT Daily Check Item` item
		join `tabIT Daily Operations Log` parent on parent.name = item.parent
		where parent.operation_date = curdate() and parent.docstatus < 2 and item.status = 'Fault'"""
	)[0][0]
	return _card(value)


@frappe.whitelist()
def get_today_exceptions():
	require_manager()
	value = frappe.db.sql(
		"""select count(*) from `tabIT Daily Check Item` item
		join `tabIT Daily Operations Log` parent on parent.name = item.parent
		where parent.operation_date = curdate() and parent.docstatus < 2 and item.status = 'Exception'"""
	)[0][0]
	return _card(value)
