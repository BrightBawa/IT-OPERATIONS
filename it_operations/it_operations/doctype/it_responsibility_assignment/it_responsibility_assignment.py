import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from it_operations.permissions import employee_user, is_manager, supervisor_user_for_employee


class ITResponsibilityAssignment(Document):
	def before_validate(self):
		self.notes = (self.notes or "").strip() or None
		self.employee_user = employee_user(self.employee)
		self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
		if not self.supervisor:
			self.supervisor = frappe.db.get_value("Employee", self.employee, "reports_to")
		self.supervisor_user = employee_user(self.supervisor) or supervisor_user_for_employee(self.employee)

	def validate(self):
		self._validate_identity_change()
		self._validate_employee()
		self._validate_dates()
		self._validate_assignment_links()
		self._validate_overlapping_assignment()

	def _validate_identity_change(self):
		old = None if self.is_new() else self.get_doc_before_save()
		if old and old.employee != self.employee and not is_manager():
			frappe.throw(
				_("Only an IT Operations Manager can change the assigned Employee."), frappe.PermissionError
			)

	def _validate_employee(self):
		employee_status = frappe.db.get_value("Employee", self.employee, "status")
		if not employee_status:
			frappe.throw(_("Employee {0} does not exist.").format(frappe.bold(self.employee)))
		if self.is_active and employee_status != "Active":
			frappe.throw(_("An active assignment requires an active Employee."))
		if not self.employee_user:
			frappe.throw(_("The assigned Employee must be linked to a system User."))
		if self.is_active and not frappe.db.get_value("User", self.employee_user, "enabled"):
			frappe.throw(_("The assigned Employee must be linked to an enabled User."))

	def _validate_dates(self):
		if self.end_date and getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(_("End Date cannot be before Start Date."))

	def _validate_assignment_links(self):
		responsibility_is_active = frappe.db.get_value(
			"IT Responsibility Type", self.responsibility_type, "is_active"
		)
		if responsibility_is_active is None:
			frappe.throw(
				_("Responsibility Type {0} does not exist.").format(frappe.bold(self.responsibility_type))
			)

		template = frappe.db.get_value(
			"IT Checklist Template",
			self.checklist_template,
			["responsibility_type", "is_active"],
			as_dict=True,
		)
		if not template:
			frappe.throw(
				_("Checklist Template {0} does not exist.").format(frappe.bold(self.checklist_template))
			)
		if template.responsibility_type != self.responsibility_type:
			frappe.throw(_("The checklist template responsibility type must match this assignment."))
		if self.is_active and (not responsibility_is_active or not template.is_active):
			frappe.throw(
				_("An active assignment requires an active Responsibility Type and Checklist Template.")
			)
		if not frappe.db.exists("Location", self.location):
			frappe.throw(_("Asset Location {0} does not exist.").format(frappe.bold(self.location)))

	def _validate_overlapping_assignment(self):
		if not self.is_active:
			return

		filters = {
			"employee": self.employee,
			"location": self.location,
			"responsibility_type": self.responsibility_type,
			"checklist_template": self.checklist_template,
			"is_active": 1,
			"start_date": ("<=", self.end_date or "9999-12-31"),
		}
		for assignment in frappe.get_all(
			"IT Responsibility Assignment",
			filters=filters,
			fields=["name", "end_date"],
		):
			if assignment.name == self.name:
				continue
			if not assignment.end_date or getdate(assignment.end_date) >= getdate(self.start_date):
				frappe.throw(
					_(
						"Assignment {0} already covers this Employee, Location, responsibility, and date range."
					).format(frappe.bold(assignment.name))
				)


def on_doctype_update():
	frappe.db.add_index("IT Responsibility Assignment", ["employee", "is_active", "start_date", "end_date"])
	frappe.db.add_index("IT Responsibility Assignment", ["location", "responsibility_type", "is_active"])
	frappe.db.add_index("IT Responsibility Assignment", ["employee_user"])
	frappe.db.add_index("IT Responsibility Assignment", ["supervisor_user"])
