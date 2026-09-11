from collections import Counter
from unittest import TestCase

from it_operations.importers.block_a_devices import (
	BLOCK_A_DEVICES,
	_device_dict,
	_equipment_notes,
	_equipment_type,
	_validate_device,
)


class TestBlockAImporter(TestCase):
	def test_source_contains_expected_valid_inventory(self):
		rows = [_device_dict(values) for values in BLOCK_A_DEVICES]
		self.assertEqual(len(rows), 55)
		self.assertTrue(all(_validate_device(row) is None for row in rows))
		for field in ("serial_number", "short_serial", "ip_address", "mac_address"):
			self.assertEqual(len({row[field] for row in rows}), 55)

	def test_equipment_types_match_source_inventory(self):
		counts = Counter(_equipment_type(_device_dict(values)) for values in BLOCK_A_DEVICES)
		self.assertEqual(
			counts,
			{"CCTV Camera": 50, "Network Video Recorder": 4, "Network Switch": 1},
		)

	def test_notes_include_supported_metadata_without_credentials(self):
		notes = _equipment_notes(_device_dict(BLOCK_A_DEVICES[0]))
		for label in ("IP:", "Model:", "Short Serial:", "Web Version:", "MAC:"):
			self.assertIn(label, notes)
		self.assertNotIn("Password", notes)
