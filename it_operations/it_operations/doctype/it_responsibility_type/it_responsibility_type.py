import frappe
from frappe.model.document import Document


class ITResponsibilityType(Document):
	def before_validate(self):
		self.responsibility_type_name = (self.responsibility_type_name or "").strip()
		self.description = (self.description or "").strip() or None
		self.applicable_equipment = (self.applicable_equipment or "").strip() or None


def on_doctype_update():
	frappe.db.add_index("IT Responsibility Type", ["inspection_frequency", "is_active"])
