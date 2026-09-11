from unittest import TestCase

from it_operations.setup.block_c_cctv import _assigned_class, _channel_location


class TestBlockCCCTVChannels(TestCase):
	def test_classroom_channel_returns_room_and_assigned_class(self):
		channel = "10C2-B08F1CR06 (1-020)"
		self.assertEqual(_channel_location(channel), ("Room", "B08F1CR06"))
		self.assertEqual(_assigned_class(channel), "10C2")

	def test_corridor_channel_returns_its_floor_without_a_class(self):
		self.assertEqual(_channel_location("24CR-0C-03 (1-016)"), ("Floor", "B08F0"))
		self.assertEqual(_channel_location("24CR-1C-04 (1-009)"), ("Floor", "B08F1"))
		self.assertEqual(_channel_location("24CR-2C-01 (1-025)"), ("Floor", "B08F2"))
		self.assertIsNone(_assigned_class("24CR-1C-04 (1-009)"))

	def test_office_channel_is_a_room_without_an_assigned_class(self):
		channel = "OFFICE-B08F0CR01 (1-003)"
		self.assertEqual(_channel_location(channel), ("Room", "B08F0CR01"))
		self.assertIsNone(_assigned_class(channel))
