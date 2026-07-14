# ruff: noqa: F821

logins = [
    "validation.campus.operator@example.test",
    "validation.campus.faculty@example.test",
    "validation.campus.portal@example.test",
]
users = env["res.users"].with_context(active_test=False).search([("login", "in", logins)])
users.write({"active": False})
env.cr.commit()
print("CLEANUP_OK archived_user_ids=%s" % users.ids)
