import frappe
from frappe import _
from frappe.utils.dashboard import cache_source

from it_operations.permissions import require_manager


@frappe.whitelist()
@cache_source
def get(**kwargs):
	require_manager()
	rows = frappe.db.sql(
		"""select status, count(*) as value from `tabIT Daily Operations Log`
		where operation_date = curdate() and docstatus < 2 group by status order by status""",
		as_dict=True,
	)
	return {
		"labels": [row.status for row in rows] or [_('No Data')],
		"datasets": [{"name": _("Logs"), "values": [row.value for row in rows] or [0]}],
	}
