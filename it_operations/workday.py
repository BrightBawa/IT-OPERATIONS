import frappe
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from frappe import _
from frappe.utils import formatdate, getdate


def get_non_working_day(operation_date, employee=None):
	"""Return why an operations log is not required, or ``None`` for a workday."""
	operation_date = getdate(operation_date)
	if operation_date.weekday() >= 5:
		day_name = operation_date.strftime("%A")
		return frappe._dict(
			code="weekend",
			label=_(day_name),
			reason=_("{0} is a non-working day").format(_(day_name)),
		)

	holiday_lists = []
	operations_holiday_list = None
	if frappe.db.exists("DocType", "IT Operations Settings") and frappe.get_meta(
		"IT Operations Settings"
	).has_field("holiday_list"):
		operations_holiday_list = frappe.db.get_single_value("IT Operations Settings", "holiday_list")
		holiday_lists.append(operations_holiday_list)

	holiday_list = get_holiday_list_for_employee(
		employee,
		raise_exception=False,
		as_on=operation_date,
	)
	# HRMS resolves dated Holiday List Assignments. Keep ERPNext's employee/company
	# defaults as a fallback for sites that have not migrated those assignments yet.
	if not holiday_list:
		if employee:
			holiday_list, company = frappe.db.get_value(
				"Employee", employee, ["holiday_list", "company"]
			) or (None, None)
		else:
			holiday_list = None
			company = frappe.db.get_single_value("Global Defaults", "default_company")
		if not holiday_list and company:
			holiday_list = frappe.db.get_value("Company", company, "default_holiday_list")
	holiday_lists.append(holiday_list)
	holiday_lists = list(dict.fromkeys(name for name in holiday_lists if name))
	if not holiday_lists:
		return None

	holiday = frappe.db.get_value(
		"Holiday",
		{"parent": ("in", holiday_lists), "holiday_date": operation_date},
		["parent", "description", "is_half_day"],
		as_dict=True,
	)
	if not holiday:
		return None

	description = (holiday.description or "").strip() or _("Holiday")
	return frappe._dict(
		code="holiday",
		label=_("Holiday"),
		reason=_("Holiday: {0}").format(description),
		holiday_list=holiday.parent,
		description=description,
		is_half_day=bool(holiday.is_half_day),
		is_global=holiday.parent == operations_holiday_list,
	)


def no_submission_message(operation_date, non_working_day):
	return _("No IT operations log was generated for {0}. Reason: {1}. No submission is required.").format(
		formatdate(operation_date), non_working_day.reason
	)
