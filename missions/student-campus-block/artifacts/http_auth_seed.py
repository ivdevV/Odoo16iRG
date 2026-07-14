# ruff: noqa: F821

from odoo import Command


LOGIN_OPERATOR = "validation.campus.operator@example.test"
LOGIN_FACULTY = "validation.campus.faculty@example.test"
LOGIN_PORTAL = "validation.campus.portal@example.test"
PASSWORD = "ValidationCampus-2026!"

operator = env["res.users"].with_context(active_test=False).search(
    [("login", "=", LOGIN_OPERATOR)], limit=1
)
operator_values = {
        "name": "Validation Campus Operator",
        "login": LOGIN_OPERATOR,
        "email": LOGIN_OPERATOR,
        "password": PASSWORD,
        "active": True,
        "groups_id": [
            Command.set(
                [
                    env.ref("base.group_user").id,
                    env.ref("openeducat_core.group_op_back_office_admin").id,
                ]
            )
        ],
}
if operator:
    operator.write(operator_values)
else:
    operator = env["res.users"].with_context(no_reset_password=True).create(
        operator_values
    )

faculty = env["res.users"].with_context(active_test=False).search(
    [("login", "=", LOGIN_FACULTY)], limit=1
)
faculty_values = {
        "name": "Validation Campus Faculty",
        "login": LOGIN_FACULTY,
        "email": LOGIN_FACULTY,
        "password": PASSWORD,
        "active": True,
        "groups_id": [
            Command.set(
                [
                    env.ref("base.group_user").id,
                    env.ref("openeducat_core.group_op_faculty").id,
                ]
            )
        ],
}
if faculty:
    faculty.write(faculty_values)
else:
    faculty = env["res.users"].with_context(no_reset_password=True).create(
        faculty_values
    )

portal = env["res.users"].with_context(active_test=False).search(
    [("login", "=", LOGIN_PORTAL)], limit=1
)
if portal:
    partner = portal.partner_id
else:
    partner = env["res.partner"].create({
        "name": "Validation Campus Portal",
        "email": LOGIN_PORTAL,
    })
portal_values = {
        "name": partner.name,
        "login": LOGIN_PORTAL,
        "email": LOGIN_PORTAL,
        "partner_id": partner.id,
        "password": PASSWORD,
        "active": True,
        "groups_id": [Command.set([env.ref("base.group_portal").id])],
}
if portal:
    portal.write(portal_values)
else:
    portal = env["res.users"].with_context(no_reset_password=True).create(
        portal_values
    )
student = env["op.student"].with_context(active_test=False).search(
    [("user_id", "=", portal.id)], limit=1
)
if not student:
    student = env["op.student"].create({
        "partner_id": partner.id,
        "first_name": "Validation",
        "last_name": "Campus Portal",
        "gender": "o",
        "user_id": portal.id,
    })
env.cr.commit()
print(
    "SEED_OK operator_id=%s faculty_id=%s portal_id=%s student_id=%s"
    % (operator.id, faculty.id, portal.id, student.id)
)
