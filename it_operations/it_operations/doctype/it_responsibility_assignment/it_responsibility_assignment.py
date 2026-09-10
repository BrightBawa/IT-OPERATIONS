import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from it_operations.permissions import employee_user, is_manager, supervisor_user_for_employee


class ITResponsibilityAssignment(Document):
	def before_validate(self):
		self.employee_user = employee_user(self.employee)
		if not self.supervisor:
			self.supervisor = frappe.db.get_value("Employee", self.employee, "reports_to")
		self.supervisor_user = employee_user(self.supervisor) or supervisor_user_for_employee(self.employee)

	def validate(self):
		old = None if self.is_new() else self.get_doc_before_save()
		if old and old.employee != self.employee and not is_manager():
			frappe.throw(_("Only an IT Operations Manager can change the assigned Employee."), frappe.PermissionError)
		if not self.employee_user:
			frappe.throw(_("The assigned Employee must be linked to a system User."))
		if self.end_date and getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(_("End Date cannot be before Start Date."))
		template_type = frappe.db.get_value("IT Checklist Template", self.checklist_template, "responsibility_type")
		if template_type and template_type != self.responsibility_type:
			frappe.throw(_("The checklist template responsibility type must match this assignment."))
