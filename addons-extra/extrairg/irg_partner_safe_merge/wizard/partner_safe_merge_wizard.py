import hashlib
import json
import re

from psycopg2 import sql

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


# This is an authorization boundary. Metadata may discover references but never
# adds an entry to these policies at runtime.
TRANSFER_ALLOWLIST = (
    ("res.users", "partner_id"),
    ("op.student", "partner_id"),
    ("crm.lead", "partner_id"),
    ("op.admission", "partner_id"),
    ("op.admission.elearning.wizard", "partner_id"),
    ("appisep.gradebook.summary", "student_id"),
    ("sale.order", "partner_id"),
    ("sale.order", "partner_invoice_id"),
    ("sale.order", "partner_shipping_id"),
    ("sale.order", "student_id"),
    ("sale.order.line", "student_id"),
    ("sale.subscription.schedule", "partner_id"),
    ("sale.subscription.schedule", "partner_invoice_id"),
    ("slide.channel.partner", "partner_id"),
    ("voip.phonecall", "partner_id"),
    ("stripe.subscription", "partner_id"),
)

RECALCULATE_ALLOWLIST = (
    ("sale.order.line", "order_partner_id"),
    ("sale.order", "commercial_partner_id"),
    ("crm.lead", "commercial_partner_id"),
    ("app.gradebook.student", "partner_id"),
    ("app.gradebook.subject", "partner_id"),
)

CONSERVE_ALLOWLIST = (
    ("mail.message", "author_id"),
    ("mail.notification", "res_partner_id"),
    ("ir.attachment", "partner_id"),
    ("sign.request.item", "partner_id"),
    ("sign.log", "partner_id"),
)

POLYMORPHIC_ALLOWLIST = (
    "mail.message",
    "mail.activity",
    "ir.attachment",
    "mail.followers",
)

PAYMENT_ACCOUNTING_BLOCKLIST = (
    ("res.partner.bank", "partner_id"),
    ("account.move", "partner_id"),
    ("account.move", "commercial_partner_id"),
    ("account.move.line", "partner_id"),
    ("account.payment", "partner_id"),
    ("payment.transaction", "partner_id"),
    ("payment.token", "partner_id"),
    ("payment.card", "partner_id"),
)

APPROVED_M2M_ALLOWLIST = (
    ("res.partner", "category_id"),
    ("res.partner.category", "partner_ids"),
)

ALLOWLISTED_TRANSIENTS = (("op.admission.elearning.wizard", "partner_id"),)

BUSINESS_COLLISION_POLICIES = {
    "op.admission": {
        "partner_field": "partner_id",
        "keys": (("register_id", "course_id", "batch_id"),),
    },
    "appisep.gradebook.summary": {
        "partner_field": "student_id",
        "keys": (("course_id", "batch_id"), ("admision_id",)),
    },
    "sale.order": {
        "partner_field": "partner_id",
        "keys": (("company_id", "client_order_ref"), ("admission_id",)),
    },
    "sale.subscription.schedule": {
        "partner_field": "partner_id",
        "keys": (("term_number", "date_due"),),
    },
}

SCALAR_ALLOWLIST = (
    "name",
    "email",
    "phone",
    "mobile",
    "vat",
    "l10n_latam_identification_type_id",
    "identification_id",
    "id_number",
    "birth_date",
    "lang",
    "country_id",
    "state_id",
    "city",
    "zip",
    "street",
    "street2",
    "is_student",
)


