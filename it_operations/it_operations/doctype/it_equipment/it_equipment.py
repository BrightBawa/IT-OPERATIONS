import frappe
from frappe import _
from frappe.model.document import Document

from it_operations.it_operations.doctype.it_monitoring_point.it_monitoring_point import (
	EQUIPMENT_TYPES_BY_POINT_TYPE,
	POINT_TYPE_BY_EQUIPMENT_TYPE,
)

DEPLOYMENT_STATUSES = {"In Storage", "Reserved", "Deployed", "Under Maintenance", "Retired"}
MONITORED_CONDITIONS = {"Operational", "Degraded"}


class ITEquipment(Document):
	def before_validate(self):
		self.equipment_name = (self.equipment_name or "").strip()
		self.serial_number = (self.serial_number or "").strip() or None
		self.notes = (self.notes or "").strip() or None
		self.deployment_status = self.get("deployment_status") or "Deployed"

	def validate(self):
		self._validate_location()
		self._validate_deployment_status()
		self._validate_asset()
		self._validate_monitoring_point()

	def after_insert(self):
		self._ensure_monitoring_point()

	def on_update(self):
		self._ensure_monitoring_point()

	def _validate_location(self):
		if not self.location:
			frappe.throw(_("Asset Location is required for every IT Equipment record."))
		if not frappe.db.exists("Location", self.location):
			frappe.throw(_("Asset Location {0} does not exist.").format(frappe.bold(self.location)))

	def _validate_deployment_status(self):
		if self.deployment_status not in DEPLOYMENT_STATUSES:
			frappe.throw(_("Invalid Deployment Status: {0}.").format(frappe.bold(self.deployment_status)))

		if self.deployment_status == "Retired" or self.status == "Retired":
			self.deployment_status = "Retired"
			self.status = "Retired"
			self.is_active = 0

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
		allowed_types = EQUIPMENT_TYPES_BY_POINT_TYPE.get(point.point_type)
		if allowed_types and self.equipment_type not in allowed_types:
			frappe.throw(
				_("Monitoring Point {0} is not compatible with Equipment Type {1}.").format(
					frappe.bold(self.monitoring_point), frappe.bold(self.equipment_type)
				)
			)
		if point.equipment and point.equipment != self.name:
			frappe.throw(_("The selected Monitoring Point is already linked to different Equipment."))

	def _ensure_monitoring_point(self):
		if not self.monitoring_point:
			point = frappe.get_doc(
				{
					"doctype": "IT Monitoring Point",
					"point_name": self._monitoring_point_name(),
					"location": self.location,
					"point_type": POINT_TYPE_BY_EQUIPMENT_TYPE[self.equipment_type],
					"camera_identifier": self.equipment_name
					if self.equipment_type == "CCTV Camera"
					else None,
					"equipment": self.name,
					"is_active": self._monitoring_point_is_active(),
				}
			).insert(ignore_permissions=True)
			self.db_set("monitoring_point", point.name, update_modified=False)
			self.monitoring_point = point.name

		self._sync_monitoring_point()

	def _monitoring_point_name(self):
		if not frappe.db.exists("IT Monitoring Point", self.equipment_name):
			return self.equipment_name
		return f"{self.equipment_name} ({self.name})"

	def _sync_monitoring_point(self):
		point = frappe.get_doc("IT Monitoring Point", self.monitoring_point)
		values = {
			"location": self.location,
			"point_type": POINT_TYPE_BY_EQUIPMENT_TYPE[self.equipment_type],
			"equipment": self.name,
			"is_active": self._monitoring_point_is_active(),
		}
		if self.equipment_type == "CCTV Camera" and not point.camera_identifier:
			values["camera_identifier"] = self.equipment_name

		if any(point.get(fieldname) != value for fieldname, value in values.items()):
			point.update(values)
			point.save(ignore_permissions=True)

	def _monitoring_point_is_active(self):
		return int(
			bool(self.is_active)
			and self.deployment_status == "Deployed"
			and self.status in MONITORED_CONDITIONS
		)


def on_doctype_update():
	frappe.db.add_index("IT Equipment", ["location", "is_active"])
	frappe.db.add_index("IT Equipment", ["deployment_status", "status", "is_active"])
	frappe.db.add_index("IT Equipment", ["equipment_type", "deployment_status"])
	frappe.db.add_index("IT Equipment", ["monitoring_point"])
