import frappe
from frappe.tests import IntegrationTestCase

from it_operations.setup.locations import ensure_classroom_floor, ensure_location


IGNORE_TEST_RECORD_DEPENDENCIES = ["Location", "Student Batch Name"]


class IntegrationTestAssetLocation(IntegrationTestCase):
	def test_campus_block_floor_room_hierarchy(self):
		suffix = frappe.generate_hash(length=8).upper()
		student_batch = self._insert_student_batch(f"Test Batch {suffix}")
		branch = self._insert_branch(f"Test Branch {suffix}")
		campus = ensure_location(
			f"Test Campus {suffix}", f"TC-{suffix}", "Campus", campus=branch.name
		)
		block = ensure_location(
			f"Test Block {suffix}", f"TB-{suffix}", "Block", parent_location=campus
		)
		floor = ensure_location(
			f"Test Floor {suffix}", f"TF-{suffix}", "Floor", parent_location=block
		)
		room = ensure_location(
			f"Test Room {suffix}",
			f"TR-{suffix}",
			"Room",
			parent_location=floor,
			assigned_class=student_batch.name,
		)

		block_doc = frappe.get_doc("Location", block)
		room_doc = frappe.get_doc("Location", room)
		campus_doc = frappe.get_doc("Location", campus)
		self.assertEqual(block_doc.custom_campus_branch, branch.name)
		self.assertEqual(room_doc.custom_campus_branch, branch.name)
		self.assertEqual(room_doc.custom_assigned_class, student_batch.name)
		self.assertEqual(room_doc.is_group, 0)
		self.assertGreater(campus_doc.rgt, room_doc.rgt)
		self.assertLess(campus_doc.lft, room_doc.lft)

	def test_existing_location_cannot_be_silently_moved(self):
		suffix = frappe.generate_hash(length=8).upper()
		first_parent = ensure_location(
			f"First Parent {suffix}", f"FP-{suffix}", "Campus"
		)
		second_parent = ensure_location(
			f"Second Parent {suffix}", f"SP-{suffix}", "Campus"
		)
		child_name = f"Test Child {suffix}"
		ensure_location(child_name, f"TC-{suffix}", "Block", parent_location=first_parent)

		with self.assertRaises(frappe.ValidationError):
			ensure_location(child_name, f"TC-{suffix}", "Block", parent_location=second_parent)

	def test_ensure_classroom_floor_creates_sequential_room_codes(self):
		suffix = frappe.generate_hash(length=8).upper()
		campus = ensure_location(f"Test Campus {suffix}", f"TC-{suffix}", "Campus")
		block = ensure_location(
			f"Test Block {suffix}", f"TB-{suffix}", "Block", parent_location=campus
		)
		floor_code = f"T{suffix}F2"

		floor, rooms = ensure_classroom_floor(block, floor_code, 8)
		second_floor, second_rooms = ensure_classroom_floor(block, floor_code, 8)

		self.assertEqual(
			frappe.db.get_value("Location", floor, "custom_it_location_type"), "Floor"
		)
		self.assertEqual(len(rooms), 8)
		self.assertEqual(second_floor, floor)
		self.assertEqual(second_rooms, rooms)
		self.assertEqual(
			frappe.get_all(
				"Location",
				filters={"parent_location": floor},
				pluck="custom_it_location_code",
				order_by="custom_it_location_code asc",
			),
			[f"{floor_code}CR{room_number:02d}" for room_number in range(1, 9)],
		)

	def _insert_branch(self, branch_name):
		return frappe.get_doc({"doctype": "Branch", "branch": branch_name}).insert(
			ignore_permissions=True
		)

	def _insert_student_batch(self, batch_name):
		return frappe.get_doc(
			{"doctype": "Student Batch Name", "batch_name": batch_name}
		).insert(ignore_permissions=True)