class IrgPartnerSafeMergeWizard(models.TransientModel):
    _name = "irg.partner.safe.merge.wizard"
    _description = "Partner Safe Merge"

    master_partner_id = fields.Many2one("res.partner", required=True)
    source_partner_id = fields.Many2one("res.partner", required=True)
    recommendation_reason = fields.Text(readonly=True)
    inventory_json = fields.Text(readonly=True, default="{}")
    prevalidation_status = fields.Text(readonly=True)
    preview_hash = fields.Char(readonly=True)
    preview_ready = fields.Boolean(readonly=True)
    confirmation_checked = fields.Boolean(string="I confirm this safe merge")
    conflict_ids = fields.One2many(
        "irg.partner.safe.merge.wizard.conflict", "wizard_id", readonly=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su or not self.env.context.get(
            "_irg_safe_merge_wizard_service"
        ):
            raise AccessError(_("Open safe merge from an authorized contact selection."))
        return super().create(vals_list)

    def write(self, vals):
        protected = {
            "master_partner_id",
            "source_partner_id",
            "recommendation_reason",
            "inventory_json",
            "prevalidation_status",
            "preview_hash",
            "preview_ready",
        }
        internal = self.env.su and self.env.context.get(
            "_irg_safe_merge_wizard_service"
        )
        if protected.intersection(vals) and not internal:
            raise AccessError(_("Generated safe-merge state cannot be changed by RPC."))
        return super().write(vals)

    @api.model
    def _assert_admin(self):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(_("Only a system administrator can safely merge contacts."))

    @api.model
    def create_from_selection(self, partner_ids):
        self._assert_admin()
        ids = [int(partner_id) for partner_id in partner_ids]
        if len(ids) != 2 or len(set(ids)) != 2:
            raise ValidationError(_("Select exactly two different contacts."))
        partners = self.env["res.partner"].with_context(active_test=False).browse(ids)
        if len(partners.exists()) != 2:
            raise ValidationError(_("Both selected contacts must still exist."))
        self._validate_pair(partners[0], partners[1])
        master, source, reason = self._recommend_master(partners[0], partners[1])
        wizard = self.with_context(_irg_safe_merge_wizard_service=True).sudo().create(
            {
                "master_partner_id": master.id,
                "source_partner_id": source.id,
                "recommendation_reason": reason,
                "prevalidation_status": _(
                    "Initial validation passed. Generate the final preview."
                ),
            }
        )
        return wizard.with_env(self.env)

    def action_swap(self):
        self.ensure_one()
        self._assert_admin()
        master, source = self.master_partner_id, self.source_partner_id
        self.with_context(_irg_safe_merge_wizard_service=True).sudo().write(
            {
                "master_partner_id": source.id,
                "source_partner_id": master.id,
                "preview_ready": False,
                "preview_hash": False,
                "inventory_json": "{}",
                "prevalidation_status": _(
                    "Master and source changed. Generate a new preview."
                ),
                "confirmation_checked": False,
            }
        )
        self.conflict_ids.with_context(_irg_safe_merge_line_service=True).sudo().unlink()
        return self._reopen_action()

    def action_preview(self):
        self.ensure_one()
        self._assert_admin()
        payload = self._preflight()
        if self._conflict_metadata() != self._expected_conflict_metadata(
            payload["conflicts"]
        ):
            self._replace_conflicts(payload["conflicts"])
            self.with_context(_irg_safe_merge_wizard_service=True).sudo().write(
                {
                    "inventory_json": self._json(payload["inventory"]),
                    "preview_hash": False,
                    "preview_ready": False,
                    "prevalidation_status": _(
                        "Review every scalar choice, then generate the final preview again."
                    ),
                    "confirmation_checked": False,
                }
            )
            if any(item["requires_choice"] for item in payload["conflicts"]):
                return self._reopen_action()
        self._validate_conflict_lines()
        payload["decisions"] = self._decision_snapshot()
        preview_hash = self._hash_payload(payload)
        self.with_context(_irg_safe_merge_wizard_service=True).sudo().write(
            {
                "inventory_json": self._json(payload["inventory"]),
                "preview_hash": preview_hash,
                "preview_ready": True,
                "prevalidation_status": _(
                    "Prevalidation passed. Review choices and confirm explicitly."
                ),
                "confirmation_checked": False,
            }
        )
        return self._reopen_action()

    def action_confirm(self):
        self.ensure_one()
        self._assert_admin()
        existing = self._existing_audit()
        if existing:
            return self._audit_action(existing)
        if not self.preview_ready or not self.preview_hash:
            raise ValidationError(_("Generate a successful preview before confirming."))
        if not self.confirmation_checked:
            raise ValidationError(_("Explicitly confirm the merge before continuing."))
        self._lock_generated_plan()
        self._lock_partners()
        existing = self._existing_audit()
        if existing:
            return self._audit_action(existing)
        payload = self._preflight()
        self._lock_inventory(payload["inventory"])
        self._lock_approved_m2m()
        payload = self._preflight()
        self._validate_conflict_lines()
        payload["decisions"] = self._decision_snapshot()
        current_hash = self._hash_payload(payload)
        if current_hash != self.preview_hash:
            raise ValidationError(
                _("The contacts changed after preview. Generate a new preview.")
            )
        audit = self._execute_merge(payload)
        return self._audit_action(audit)

    def _existing_audit(self):
        self.ensure_one()
        source = self.source_partner_id.with_context(active_test=False)
        audit = self.env["irg.partner.safe.merge.audit"].sudo().search(
            [("origin_partner_id", "=", source.id)], limit=1
        )
        if audit and source.irg_merged_into_partner_id == self.master_partner_id:
            return audit
        return self.env["irg.partner.safe.merge.audit"]

    def _preflight(self):
        self.ensure_one()
        self._assert_admin()
        master = self.master_partner_id.sudo().with_context(active_test=False)
        source = self.source_partner_id.sudo().with_context(active_test=False)
        self._validate_pair(master, source)
        student_user_links = self._validate_users_students(master, source)
        inventory = self._relation_inventory(master, source)
        conflicts = self._scalar_conflicts(master, source)
        return {
            "master_id": master.id,
            "source_id": source.id,
            "scalars": self._scalar_snapshot(master, source),
            "conflicts": conflicts,
            "inventory": inventory,
            "student_user_links": student_user_links,
        }

    @api.model
    def _validate_pair(self, master, source):
        if not master.exists() or not source.exists() or master == source:
            raise ValidationError(_("Master and source must be two existing contacts."))
        if not master.active or not source.active:
            raise ValidationError(_("Both contacts must be active before the merge."))
        if master.is_company or source.is_company:
            raise ValidationError(_("Safe merge only supports personal contacts."))
        if self._is_ancestor(master, source) or self._is_ancestor(source, master):
            raise ValidationError(_("Parent and child contacts cannot be merged."))
        if master.company_id and source.company_id and master.company_id != source.company_id:
            raise ValidationError(_("The contacts belong to incompatible companies."))
        if master.irg_merged_into_partner_id or source.irg_merged_into_partner_id:
            raise ValidationError(_("A contact already used as a merged source cannot be reused."))
        if not self._identity_matches(master, source):
            raise ValidationError(
                _(
                    "The contacts do not share a normalized email, phone number, "
                    "or identity document."
                )
            )

    @api.model
    def _is_ancestor(self, candidate, partner):
        current = partner.parent_id
        seen = set()
        while current and current.id not in seen:
            if current == candidate:
                return True
            seen.add(current.id)
            current = current.parent_id
        return False

    @api.model
    def _identity_matches(self, first, second):
        candidates = []
        candidates.append(
            (self._normalize_email(first.email), self._normalize_email(second.email))
        )
        for field_name in ("phone", "mobile"):
            if field_name in first._fields:
                candidates.append(
                    (
                        self._normalize_phone(first[field_name]),
                        self._normalize_phone(second[field_name]),
                    )
                )
        for field_name in ("vat", "identification_id", "id_number"):
            if field_name in first._fields:
                candidates.append(
                    (
                        self._normalize_document(first[field_name]),
                        self._normalize_document(second[field_name]),
                    )
                )
        return any(left and left == right for left, right in candidates)

    @api.model
    def _normalize_email(self, value):
        return (value or "").strip().casefold()

    @api.model
    def _normalize_phone(self, value):
        digits = re.sub(r"\D", "", value or "")
        return digits[-9:] if len(digits) >= 9 else digits

    @api.model
    def _normalize_document(self, value):
        return re.sub(r"[^0-9A-Z]", "", (value or "").upper())

    @api.model
    def _recommend_master(self, first, second):
        first_score = self._recommendation_score(first)
        second_score = self._recommendation_score(second)
        if first_score >= second_score:
            master, source = first, second
            winner, loser = first_score, second_score
        else:
            master, source = second, first
            winner, loser = second_score, first_score
        labels = (
            _("active/confirmed subscription"),
            _("confirmed sale"),
            _("payment history"),
            _("linked user/student"),
            _("contact completeness"),
            _("record age"),
        )
        reason = _("Recommended %(partner)s because it has priority by %(reason)s.") % {
            "partner": master.display_name,
            "reason": labels[next((i for i, pair in enumerate(zip(winner, loser)) if pair[0] != pair[1]), 5)],
        }
        return master, source, reason

    @api.model
    def _recommendation_score(self, partner):
        subscription_count = 0
        if "sale.subscription.schedule" in self.env:
            model = self.env["sale.subscription.schedule"].sudo()
            if "partner_id" in model._fields:
                domain = [("partner_id", "=", partner.id)]
                if "order_id" in model._fields and "state" in self.env["sale.order"]._fields:
                    domain.append(("order_id.state", "in", ("sale", "done")))
                subscription_count = model.search_count(domain)
        sale_count = self.env["sale.order"].sudo().search_count(
            [("partner_id", "=", partner.id), ("state", "in", ("sale", "done"))]
        )
        payment_count = 0
        for model_name, field_name in (
            ("account.payment", "partner_id"),
            ("payment.transaction", "partner_id"),
        ):
            if model_name in self.env and field_name in self.env[model_name]._fields:
                payment_count += self.env[model_name].sudo().search_count(
                    [(field_name, "=", partner.id)]
                )
        entity_count = 0
        for model_name in ("res.users", "op.student"):
            if model_name in self.env:
                entity_count += self.env[model_name].sudo().with_context(
                    active_test=False
                ).search_count([("partner_id", "=", partner.id)])
        completeness = sum(
            bool(partner[field_name])
            for field_name in SCALAR_ALLOWLIST
            if field_name in partner._fields
        )
        return (
            bool(subscription_count),
            bool(sale_count),
            bool(payment_count),
            bool(entity_count),
            completeness,
            -partner.id,
        )

    @api.model
    def _validate_users_students(self, master, source):
        users = self.env["res.users"].sudo().with_context(active_test=False)
        master_users = users.search([("partner_id", "=", master.id)], order="id")
        source_users = users.search([("partner_id", "=", source.id)], order="id")
        if len(master_users) > 1 or len(source_users) > 1:
            raise ValidationError(_("Each contact may have at most one linked user."))
        students = self.env["op.student"].sudo().with_context(active_test=False)
        master_students = students.search([("partner_id", "=", master.id)], order="id")
        source_students = students.search([("partner_id", "=", source.id)], order="id")
        if len(master_students) > 1 or len(source_students) > 1:
            raise ValidationError(_("Each contact may have at most one linked student."))
        if (master_users or master_students) and (source_users or source_students):
            raise ValidationError(
                _(
                    "Master and source both contain a user/student identity graph; "
                    "resolve it manually before merging."
                )
            )
        result = {}
        for label, student, expected_users, partner in (
            ("master", master_students, master_users, master),
            ("source", source_students, source_users, source),
        ):
            if student:
                linked_user = student.user_id
                if expected_users and linked_user != expected_users:
                    raise ValidationError(
                        _("A contact user and student must be linked to each other exactly.")
                    )
                if linked_user and (
                    not expected_users or linked_user.partner_id != partner
                ):
                    raise ValidationError(
                        _("Student and user do not point to the same contact.")
                    )
            result[label] = {
                "partner_id": partner.id,
                "user_id": expected_users.id if expected_users else None,
                "student_id": student.id if student else None,
                "student_user_id": student.user_id.id if student and student.user_id else None,
            }
        return result

    def _relation_inventory(self, master, source):
        inventory = []
        fields_meta = self.env["ir.model.fields"].sudo().search(
            [("ttype", "=", "many2one"), ("relation", "=", "res.partner")],
            order="model, name",
        )
        for metadata in fields_meta:
            model_name, field_name = metadata.model, metadata.name
            if model_name not in self.env:
                continue
            model = self.env[model_name].sudo().with_context(active_test=False)
            if not self._can_search_persistent_rows(model):
                continue
            field = model._fields.get(field_name)
            if not field or not field.store or getattr(model, "_transient", False):
                continue
            records = model.search([(field_name, "=", source.id)], order="id")
            if model_name == "res.partner":
                records -= source
            if not records:
                continue
            key = (model_name, field_name)
            action = self._classify_relation(key, field)
            item = {
                "model": model_name,
                "field": field_name,
                "action": action,
                "ids": records.ids,
            }
            inventory.append(item)
            if action == "block":
                raise ValidationError(
                    _(
                        "Merge blocked: %(count)s record(s) in %(model)s.%(field)s "
                        "reference the source and are not authorized for transfer."
                    )
                    % {
                        "count": len(records),
                        "model": model_name,
                        "field": field_name,
                    }
                )
        self._inventory_unknown_references(source, inventory)
        self._inventory_unknown_polymorphic(source, inventory)
        self._inventory_allowlisted_transients(source, inventory)
        self._inventory_many2many(master, source, inventory)
        self._inventory_direct_resources(source, inventory)
        self._inventory_follower_state(master, source, inventory)
        self._validate_business_collisions(master, source, inventory)
        self._validate_unique_collisions(master, inventory)
        inventory.sort(key=lambda item: (item["model"], item["field"], item["ids"]))
        return inventory

    @api.model
    def _can_search_persistent_rows(self, model):
        # `_auto = False` also covers searchable SQL views. Absence of `id` is
        # the narrow signal that this registry model cannot contain ORM rows.
        return "id" in model._fields

    @api.model
    def _classify_relation(self, key, field):
        if key in PAYMENT_ACCOUNTING_BLOCKLIST:
            return "block"
        if key == ("mail.followers", "partner_id"):
            return "union"
        if key in CONSERVE_ALLOWLIST:
            return "conserve"
        if key in RECALCULATE_ALLOWLIST:
            return "recalculate"
        if key in TRANSFER_ALLOWLIST:
            if field.compute or field.related:
                return "recalculate"
            return "transfer"
        return "block"

    def _inventory_allowlisted_transients(self, source, inventory):
        for model_name, field_name in ALLOWLISTED_TRANSIENTS:
            if model_name not in self.env:
                continue
            model = self.env[model_name].sudo().with_context(active_test=False)
            field = model._fields.get(field_name)
            if not field or field.comodel_name != "res.partner":
                raise ValidationError(
                    _("Allowlisted transient %(model)s.%(field)s is not installed as expected.")
                    % {"model": model_name, "field": field_name}
                )
            records = model.search([(field_name, "=", source.id)], order="id")
            if records:
                inventory.append(
                    {
                        "model": model_name,
                        "field": field_name,
                        "action": "transfer",
                        "ids": records.ids,
                    }
                )

    def _inventory_many2many(self, master, source, inventory):
        metadata_records = self.env["ir.model.fields"].sudo().search(
            [("ttype", "=", "many2many")], order="model, name"
        )
        for metadata in metadata_records:
            if metadata.model not in self.env:
                continue
            model = self.env[metadata.model].sudo().with_context(active_test=False)
            if not self._can_search_persistent_rows(model):
                continue
            field = model._fields.get(metadata.name)
            if not field or not field.store:
                continue
            key = (metadata.model, metadata.name)
            if key in APPROVED_M2M_ALLOWLIST:
                continue
            if metadata.model == "res.partner":
                values = source.sudo()[metadata.name]
                if values:
                    raise ValidationError(
                        _(
                            "Merge blocked by non-approved direct Many2many "
                            "res.partner.%(field)s values %(ids)s."
                        )
                        % {"field": metadata.name, "ids": values.ids}
                    )
                continue
            if field.comodel_name != "res.partner":
                continue
            records = model.search([(metadata.name, "in", source.id)], order="id")
            if records:
                raise ValidationError(
                    _(
                        "Merge blocked by non-approved direct Many2many "
                        "%(model)s.%(field)s on records %(ids)s."
                    )
                    % {
                        "model": metadata.model,
                        "field": metadata.name,
                        "ids": records.ids,
                    }
                )
        category_rows = {
            "source": [[source.id, category_id] for category_id in sorted(source.category_id.ids)],
            "master": [[master.id, category_id] for category_id in sorted(master.category_id.ids)],
        }
        inventory.append(
            {
                "model": "res.partner.category",
                "field": "category_id",
                "action": "union",
                "ids": sorted(source.category_id.ids),
                "target_ids": sorted(master.category_id.ids),
                "relation_rows": category_rows,
            }
        )

    def _inventory_unknown_references(self, source, inventory):
        metadata_records = self.env["ir.model.fields"].sudo().search(
            [("ttype", "=", "reference")], order="model, name"
        )
        needle = "res.partner,%s" % source.id
        for metadata in metadata_records:
            if metadata.model not in self.env:
                continue
            model = self.env[metadata.model].sudo().with_context(active_test=False)
            if not self._can_search_persistent_rows(model):
                continue
            field = model._fields.get(metadata.name)
            if not field or not field.store or getattr(model, "_transient", False):
                continue
            records = model.search([(metadata.name, "=", needle)], order="id")
            if records:
                raise ValidationError(
                    _(
                        "Merge blocked by unknown reference %(model)s.%(field)s "
                        "on records %(ids)s."
                    )
                    % {
                        "model": metadata.model,
                        "field": metadata.name,
                        "ids": records.ids,
                    }
                )

    def _inventory_unknown_polymorphic(self, source, inventory):
        for model_name in sorted(self.env.registry.models):
            if model_name in POLYMORPHIC_ALLOWLIST or model_name == "ir.model.data":
                continue
            model = self.env[model_name].sudo().with_context(active_test=False)
            if (
                not self._can_search_persistent_rows(model)
                or getattr(model, "_transient", False)
                or "res_id" not in model._fields
            ):
                continue
            discriminator = "res_model" if "res_model" in model._fields else (
                "model" if "model" in model._fields else False
            )
            if not discriminator:
                continue
            if model._fields["res_id"].type != "integer":
                continue
            if not model._fields["res_id"].store or not model._fields[discriminator].store:
                continue
            records = model.search(
                [(discriminator, "=", "res.partner"), ("res_id", "=", source.id)],
                order="id",
            )
            if records:
                raise ValidationError(
                    _("Merge blocked by unknown polymorphic records in %(model)s: %(ids)s.")
                    % {"model": model_name, "ids": records.ids}
                )

    def _inventory_direct_resources(self, source, inventory):
        for model_name in POLYMORPHIC_ALLOWLIST:
            if model_name not in self.env:
                continue
            model = self.env[model_name].sudo().with_context(active_test=False)
            discriminator = "res_model" if "res_model" in model._fields else "model"
            records = model.search(
                [(discriminator, "=", "res.partner"), ("res_id", "=", source.id)],
                order="id",
            )
            if records:
                inventory.append(
                    {
                        "model": model_name,
                        "field": "res_id",
                        "action": "union" if model_name == "mail.followers" else "transfer",
                        "ids": records.ids,
                    }
                )
        model_data = self.env["ir.model.data"].sudo().search(
            [("model", "=", "res.partner"), ("res_id", "=", source.id)], order="id"
        )
        if model_data:
            inventory.append(
                {
                    "model": "ir.model.data",
                    "field": "res_id",
                    "action": "conserve",
                    "ids": model_data.ids,
                }
            )

    def _inventory_follower_state(self, master, source, inventory):
        Followers = self.env["mail.followers"].sudo().with_context(active_test=False)
        source_rows = Followers.search(
            [
                "|",
                ("partner_id", "=", source.id),
                "&",
                ("res_model", "=", "res.partner"),
                ("res_id", "=", source.id),
            ],
            order="id",
        )
        target_ids = set()
        subtype_state = {}
        for follower in source_rows:
            target_partner = master.id if follower.partner_id == source else follower.partner_id.id
            target_res_id = (
                master.id
                if follower.res_model == "res.partner" and follower.res_id == source.id
                else follower.res_id
            )
            target = Followers.search(
                [
                    ("res_model", "=", follower.res_model),
                    ("res_id", "=", target_res_id),
                    ("partner_id", "=", target_partner),
                    ("id", "!=", follower.id),
                ],
                limit=1,
            )
            target_ids.update(target.ids)
            subtype_state[str(follower.id)] = sorted(follower.subtype_ids.ids)
            if target:
                subtype_state[str(target.id)] = sorted(target.subtype_ids.ids)
        inventory.append(
            {
                "model": "mail.followers",
                "field": "semantic_union",
                "action": "union",
                "ids": source_rows.ids,
                "target_ids": sorted(target_ids),
                "subtype_ids": subtype_state,
            }
        )

    def _validate_business_collisions(self, master, source, inventory):
        for model_name, policy in BUSINESS_COLLISION_POLICIES.items():
            if model_name not in self.env:
                continue
            model = self.env[model_name].sudo().with_context(active_test=False)
            partner_field = policy["partner_field"]
            if partner_field not in model._fields:
                continue
            source_rows = model.search([(partner_field, "=", source.id)], order="id")
            if not source_rows:
                continue
            target_rows = model.search([(partner_field, "=", master.id)], order="id")
            state = []
            for record in source_rows | target_rows:
                state.append(
                    {
                        "id": record.id,
                        "side": "source" if record in source_rows else "master",
                        "keys": {
                            ",".join(key_fields): [
                                self._canonical_value(record[field_name])
                                for field_name in key_fields
                                if field_name in model._fields
                            ]
                            for key_fields in policy["keys"]
                        },
                    }
                )
            inventory.append(
                {
                    "model": model_name,
                    "field": "business_policy",
                    "action": "validate",
                    "ids": source_rows.ids,
                    "target_ids": target_rows.ids,
                    "policy_state": state,
                }
            )
            for record in source_rows:
                for key_fields in policy["keys"]:
                    if any(field_name not in model._fields for field_name in key_fields):
                        continue
                    values = [record[field_name] for field_name in key_fields]
                    if not all(values):
                        continue
                    domain = [(partner_field, "=", master.id)]
                    domain.extend(
                        (field_name, "=", self._write_value(value))
                        for field_name, value in zip(key_fields, values)
                    )
                    collision = model.search(domain, limit=1)
                    if collision:
                        raise ValidationError(
                            _(
                                "Merge blocked by %(model)s business key %(fields)s "
                                "between source record %(source)s and master record %(master)s."
                            )
                            % {
                                "model": model_name,
                                "fields": ", ".join(key_fields),
                                "source": record.id,
                                "master": collision.id,
                            }
                        )
        if "slide.channel.partner" in self.env:
            memberships = self.env["slide.channel.partner"].sudo().with_context(
                active_test=False
            )
            source_rows = memberships.search([("partner_id", "=", source.id)])
            channel_field = "channel_id" if "channel_id" in memberships._fields else False
            if source_rows and channel_field:
                duplicate = memberships.search_count(
                    [
                        ("partner_id", "=", master.id),
                        (channel_field, "in", source_rows.mapped(channel_field).ids),
                    ]
                )
                if duplicate:
                    raise ValidationError(
                        _("Merge blocked by duplicate educational channel membership.")
                    )
        if "stripe.subscription" in self.env:
            subscriptions = self.env["stripe.subscription"].sudo().with_context(
                active_test=False
            )
            if "partner_id" in subscriptions._fields:
                if subscriptions.search_count([("partner_id", "=", master.id)]) and subscriptions.search_count(
                    [("partner_id", "=", source.id)]
                ):
                    raise ValidationError(
                        _("Merge blocked because both contacts have Stripe subscriptions.")
                    )

    def _validate_unique_collisions(self, master, inventory):
        """Preflight unique indexes affected by each authorized FK rewrite."""
        for item in inventory:
            if item["action"] != "transfer" or item["field"] == "res_id":
                continue
            model = self.env[item["model"]].sudo().with_context(active_test=False)
            field = model._fields.get(item["field"])
            if not field or not field.store:
                continue
            self.env.cr.execute(
                """
                SELECT array_agg(attribute.attname ORDER BY key_position.ordinality)
                  FROM pg_index index_definition
                  JOIN LATERAL unnest(index_definition.indkey)
                       WITH ORDINALITY AS key_position(attnum, ordinality) ON TRUE
                  JOIN pg_attribute attribute
                    ON attribute.attrelid = index_definition.indrelid
                   AND attribute.attnum = key_position.attnum
                 WHERE index_definition.indrelid = %s::regclass
                   AND index_definition.indisunique
                 GROUP BY index_definition.indexrelid
                """,
                [model._table],
            )
            for columns, in self.env.cr.fetchall():
                if item["field"] not in columns:
                    continue
                field_names = []
                for column in columns:
                    matching = next(
                        (
                            name
                            for name, candidate in model._fields.items()
                            if candidate.store and name == column
                        ),
                        False,
                    )
                    if not matching:
                        field_names = []
                        break
                    field_names.append(matching)
                if not field_names:
                    continue
                for record in model.browse(item["ids"]).exists():
                    domain = [(item["field"], "=", master.id), ("id", "!=", record.id)]
                    nullable = False
                    for field_name in field_names:
                        if field_name == item["field"]:
                            continue
                        value = record[field_name]
                        if not value:
                            nullable = True
                            break
                        domain.append((field_name, "=", self._write_value(value)))
                    if not nullable and model.search_count(domain):
                        raise ValidationError(
                            _(
                                "Merge blocked by a unique business collision in "
                                "%(model)s on %(fields)s."
                            )
                            % {"model": item["model"], "fields": ", ".join(field_names)}
                        )

    def _scalar_snapshot(self, master, source):
        return {
            field_name: {
                "master": self._canonical_value(master[field_name]),
                "source": self._canonical_value(source[field_name]),
            }
            for field_name in self._writable_scalar_fields(master)
        }

    def _scalar_conflicts(self, master, source):
        conflicts = []
        for field_name in self._writable_scalar_fields(master):
            master_value = master[field_name]
            source_value = source[field_name]
            if self._canonical_value(master_value) == self._canonical_value(source_value):
                continue
            requires_choice = bool(master_value and source_value)
            choice = False if requires_choice else (
                "master" if master_value or not source_value else "source"
            )
            conflicts.append(
                {
                    "field_name": field_name,
                    "master_value": self._display_value(master, field_name),
                    "source_value": self._display_value(source, field_name),
                    "requires_choice": requires_choice,
                    "choice": choice,
                }
            )
        return conflicts

    @api.model
    def _writable_scalar_fields(self, partner):
        result = []
        for field_name in SCALAR_ALLOWLIST:
            field = partner._fields.get(field_name)
            if not field or field.compute or field.related or field.company_dependent:
                continue
            if field.type in ("binary", "one2many", "many2many"):
                continue
            result.append(field_name)
        return result

    def _replace_conflicts(self, conflicts):
        self.conflict_ids.with_context(_irg_safe_merge_line_service=True).sudo().unlink()
        Line = self.env["irg.partner.safe.merge.wizard.conflict"].with_context(
            _irg_safe_merge_line_service=True
        ).sudo()
        for values in conflicts:
            Line.create(dict(values, wizard_id=self.id))

    def _conflict_metadata(self):
        return sorted(
            (
                line.field_name,
                line.master_value or "",
                line.source_value or "",
                bool(line.requires_choice),
            )
            for line in self.conflict_ids
        )

    @api.model
    def _expected_conflict_metadata(self, conflicts):
        return sorted(
            (
                item["field_name"],
                item["master_value"] or "",
                item["source_value"] or "",
                bool(item["requires_choice"]),
            )
            for item in conflicts
        )

    def _decision_snapshot(self):
        return {
            line.field_name: line.choice or None
            for line in self.conflict_ids.sorted("field_name")
        }

    def _validate_conflict_lines(self):
        allowed = set(self._writable_scalar_fields(self.master_partner_id))
        if any(line.field_name not in allowed for line in self.conflict_ids):
            raise ValidationError(_("The scalar choice list was manipulated."))
        expected = {
            item["field_name"]
            for item in self._scalar_conflicts(
                self.master_partner_id, self.source_partner_id
            )
        }
        if set(self.conflict_ids.mapped("field_name")) != expected:
            raise ValidationError(_("The scalar choice list is stale or incomplete."))
        if any(line.requires_choice and not line.choice for line in self.conflict_ids):
            raise ValidationError(_("Choose master or source for every scalar conflict."))

    def _hash_payload(self, payload):
        stable = {
            "master_id": payload["master_id"],
            "source_id": payload["source_id"],
            "scalars": payload["scalars"],
            "inventory": payload["inventory"],
            "decisions": payload["decisions"],
            "student_user_links": payload["student_user_links"],
        }
        return hashlib.sha256(self._json(stable).encode("utf-8")).hexdigest()

    def _ordered_partner_ids(self):
        self.ensure_one()
        return sorted((self.master_partner_id.id, self.source_partner_id.id))

    def _lock_partners(self):
        ids = self._ordered_partner_ids()
        self.env.flush_all()
        self.env.cr.execute(
            "SELECT id FROM res_partner WHERE id IN %s ORDER BY id FOR UPDATE",
            [tuple(ids)],
        )
        self.master_partner_id.invalidate_recordset()
        self.source_partner_id.invalidate_recordset()

    def _lock_generated_plan(self):
        self.env.flush_all()
        self.env.cr.execute(
            "SELECT id FROM irg_partner_safe_merge_wizard "
            "WHERE id = %s FOR UPDATE",
            [self.id],
        )
        conflict_ids = sorted(self.conflict_ids.ids)
        if conflict_ids:
            self.env.cr.execute(
                "SELECT id FROM irg_partner_safe_merge_wizard_conflict "
                "WHERE id IN %s ORDER BY id FOR UPDATE",
                [tuple(conflict_ids)],
            )
        self.invalidate_recordset()
        self.conflict_ids.invalidate_recordset()

    def _lock_approved_m2m(self):
        self.env.cr.execute(
            "SELECT partner_id, category_id "
            "FROM res_partner_res_partner_category_rel "
            "WHERE partner_id IN %s "
            "ORDER BY partner_id, category_id FOR UPDATE",
            [tuple(self._ordered_partner_ids())],
        )

    def _lock_inventory(self, inventory):
        grouped = {}
        for item in inventory:
            if item["model"] == "ir.model.data" and item["action"] == "conserve":
                continue
            grouped.setdefault(item["model"], set()).update(item["ids"])
            grouped[item["model"]].update(item.get("target_ids", []))
        for model_name in sorted(grouped):
            if model_name not in self.env or not grouped[model_name]:
                continue
            table = self.env[model_name]._table
            query = sql.SQL("SELECT id FROM {} WHERE id IN %s ORDER BY id FOR UPDATE").format(
                sql.Identifier(table)
            )
            self.env.cr.execute(query, [tuple(sorted(grouped[model_name]))])
            self.env[model_name].browse(grouped[model_name]).invalidate_recordset()

    def _execute_merge(self, payload):
        master = self.master_partner_id.sudo()
        source = self.source_partner_id.sudo()
        before_snapshot = {
            "master": self._partner_snapshot(master),
            "source": self._partner_snapshot(source),
        }
        actions = {}
        decisions = payload["decisions"]
        scalar_values = {}
        for field_name, choice in decisions.items():
            if choice == "source":
                scalar_values[field_name] = self._write_value(source[field_name])
        if scalar_values:
            master.write(scalar_values)
        actions["scalar_fields"] = sorted(scalar_values)
        self._inject_failure("scalars")

        users = self.env["res.users"].sudo().with_context(active_test=False).search(
            [("partner_id", "=", source.id)], order="id"
        )
        if users:
            users.write({"partner_id": master.id})
        actions["res.users.partner_id"] = users.ids
        self._inject_failure("user")

        students = self.env["op.student"].sudo().with_context(active_test=False).search(
            [("partner_id", "=", source.id)], order="id"
        )
        if students:
            students.write({"partner_id": master.id})
        actions["op.student.partner_id"] = students.ids
        self._inject_failure("student")

        transferred = self._transfer_relations(payload["inventory"])
        actions.update(transferred)
        self.env.flush_all()
        self._inject_failure("relations")

        if source.category_id:
            master.write(
                {"category_id": [(4, category_id) for category_id in source.category_id.ids]}
            )
        actions["res.partner.category_id"] = source.category_id.ids
        self._inject_failure("m2m")

        follower_actions = self._transfer_direct_resources(source, master)
        actions.update(follower_actions)
        self._inject_failure("chatter")

        source.with_context(_irg_safe_merge_service=True).sudo().write(
            {"active": False, "irg_merged_into_partner_id": master.id}
        )
        actions["archived_source"] = source.id
        self._inject_failure("archive")

        self.env.flush_all()
        after_snapshot = {
            "master": self._partner_snapshot(master),
            "source": self._partner_snapshot(source.with_context(active_test=False)),
        }

        audit = self.env["irg.partner.safe.merge.audit"].with_context(
            _irg_safe_merge_service=True
        ).sudo().create(
            {
                "master_partner_id": master.id,
                "origin_partner_id": source.id,
                "actor_id": self.env.user.id,
                "preview_hash": self.preview_hash,
                "recommendation_reason": self.recommendation_reason,
                "decisions_json": self._json(decisions),
                "inventory_json": self._json(payload["inventory"]),
                "actions_json": self._json(actions),
                "before_snapshot_json": self._json(before_snapshot),
                "after_snapshot_json": self._json(after_snapshot),
            }
        )
        return audit

    def _transfer_relations(self, inventory):
        actions = {}
        skip = {
            ("res.users", "partner_id"),
            ("op.student", "partner_id"),
            ("mail.followers", "partner_id"),
        }
        for item in inventory:
            key = (item["model"], item["field"])
            if item["action"] != "transfer" or key in skip or item["field"] == "res_id":
                continue
            model = self.env[item["model"]].sudo().with_context(active_test=False)
            records = model.browse(item["ids"]).exists()
            if records:
                records.write({item["field"]: self.master_partner_id.id})
            actions["%s.%s" % key] = records.ids
        return actions

    def _transfer_direct_resources(self, source, master):
        actions = {}
        for model_name in ("mail.message", "mail.activity", "ir.attachment"):
            if model_name not in self.env:
                continue
            model = self.env[model_name].sudo().with_context(active_test=False)
            discriminator = "res_model" if "res_model" in model._fields else "model"
            records = model.search(
                [(discriminator, "=", "res.partner"), ("res_id", "=", source.id)],
                order="id",
            )
            if records:
                records.write({"res_id": master.id})
            actions["%s.res_id" % model_name] = records.ids
        actions.update(self._merge_followers(source, master))
        return actions

    def _merge_followers(self, source, master):
        Followers = self.env["mail.followers"].sudo().with_context(active_test=False)
        followers = Followers.search(
            [
                "|",
                ("partner_id", "=", source.id),
                "&",
                ("res_model", "=", "res.partner"),
                ("res_id", "=", source.id),
            ],
            order="id",
        )
        moved = []
        united = []
        for follower in followers:
            target_partner = master.id if follower.partner_id == source else follower.partner_id.id
            target_res_id = (
                master.id
                if follower.res_model == "res.partner" and follower.res_id == source.id
                else follower.res_id
            )
            collision = Followers.search(
                [
                    ("res_model", "=", follower.res_model),
                    ("res_id", "=", target_res_id),
                    ("partner_id", "=", target_partner),
                    ("id", "!=", follower.id),
                ],
                limit=1,
            )
            if collision:
                if follower.subtype_ids:
                    collision.write(
                        {
                            "subtype_ids": [
                                (4, subtype_id) for subtype_id in follower.subtype_ids.ids
                            ]
                        }
                    )
                united.append({"kept": collision.id, "removed": follower.id})
                follower.unlink()
            else:
                follower.write({"partner_id": target_partner, "res_id": target_res_id})
                moved.append(follower.id)
        return {"mail.followers.moved": moved, "mail.followers.united": united}

    def _inject_failure(self, phase):
        if self.env.context.get("irg_safe_merge_fail_after_phase") == phase:
            raise UserError(_("Injected safe-merge failure after phase: %s") % phase)

    @api.model
    def _canonical_value(self, value):
        if isinstance(value, models.BaseModel):
            return value.ids
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value if value is not False else None

    def _partner_snapshot(self, partner):
        users = self.env["res.users"].sudo().with_context(active_test=False).search(
            [("partner_id", "=", partner.id)], order="id"
        )
        students = self.env["op.student"].sudo().with_context(active_test=False).search(
            [("partner_id", "=", partner.id)], order="id"
        )
        return {
            "id": partner.id,
            "display_name": partner.display_name,
            "active": bool(partner.active),
            "merged_into_id": partner.irg_merged_into_partner_id.id or None,
            "scalars": {
                field_name: self._canonical_value(partner[field_name])
                for field_name in self._writable_scalar_fields(partner)
            },
            "category_ids": sorted(partner.category_id.ids),
            "user_ids": users.ids,
            "student_ids": students.ids,
            "student_user_links": {
                str(student.id): student.user_id.id or None for student in students
            },
        }

    @api.model
    def _write_value(self, value):
        if isinstance(value, models.BaseModel):
            return value.id
        return value

    @api.model
    def _display_value(self, record, field_name):
        value = record[field_name]
        if isinstance(value, models.BaseModel):
            return value.display_name if value else ""
        return str(value or "")

    @api.model
    def _json(self, value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _reopen_action(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Safe merge"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.model
    def _audit_action(self, audit):
        return {
            "type": "ir.actions.act_window",
            "name": _("Safe merge audit"),
            "res_model": "irg.partner.safe.merge.audit",
            "res_id": audit.id,
            "view_mode": "form",
            "target": "current",
        }


class IrgPartnerSafeMergeWizardConflict(models.TransientModel):
    _name = "irg.partner.safe.merge.wizard.conflict"
    _description = "Partner Safe Merge Scalar Choice"
    _order = "field_name, id"

    wizard_id = fields.Many2one(
        "irg.partner.safe.merge.wizard", required=True, ondelete="cascade"
    )
    field_name = fields.Char(required=True, readonly=True)
    master_value = fields.Char(readonly=True)
    source_value = fields.Char(readonly=True)
    requires_choice = fields.Boolean(readonly=True)
    choice = fields.Selection(
        [("master", "Keep master"), ("source", "Use source")], required=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su or not self.env.context.get(
            "_irg_safe_merge_line_service"
        ):
            raise AccessError(_("Scalar choices can only be generated by safe merge."))
        return super().create(vals_list)

    def write(self, vals):
        protected = {"wizard_id", "field_name", "master_value", "source_value", "requires_choice"}
        internal = self.env.su and self.env.context.get(
            "_irg_safe_merge_line_service"
        )
        if protected.intersection(vals) and not internal:
            raise ValidationError(_("Generated scalar choice metadata is immutable."))
        return super().write(vals)

    def unlink(self):
        if not self.env.su or not self.env.context.get(
            "_irg_safe_merge_line_service"
        ):
            raise AccessError(_("Scalar choices can only be removed by safe merge."))
        return super().unlink()
