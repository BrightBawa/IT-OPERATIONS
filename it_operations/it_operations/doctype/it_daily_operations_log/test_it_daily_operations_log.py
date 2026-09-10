import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import getdate

from it_operations.it_operations.doctype.it_daily_operations_log.it_daily_operations_log import generate_logs


EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Employee",
	"User",
	"IT Location",
	"IT Monitoring Point",
	"IT Equipment",
	"IT Responsibility Assignment",
	"IT Checklist Template",
]


class IntegrationTestITDailyOperationsLog(IntegrationTestCase):
	def setUp(self):
		self.employee = frappe.db.get_value(
			"Employee",
			{"status": "Active", "user_id": ("is", "set")},
			"name",
		)
		if not self.employee:
			self.skipTest("No active Employee linked to an enabled User is available")

		self.test_date = getdate("2099-12-31")
		self.suffix = frappe.generate_hash(length=8)
		self.location = frappe.get_doc(
			{
				"doctype": "IT Location",
				"location_name": f"Test IT Location {self.suffix}",
				"location_type": "Room",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		self.point = frappe.get_doc(
			{
				"doctype": "IT Monitoring Point",
				"point_name": f"Test Camera {self.suffix}",
				"location": self.location.name,
				"point_type": "Camera",
				"camera_identifier": f"CAM-{self.suffix}",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		self.template = frappe.get_doc(
			{
				"doctype": "IT Checklist Template",
				"template_name": f"Test CCTV Template {self.suffix}",
				"responsibility_type": "CCTV Monitoring",
				"is_active": 1,
				"items": [
					{
						"check_title": "Confirm camera is online",
						"check_type": "Camera",
						"monitoring_point": self.point.name,
						"mandatory": 1,
					}
				],
			}
		).insert(ignore_permissions=True)
		self.assignment = frappe.get_doc(
			{
				"doctype": "IT Responsibility Assignment",
				"employee": self.employee,
				"location": self.location.name,
				"responsibility_type": "CCTV Monitoring",
				"checklist_template": self.template.name,
				"start_date": self.test_date,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)

	def test_generation_is_idempotent_and_refreshes_missing_rows(self):
		first = generate_logs(self.test_date, employee=self.employee)
		second = generate_logs(self.test_date, employee=self.employee)
		self.assertEqual(first, second)
		self.assertEqual(len(first), 1)
		log = frappe.get_doc("IT Daily Operations Log", first[0])
		self.assertEqual(len(log.check_items), 1)
		log.check_items[0].mandatory = 0
		with self.assertRaises(frappe.ValidationError):
			log.save(ignore_permissions=True)
		log.reload()
		log.remove(log.check_items[0])
		with self.assertRaises(frappe.ValidationError):
			log.save(ignore_permissions=True)
		log.reload()

		self.template.append(
			"items",
			{
				"check_title": "Confirm recorded image is clear",
				"check_type": "Camera",
				"monitoring_point": self.point.name,
				"mandatory": 0,
			},
		)
		self.template.save(ignore_permissions=True)
		generate_logs(self.test_date, employee=self.employee, regenerate=True)
		log.reload()
		self.assertEqual(len(log.check_items), 2)

	def test_submission_requires_mandatory_checks_and_fault_remarks(self):
		name = generate_logs(self.test_date, employee=self.employee)[0]
		log = frappe.get_doc("IT Daily Operations Log", name)
		with self.assertRaises(frappe.ValidationError):
			log.submit()

		log.reload()
		for row in log.check_items:
			if row.mandatory:
				row.status = "Fault"
		with self.assertRaises(frappe.ValidationError):
			log.save(ignore_permissions=True)

		log.reload()
		for row in log.check_items:
			if row.mandatory:
				row.status = "Fault"
				row.remarks = "No video signal"
		log.save(ignore_permissions=True)
		self.assertEqual(log.check_items[0].checked_by, "Administrator")
		self.assertTrue(log.check_items[0].checked_at)
		log.submit()
		self.assertEqual(log.status, "Submitted")
		self.assertTrue(log.submitted_at)
		self.assertEqual(log.submitted_by, "Administrator")
