import frappe
from frappe import _
from frappe.model.document import Document

from it_operations.it_operations.doctype.it_monitoring_point.it_monitoring_point import (
	EQUIPMENT_TYPE_BY_POINT_TYPE,
)


class ITEquipment(Document):
	def before_validate(self):
		self.equipment_name = (self.equipment_name or "").strip()
		self.serial_number = (self.serial_number or "").strip() or None
		self.notes = (self.notes or "").strip() or None

	def validate(self):
		self._validate_asset()
		self._validate_monitoring_point()

	def _validate_asset(self):
		if not self.asset:
			return
		existing = frappe.db.get_value("IT Equipment", {"asset": self.asset}, "name")
		if existing and existing != self.name:
			frappe.throw(
				_("ERPNext Asset {0} is already linked to Equipment {1}.").format(
					frappe.bold(self.asset), frappe.bold(existing)
				)
			)

	def _validate_monitoring_point(self):
		if not self.monitoring_point:
			return

		point = frappe.db.get_value(
			"IT Monitoring Point",
			self.monitoring_point,
			["point_type", "location", "equipment"],
			as_dict=True,
		)
		if not point:
			frappe.throw(_("Monitoring Point {0} does not exist.").format(frappe.bold(self.monitoring_point)))
		if point.location != self.location:
			frappe.throw(_("The Equipment and Monitoring Point must use the same Asset Location."))

		expected_type = EQUIPMENT_TYPE_BY_POINT_TYPE.get(point.point_type)
		if expected_type and expected_type != self.equipment_type:
			frappe.throw(
				_("Monitoring Point {0} requires Equipment Type {1}.").format(
					frappe.bold(self.monitoring_point), frappe.bold(expected_type)
				)
			)
		if point.equipment and point.equipment != self.name:
			frappe.throw(_("The selected Monitoring Point is already linked to different Equipment."))


def on_doctype_update():
	frappe.db.add_index("IT Equipment", ["location", "is_active"])
	frappe.db.add_index("IT Equipment", ["equipment_type", "status"])
	frappe.db.add_index("IT Equipment", ["monitoring_point"])
