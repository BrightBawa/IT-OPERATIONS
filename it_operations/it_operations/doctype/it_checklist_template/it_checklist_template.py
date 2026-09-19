import frappe
from frappe import _
from frappe.model.document import Document


class ITChecklistTemplate(Document):
	def before_validate(self):
		self.template_name = (self.template_name or "").strip()
		self.description = (self.description or "").strip() or None
		for row in self.items:
			row.check_title = (row.check_title or "").strip()
			row.instructions = (row.instructions or "").strip() or None

	def validate(self):
		self._validate_responsibility_type()
		self._validate_items()

	def _validate_responsibility_type(self):
		is_active = frappe.db.get_value("IT Responsibility Type", self.responsibility_type, "is_active")
		if is_active is None:
			frappe.throw(
				_("Responsibility Type {0} does not exist.").format(frappe.bold(self.responsibility_type))
			)
		if self.is_active and not is_active:
			frappe.throw(_("An active checklist template requires an active Responsibility Type."))

	def _validate_items(self):
		if not self.items:
			frappe.throw(_("Add at least one checklist item."))

		seen = set()
		for row in self.items:
			if row.check_type == "Camera" and not row.monitoring_point:
				frappe.throw(_("Row {0}: Camera checks require a Monitoring Point.").format(row.idx))

			self._validate_item_links(row)
			key = (
				(row.check_title or "").casefold(),
				row.monitoring_point or "",
				row.equipment or "",
			)
			if key in seen:
				frappe.throw(_("Row {0}: This checklist item is duplicated.").format(row.idx))
			seen.add(key)

	def _validate_item_links(self, row):
		point = None
		if row.monitoring_point:
			point = frappe.db.get_value(
				"IT Monitoring Point",
				row.monitoring_point,
				["point_type", "equipment", "is_active"],
				as_dict=True,
			)
			if not point:
				frappe.throw(
					_("Row {0}: Monitoring Point {1} does not exist.").format(row.idx, row.monitoring_point)
				)
			if row.check_type == "Camera" and point.point_type != "Camera":
				frappe.throw(_("Row {0}: Camera checks require a camera Monitoring Point.").format(row.idx))

		if row.equipment:
			equipment_is_active = frappe.db.get_value("IT Equipment", row.equipment, "is_active")
			if equipment_is_active is None:
				frappe.throw(_("Row {0}: Equipment {1} does not exist.").format(row.idx, row.equipment))

		if point and point.equipment and row.equipment and point.equipment != row.equipment:
			frappe.throw(_("Row {0}: The Monitoring Point is linked to different Equipment.").format(row.idx))


def on_doctype_update():
	frappe.db.add_index("IT Checklist Template", ["responsibility_type", "is_active"])
