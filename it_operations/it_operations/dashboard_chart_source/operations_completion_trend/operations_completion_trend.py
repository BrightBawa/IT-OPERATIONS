import frappe
from frappe import _
from frappe.utils.dashboard import cache_source

from it_operations.permissions import require_manager


@frappe.whitelist()
@cache_source
def get(**kwargs):
	require_manager()
	rows = frappe.db.sql(
		"""select operation_date, round(avg(completion_rate), 2) as value
		from `tabIT Daily Operations Log` where operation_date >= date_sub(curdate(), interval 30 day)
		and docstatus < 2 group by operation_date order by operation_date""",
		as_dict=True,
	)
	return {
		"labels": [str(row.operation_date) for row in rows] or [_('No Data')],
		"datasets": [{"name": _("Completion %"), "values": [row.value for row in rows] or [0]}],
	}
