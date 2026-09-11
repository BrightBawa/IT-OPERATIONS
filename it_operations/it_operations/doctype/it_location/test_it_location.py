import frappe
from frappe.tests import IntegrationTestCase

from it_operations.setup.locations import ensure_classroom_floor


IGNORE_TEST_RECORD_DEPENDENCIES = ["Student Batch Name"]


class IntegrationTestITLocation(IntegrationTestCase):
	def test_campus_block_floor_room_hierarchy(self):
		suffix = frappe.generate_hash(length=8)
		student_batch = self._insert_student_batch(f"Test Batch {suffix}")
		branch = self._insert_branch(f"Test Branch {suffix}")
		campus = self._insert(f"Test Campus {suffix}", "Campus", campus=branch.name)
		block = self._insert("Block A", "Block", campus.name)
		floor = self._insert("F1", "Floor", block.name)
		room = self._insert("B01F1CR01", "Room", floor.name, assigned_class=student_batch.name)

		self.assertEqual(block.campus, branch.name)
		self.assertEqual(room.campus, branch.name)
		self.assertEqual(
			room.full_location_path,
			f"{campus.location_name} / Block A / F1 / B01F1CR01",
		)
		self.assertEqual(room.is_group, 0)
		self.assertEqual(room.assigned_class, student_batch.name)
		campus.reload()
		self.assertGreater(campus.rgt, room.rgt)
		self.assertLess(campus.lft, room.lft)

		second_branch = self._insert_branch(f"Second Branch {suffix}")
		second_campus = self._insert(f"Second Campus {suffix}", "Campus", campus=second_branch.name)
		second_block = self._insert("Block A", "Block", second_campus.name)
		self.assertEqual(second_block.location_name, block.location_name)
		self.assertNotEqual(second_block.name, block.name)

	def test_non_campus_location_requires_valid_parent(self):
		with self.assertRaises(frappe.ValidationError):
			self._insert("Orphan Block", "Block")

		suffix = frappe.generate_hash(length=8)
		student_batch = self._insert_student_batch(f"Test Batch {suffix}")
		branch = self._insert_branch(f"Test Branch {suffix}")
		campus = self._insert(f"Test Campus {suffix}", "Campus", campus=branch.name)
		block = self._insert("Block A", "Block", campus.name)
		with self.assertRaises(frappe.ValidationError):
			self._insert("Invalid Room", "Room", campus.name)
		with self.assertRaises(frappe.ValidationError):
			self._insert(
				"Invalid Assigned Class", "Floor", block.name, assigned_class=student_batch.name
			)

	def test_ensure_classroom_floor_creates_sequential_room_codes(self):
		suffix = frappe.generate_hash(length=8).upper()
		branch = self._insert_branch(f"Test Branch {suffix}")
		campus = self._insert(f"Test Campus {suffix}", "Campus", campus=branch.name)
		block = self._insert("Block C", "Block", campus.name)
		floor_code = f"T{suffix}F2"

		floor, rooms = ensure_classroom_floor(block.name, floor_code, 8)
		second_floor, second_rooms = ensure_classroom_floor(block.name, floor_code, 8)

		self.assertEqual(frappe.db.get_value("IT Location", floor, "location_type"), "Floor")
		self.assertEqual(len(rooms), 8)
		self.assertEqual(second_floor, floor)
		self.assertEqual(second_rooms, rooms)
		self.assertEqual(
			frappe.get_all(
				"IT Location",
				filters={"parent_location": floor},
				pluck="location_code",
				order_by="location_code asc",
			),
			[f"{floor_code}CR{room_number:02d}" for room_number in range(1, 9)],
		)

	def _insert(
		self, location_name, location_type, parent_location=None, campus=None, assigned_class=None
	):
		return frappe.get_doc(
			{
				"doctype": "IT Location",
				"location_name": location_name,
				"location_type": location_type,
				"parent_location": parent_location,
				"campus": campus,
				"assigned_class": assigned_class,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)

	def _insert_branch(self, branch_name):
		return frappe.get_doc({"doctype": "Branch", "branch": branch_name}).insert(ignore_permissions=True)

	def _insert_student_batch(self, batch_name):
		return frappe.get_doc(
			{"doctype": "Student Batch Name", "batch_name": batch_name}
		).insert(ignore_permissions=True)
