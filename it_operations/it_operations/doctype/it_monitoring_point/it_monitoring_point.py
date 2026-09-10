import frappe
from frappe import _
from frappe.model.document import Document


class ITMonitoringPoint(Document):
	def validate(self):
		if self.point_type == "Camera" and not self.camera_identifier:
			frappe.throw(_("Camera Identifier is required for camera monitoring points."))
