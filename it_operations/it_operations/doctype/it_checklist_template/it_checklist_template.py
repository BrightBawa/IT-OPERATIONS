import frappe
from frappe import _
from frappe.model.document import Document


class ITChecklistTemplate(Document):
	def validate(self):
		if not self.items:
			frappe.throw(_("Add at least one checklist item."))
		camera_rows = [row for row in self.items if row.check_type == "Camera"]
		for row in camera_rows:
			if not row.monitoring_point:
				frappe.throw(_("Row {0}: Camera checks require a Monitoring Point.").format(row.idx))
