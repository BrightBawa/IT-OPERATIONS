import json
from pathlib import Path

from frappe.tests import UnitTestCase

DOCTYPE_ROOT = Path(__file__).parents[1] / "it_operations" / "doctype"
SEARCHABLE_DOCTYPES = {
	"it_checklist_template": ("template_name", {"responsibility_type"}),
	"it_daily_operations_log": ("employee_name", {"employee", "operation_date", "status"}),
	"it_equipment": (
		"equipment_name",
		{"equipment_type", "location", "deployment_status", "status"},
	),
	"it_location": ("location_name", {"location_code", "full_location_path"}),
	"it_monitoring_point": ("point_name", {"location", "point_type"}),
	"it_responsibility_assignment": (
		"employee_name",
		{"employee", "location", "responsibility_type", "checklist_template"},
	),
	"it_responsibility_type": ("responsibility_type_name", {"inspection_frequency"}),
}


class TestDoctypeSearchMetadata(UnitTestCase):
	def test_link_search_metadata_is_consistent(self):
		for directory, (title_field, expected_search_fields) in SEARCHABLE_DOCTYPES.items():
			with self.subTest(doctype=directory):
				definition = self._load_definition(directory)
				fieldnames = {field["fieldname"] for field in definition["fields"]}
				search_fields = {
					fieldname.strip()
					for fieldname in definition.get("search_fields", "").split(",")
					if fieldname.strip()
				}

				self.assertEqual(definition.get("title_field"), title_field)
				self.assertEqual(definition.get("show_title_field_in_link"), 1)
				self.assertTrue(search_fields <= fieldnames)
				self.assertIn(title_field, search_fields)
				self.assertTrue(expected_search_fields <= search_fields)

	@staticmethod
	def _load_definition(directory):
		path = DOCTYPE_ROOT / directory / f"{directory}.json"
		with path.open(encoding="utf-8") as source:
			return json.load(source)
