from ipaddress import ip_address

import frappe
from frappe import _
from frappe.model.document import Document

EQUIPMENT_TYPE_BY_POINT_TYPE = {
	"Camera": "CCTV Camera",
	"Network Video Recorder": "Network Video Recorder",
	"Television": "Television",
	"Wireless Access Point": "Wireless Access Point",
	"Network Switch": "Network Switch",
	"Router": "Router",
	"Server": "Server",
}


class ITMonitoringPoint(Document):
	def before_validate(self):
		for fieldname in (
			"point_name",
			"camera_identifier",
			"camera_make",
			"camera_model",
			"ip_address",
			"nvr_name",
			"nvr_channel",
			"view_description",
			"notes",
		):
			self.set(fieldname, (self.get(fieldname) or "").strip() or None)

	def validate(self):
		self._validate_camera_fields()
		self._validate_ip_address()
		self._validate_equipment()

	def _validate_camera_fields(self):
		if self.point_type != "Camera":
			self.nvr_name = None
			self.nvr_channel = None
			return
		if not self.camera_identifier:
			frappe.throw(_("Camera Identifier is required for camera monitoring points."))

	def _validate_ip_address(self):
		if not self.ip_address:
			return
		try:
			self.ip_address = str(ip_address(self.ip_address))
		except ValueError:
			frappe.throw(_("Enter a valid IPv4 or IPv6 address."))

	def _validate_equipment(self):
		if not self.equipment:
			return

		equipment = frappe.db.get_value(
			"IT Equipment",
			self.equipment,
			["equipment_type", "location", "monitoring_point"],
			as_dict=True,
		)
		if not equipment:
			frappe.throw(_("Equipment {0} does not exist.").format(frappe.bold(self.equipment)))
		if equipment.location != self.location:
			frappe.throw(_("The Monitoring Point and Equipment must use the same Asset Location."))

		expected_type = EQUIPMENT_TYPE_BY_POINT_TYPE.get(self.point_type)
		if expected_type and equipment.equipment_type != expected_type:
			frappe.throw(
				_("A {0} Monitoring Point requires {1} Equipment.").format(
					frappe.bold(self.point_type), frappe.bold(expected_type)
				)
			)
		if equipment.monitoring_point and equipment.monitoring_point != self.name:
			frappe.throw(_("The selected Equipment is already linked to another Monitoring Point."))


def on_doctype_update():
	frappe.db.add_index("IT Monitoring Point", ["location", "is_active"])
	frappe.db.add_index("IT Monitoring Point", ["point_type", "is_active"])
	frappe.db.add_index("IT Monitoring Point", ["equipment"])
