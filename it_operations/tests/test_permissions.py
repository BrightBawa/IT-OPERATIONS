from unittest.mock import patch

from frappe.tests import UnitTestCase

from it_operations.permissions import assignment_query, daily_log_query


class TestPermissionQueries(UnitTestCase):
	def test_operations_user_query_is_limited_to_own_logs(self):
		with patch("it_operations.permissions.frappe.get_roles", return_value=["IT Operations User"]):
			condition = daily_log_query("operator@example.com")
		self.assertIn("assigned_user", condition)
		self.assertNotIn("supervisor_user", condition)

	def test_supervisor_query_includes_self_and_team(self):
		with patch("it_operations.permissions.frappe.get_roles", return_value=["IT Operations Supervisor"]):
			log_condition = daily_log_query("supervisor@example.com")
			assignment_condition = assignment_query("supervisor@example.com")
		self.assertIn("assigned_user", log_condition)
		self.assertIn("supervisor_user", log_condition)
		self.assertIn("employee_user", assignment_condition)
		self.assertIn("supervisor_user", assignment_condition)

	def test_manager_query_has_no_row_restriction(self):
		with patch("it_operations.permissions.frappe.get_roles", return_value=["IT Operations Manager"]):
			self.assertEqual(daily_log_query("manager@example.com"), "")
			self.assertEqual(assignment_query("manager@example.com"), "")
