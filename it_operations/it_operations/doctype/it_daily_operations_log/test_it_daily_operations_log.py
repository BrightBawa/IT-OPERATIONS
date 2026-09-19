import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate

from it_operations.it_operations.doctype.it_daily_operations_log.it_daily_operations_log import (
	DEVICE_REQUIREMENTS,
	PASSING_DEVICE_VALUES,
	generate_logs,
	generate_logs_with_status,
)

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Employee",
	"User",
	"Location",
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

		test_day = {
			"test_device_result_is_calculated_from_simple_checks": 5,
			"test_generation_is_idempotent_and_refreshes_missing_rows": 6,
			"test_submission_requires_mandatory_checks_and_fault_remarks": 7,
			"test_equipment_types_only_require_applicable_checks": 8,
			"test_holiday_does_not_generate_a_log": 9,
			"test_weekend_does_not_generate_a_log": 10,
		}[self._testMethodName]
		self.test_date = getdate(add_days("2098-01-01", test_day))
		self.suffix = frappe.generate_hash(length=8)
		self.campus = frappe.get_doc(
			{
				"doctype": "Location",
				"location_name": f"Test Campus {self.suffix}",
				"custom_it_location_type": "Campus",
				"is_group": 1,
			}
		).insert(ignore_permissions=True)
		self.block = frappe.get_doc(
			{
				"doctype": "Location",
				"location_name": f"Test Block {self.suffix}",
				"custom_it_location_type": "Block",
				"parent_location": self.campus.name,
				"is_group": 1,
			}
		).insert(ignore_permissions=True)
		self.location = frappe.get_doc(
			{
				"doctype": "Location",
				"location_name": f"Test Asset Location {self.suffix}",
				"custom_it_location_type": "Room",
				"parent_location": self.block.name,
				"is_group": 0,
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
		self.equipment = frappe.get_doc(
			{
				"doctype": "IT Equipment",
				"equipment_name": f"Test Camera {self.suffix}",
				"equipment_type": "CCTV Camera",
				"serial_number": f"SERIAL-{self.suffix}",
				"location": self.location.name,
				"monitoring_point": self.point.name,
				"status": "Operational",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		self.point.db_set("equipment", self.equipment.name, update_modified=False)
		self.template = frappe.get_doc(
			{
				"doctype": "IT Checklist Template",
				"template_name": f"Test CCTV Template {self.suffix}",
				"responsibility_type": "CCTV Equipment Inspection",
				"is_active": 1,
				"items": [
					{
						"check_title": "Confirm camera is online",
						"check_type": "Camera",
						"monitoring_point": self.point.name,
						"equipment": self.equipment.name,
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
				"responsibility_type": "CCTV Equipment Inspection",
				"checklist_template": self.template.name,
				"start_date": self.test_date,
				"end_date": self.test_date,
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
		self.assertEqual(log.check_items[0].device_kind, "CCTV Camera")
		self.assertEqual(log.check_items[0].serial_number, f"SERIAL-{self.suffix}")
		self.assertEqual(log.check_items[0].online_status, "Not Checked")
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
				"equipment": self.equipment.name,
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
				row.online_status = "Offline"
				row.working_status = "Not Working"
				row.alignment_status = "Aligned"
				row.recording_status = "Not Recording"
				row.playback_status = "Not Working"
		with self.assertRaises(frappe.ValidationError):
			log.save(ignore_permissions=True)

		log.reload()
		for row in log.check_items:
			if row.mandatory:
				row.online_status = "Offline"
				row.working_status = "Not Working"
				row.alignment_status = "Aligned"
				row.recording_status = "Not Recording"
				row.playback_status = "Not Working"
				row.remarks = "No video signal"
		log.save(ignore_permissions=True)
		self.assertEqual(log.check_items[0].status, "Fault")
		self.assertEqual(log.check_items[0].checked_by, "Administrator")
		self.assertTrue(log.check_items[0].checked_at)
		log.submit()
		self.assertEqual(log.status, "Submitted")
		self.assertTrue(log.submitted_at)
		self.assertEqual(log.submitted_by, "Administrator")

	def test_device_result_is_calculated_from_simple_checks(self):
		name = generate_logs(self.test_date, employee=self.employee)[0]
		log = frappe.get_doc("IT Daily Operations Log", name)
		row = log.check_items[0]
		row.online_status = "Online"
		row.working_status = "Working"
		row.alignment_status = "Aligned"
		row.recording_status = "Recording"
		row.playback_status = "Working"
		log.save(ignore_permissions=True)

		self.assertEqual(row.status, "OK")
		self.assertEqual(log.completed_checks, 1)
		self.assertEqual(log.completion_rate, 100)

	def test_equipment_types_only_require_applicable_checks(self):
		log = frappe.new_doc("IT Daily Operations Log")
		for device_kind in ("Television", "Wireless Access Point"):
			row = log.append("check_items", {"device_kind": device_kind})
			required_fields = DEVICE_REQUIREMENTS[device_kind]
			for field in required_fields:
				row.set(field, PASSING_DEVICE_VALUES[field])

		log._set_device_results()

		for row in log.check_items:
			self.assertEqual(row.status, "OK")
			for field in PASSING_DEVICE_VALUES:
				expected = (
					PASSING_DEVICE_VALUES[field]
					if field in DEVICE_REQUIREMENTS[row.device_kind]
					else "Not Applicable"
				)
				self.assertEqual(row.get(field), expected)

	def test_holiday_does_not_generate_a_log(self):
		holiday_list = frappe.get_doc(
			{
				"doctype": "Holiday List",
				"holiday_list_name": f"IT Operations Test Holidays {self.suffix}",
				"from_date": self.test_date,
				"to_date": self.test_date,
				"holidays": [
					{
						"holiday_date": self.test_date,
						"description": "Test Public Holiday",
					}
				],
			}
		).insert(ignore_permissions=True)
		if frappe.db.exists("DocType", "Holiday List Assignment"):
			assignment = frappe.get_doc(
				{
					"doctype": "Holiday List Assignment",
					"applicable_for": "Employee",
					"assigned_to": self.employee,
					"holiday_list": holiday_list.name,
					"from_date": self.test_date,
				}
			).insert(ignore_permissions=True)
			assignment.submit()
		else:
			frappe.db.set_value("Employee", self.employee, "holiday_list", holiday_list.name)

		result = generate_logs_with_status(self.test_date, employee=self.employee)

		self.assertEqual(result.logs, [])
		self.assertEqual(result.non_working_day.code, "holiday")
		self.assertIn("Test Public Holiday", result.non_working_day.reason)
		self.assertFalse(
			frappe.db.exists(
				"IT Daily Operations Log",
				{"log_key": f"{self.test_date.isoformat()}::{self.employee}"},
			)
		)

	def test_weekend_does_not_generate_a_log(self):
		result = generate_logs_with_status(self.test_date, employee=self.employee)

		self.assertEqual(result.logs, [])
		self.assertEqual(result.non_working_day.code, "weekend")
		self.assertIn("Saturday", result.non_working_day.reason)
