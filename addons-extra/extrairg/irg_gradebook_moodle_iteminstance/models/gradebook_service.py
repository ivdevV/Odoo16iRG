from odoo.addons.irg_gradebook_moodle_wizard.models.gradebook_service import (
    GradebookMoodleService,
)


class IteminstanceGradebookMoodleService(GradebookMoodleService):
    """Validate the activity-instance ID consumed by this bridge."""

    @classmethod
    def _validate_grade_payload(cls, payload):
        usergrades = super()._validate_grade_payload(payload)
        for usergrade in usergrades:
            for item in usergrade["gradeitems"]:
                iteminstance = item.get("iteminstance")
                if iteminstance is not None and type(iteminstance) is not int:
                    cls._raise_invalid_response()
        return usergrades
