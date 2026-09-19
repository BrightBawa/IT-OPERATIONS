import frappe
from frappe.tests import IntegrationTestCase

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = ["Location", "IT Equipment"]


class IntegrationTestITMonitoringPoint(IntegrationTestCase):
	def test_rejects_invalid_ip_address(self):
		doc = frappe.get_doc(
			{
				"doctype": "IT Monitoring Point",
				"point_name": "Test Invalid IP",
				"point_type": "Camera",
				"camera_identifier": "TEST-CAM",
				"ip_address": "999.1.1.1",
			}
		)
		doc.before_validate()
		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	def test_non_camera_point_clears_camera_recorder_fields(self):
		doc = frappe.get_doc(
			{
				"doctype": "IT Monitoring Point",
				"point_name": "Test Server Point",
				"point_type": "Server",
				"nvr_name": "Should be cleared",
				"nvr_channel": "Should be cleared",
			}
		)
		doc.before_validate()
		doc.validate()
		self.assertIsNone(doc.nvr_name)
		self.assertIsNone(doc.nvr_channel)
