import frappe
from frappe.tests import IntegrationTestCase

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = ["Asset", "Location", "IT Monitoring Point"]


class IntegrationTestITEquipment(IntegrationTestCase):
	def test_location_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "IT Equipment",
				"equipment_name": f"No Location {frappe.generate_hash(length=8)}",
				"equipment_type": "Computer",
				"status": "Operational",
				"is_active": 1,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_creates_monitoring_point_and_inherits_location(self):
		suffix = frappe.generate_hash(length=8)
		first_location = self._insert_location(f"Equipment Room A {suffix}")
		second_location = self._insert_location(f"Equipment Room B {suffix}")
		equipment = frappe.get_doc(
			{
				"doctype": "IT Equipment",
				"equipment_name": f"Test Computer {suffix}",
				"equipment_type": "Computer",
				"location": first_location.name,
				"status": "Operational",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)

		self.assertTrue(equipment.monitoring_point)
		point = frappe.get_doc("IT Monitoring Point", equipment.monitoring_point)
		self.assertEqual(point.equipment, equipment.name)
		self.assertEqual(point.location, first_location.name)
		self.assertEqual(point.point_type, "Network Endpoint")
		self.assertEqual(point.is_active, 1)

		equipment.deployment_status = "In Storage"
		equipment.save(ignore_permissions=True)
		point.reload()
		self.assertEqual(point.is_active, 0)

		equipment.deployment_status = "Deployed"
		equipment.location = second_location.name
		equipment.save(ignore_permissions=True)
		point.reload()
		self.assertEqual(point.location, second_location.name)
		self.assertEqual(point.is_active, 1)

	@staticmethod
	def _insert_location(location_name):
		return frappe.get_doc(
			{
				"doctype": "Location",
				"location_name": location_name,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
