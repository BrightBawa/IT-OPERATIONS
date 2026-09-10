import frappe


USER_ROLE = "IT Operations User"
SUPERVISOR_ROLE = "IT Operations Supervisor"
MANAGER_ROLE = "IT Operations Manager"


def _roles(user):
	return set(frappe.get_roles(user))


def is_manager(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or MANAGER_ROLE in _roles(user) or "System Manager" in _roles(user)


def is_supervisor(user=None):
	return SUPERVISOR_ROLE in _roles(user or frappe.session.user)


def require_manager(user=None):
	if not is_manager(user):
		frappe.throw("IT Operations Manager access is required.", frappe.PermissionError)


def employee_user(employee):
	return frappe.db.get_value("Employee", employee, "user_id") if employee else None


def supervisor_user_for_employee(employee):
	if not employee:
		return None
	reports_to = frappe.db.get_value("Employee", employee, "reports_to")
	return employee_user(reports_to)


def can_access_employee(employee, user=None, supervisor_user=None):
	user = user or frappe.session.user
	if is_manager(user):
		return True
	if employee_user(employee) == user:
		return True
	if not is_supervisor(user):
		return False
	return (supervisor_user or supervisor_user_for_employee(employee)) == user


def _daily_condition(user):
	escaped_user = frappe.db.escape(user)
	if is_supervisor(user):
		return (
			f"(`tabIT Daily Operations Log`.`assigned_user` = {escaped_user} "
			f"or `tabIT Daily Operations Log`.`supervisor_user` = {escaped_user})"
		)
	return f"`tabIT Daily Operations Log`.`assigned_user` = {escaped_user}"


def daily_log_query(user=None):
	user = user or frappe.session.user
	if is_manager(user):
		return ""
	return _daily_condition(user)


def daily_log_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if is_manager(user):
		return True
	if permission_type == "create" and not getattr(doc, "employee", None):
		return bool({USER_ROLE, SUPERVISOR_ROLE} & _roles(user))
	return can_access_employee(doc.employee, user, getattr(doc, "supervisor_user", None))


def assignment_query(user=None):
	user = user or frappe.session.user
	if is_manager(user):
		return ""
	escaped_user = frappe.db.escape(user)
	if is_supervisor(user):
		return (
			f"(`tabIT Responsibility Assignment`.`employee_user` = {escaped_user} "
			f"or `tabIT Responsibility Assignment`.`supervisor_user` = {escaped_user})"
		)
	return f"`tabIT Responsibility Assignment`.`employee_user` = {escaped_user}"


def assignment_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if is_manager(user):
		return True
	if permission_type == "create" and not getattr(doc, "employee", None):
		return is_supervisor(user)
	return can_access_employee(doc.employee, user, getattr(doc, "supervisor_user", None))
