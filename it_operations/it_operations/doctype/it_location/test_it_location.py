import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestITLocation(IntegrationTestCase):
	def test_campus_block_floor_room_hierarchy(self):
		suffix = frappe.generate_hash(length=8)
		branch = self._insert_branch(f"Test Branch {suffix}")
		campus = self._insert(f"Test Campus {suffix}", "Campus", campus=branch.name)
		block = self._insert("Block A", "Block", campus.name)
		floor = self._insert("F1", "Floor", block.name)
		room = self._insert("B01F1CR01", "Room", floor.name)

		self.assertEqual(block.campus, branch.name)
		self.assertEqual(room.campus, branch.name)
		self.assertEqual(
			room.full_location_path,
			f"{campus.location_name} / Block A / F1 / B01F1CR01",
		)
		self.assertEqual(room.is_group, 0)
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
		branch = self._insert_branch(f"Test Branch {suffix}")
		campus = self._insert(f"Test Campus {suffix}", "Campus", campus=branch.name)
		with self.assertRaises(frappe.ValidationError):
			self._insert("Invalid Room", "Room", campus.name)

	def _insert(self, location_name, location_type, parent_location=None, campus=None):
		return frappe.get_doc(
			{
				"doctype": "IT Location",
				"location_name": location_name,
				"location_type": location_type,
				"parent_location": parent_location,
				"campus": campus,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)

	def _insert_branch(self, branch_name):
		return frappe.get_doc({"doctype": "Branch", "branch": branch_name}).insert(ignore_permissions=True)
