# -*- coding: utf-8 -*-
import base64
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

from .listado_parser import parse_listado_xlsx
from .xlsx_export import build_xlsx, methodology_rows, xlsxwriter

TYPE_LABEL = {
    "article": "Artículo / contenido",
    "video": "Vídeo",
    "certification": "Evaluación / asignación",
    "document": "Documento",
    "infographic": "Infografía",
    "quiz": "Cuestionario",
}


def _yesno(value):
    return _("Sí") if value else _("No")


class IrgCampusActivityAuditWizard(models.TransientModel):
    _name = "irg.campus.activity.audit.wizard"
    _description = "Informe de actividad de campus"

    batch_id = fields.Many2one("op.batch", string="Lote", required=True)
    listado_file = fields.Binary(string="Listado de alumnos (opcional)")
    listado_filename = fields.Char(string="Nombre del listado")
    file_data = fields.Binary(string="Informe", readonly=True)
    filename = fields.Char(string="Nombre del archivo", readonly=True)
    state = fields.Selection(
        [("choose", "Elegir"), ("done", "Hecho")],
        default="choose",
        string="Estado",
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        active_id = self.env.context.get("active_id")
        if (
            active_id
            and self.env.context.get("active_model") == "op.batch"
            and "batch_id" in fields_list
            and not values.get("batch_id")
        ):
            values["batch_id"] = active_id
        return values

    def _assert_can_export(self):
        self.ensure_one()
        if self.env.su:
            return
        if not self.env.user.has_group("openeducat_core.group_op_faculty"):
            raise AccessError(
                _("Solo el personal interno de Facultad puede generar el informe de actividad.")
            )
        if not self.batch_id:
            raise UserError(_("No se ha seleccionado ningún lote."))
        if xlsxwriter is None:
            raise UserError(_("La librería xlsxwriter no está instalada."))

    def action_generate(self):
        self.ensure_one()
        self._assert_can_export()
        data_wizard = self.sudo()
        enrollments = data_wizard._enrollments()
        listado = data_wizard._listado_rows()
        matched, unmatched = data_wizard._match_enrollments(enrollments, listado)
        if not matched and not unmatched:
            raise UserError(_("No hay estudiantes en este lote."))
        sheets = data_wizard._build_sheets(matched, unmatched, bool(listado))
        payload = build_xlsx(sheets)
        filename = "informe_actividad_%s_%s.xlsx" % (
            self.batch_id.code or self.batch_id.name or "lote",
            fields.Date.today().strftime("%Y%m%d"),
        )
        self.write(
            {
                "file_data": base64.b64encode(payload),
                "filename": filename,
                "state": "done",
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
            "context": self.env.context,
        }

    def _enrollments(self):
        self.ensure_one()
        return self.env["op.student.course"].search(
            [("batch_id", "=", self.batch_id.id)]
        )

    def _listado_rows(self):
        self.ensure_one()
        if not self.listado_file:
            return []
        return parse_listado_xlsx(base64.b64decode(self.listado_file))

    def _match_enrollments(self, enrollments, listado):
        if not listado:
            return enrollments, []
        by_email = defaultdict(list)
        for enrollment in enrollments:
            for email in self._enrollment_emails(enrollment):
                by_email[email].append(enrollment)
        matched_ids = self.env["op.student.course"]
        unmatched = []
        seen = set()
        for item in listado:
            hits = by_email.get(item["email_norm"]) or []
            if item.get("course_code"):
                code = item["course_code"].lower()
                hits = [
                    enrollment
                    for enrollment in hits
                    if (enrollment.course_id.code or "").lower() == code
                ]
            if not hits:
                unmatched.append(item)
                continue
            for enrollment in hits:
                if enrollment.id not in seen:
                    matched_ids |= enrollment
                    seen.add(enrollment.id)
        return matched_ids, unmatched

    def _enrollment_emails(self, enrollment):
        emails = set()
        partner = enrollment.student_id.partner_id
        for raw in (
            partner.email,
            enrollment.student_id.email,
            enrollment.student_id.user_id.login,
        ):
            if raw:
                emails.add(raw.strip().lower())
        return emails

    def _completion_flags(self, enrollment):
        catalog_done, catalog_total, campus_done = self._campus_catalog(enrollment)
        completion = float(enrollment.completion_porc or 0.0)
        return {
            "matricula_estado": enrollment.state,
            "matricula_finalizada": enrollment.state == "finished",
            "completion_porc": round(completion, 2),
            "libreta_100": completion >= 100.0,
            "campus_completado": campus_done,
            "actividades_completadas": catalog_done,
            "actividades_publicadas": catalog_total,
            "progreso_catalogo": (
                round(100.0 * catalog_done / catalog_total, 1) if catalog_total else ""
            ),
        }

    def _campus_memberships(self, enrollment):
        partner = enrollment.student_id.partner_id
        domain = [
            ("partner_id", "=", partner.id),
            ("batch_id", "=", enrollment.batch_id.id),
        ]
        PartnerChannel = self.env["slide.channel.partner"]
        if "active" in PartnerChannel._fields:
            domain.append(("active", "=", True))
        return PartnerChannel.search(domain)

    def _published_slides(self, channel):
        Slide = self.env["slide.slide"]
        domain = [("channel_id", "=", channel.id)]
        if "active" in Slide._fields:
            domain.append(("active", "=", True))
        if "is_category" in Slide._fields:
            domain.append(("is_category", "=", False))
        if "is_published" in Slide._fields:
            domain.append(("is_published", "=", True))
        return Slide.search(domain, order="sequence, id")

    def _campus_catalog(self, enrollment):
        done = 0
        total = 0
        memberships = self._campus_memberships(enrollment)
        partner = enrollment.student_id.partner_id
        SlidePartner = self.env["slide.slide.partner"]
        for membership in memberships:
            slides = self._published_slides(membership.channel_id)
            total += len(slides)
            if not slides:
                continue
            partners = SlidePartner.search(
                [
                    ("partner_id", "=", partner.id),
                    ("slide_id", "in", slides.ids),
                    ("completed", "=", True),
                ]
            )
            done += len(set(partners.mapped("slide_id").ids))
        campus_done = bool(total) and done == total
        return done, total, campus_done

    def _build_sheets(self, enrollments, unmatched, has_listado):
        summary_headers = [
            "email",
            "nombre",
            "id_estudiante",
            "id_partner",
            "lote",
            "curso",
            "codigo_curso",
            "matricula_estado",
            "matricula_finalizada",
            "completion_porc",
            "libreta_100",
            "canales_inscritos",
            "canales_completados",
            "campus_completado",
            "actividades_completadas",
            "actividades_publicadas",
            "progreso_catalogo_%",
        ]
        summary_rows = []
        channel_rows = []
        activity_rows = []
        survey_rows = []
        book_rows = []
        subject_rows = []
        result_rows = []
        for enrollment in enrollments:
            flags = self._completion_flags(enrollment)
            partner = enrollment.student_id.partner_id
            email = partner.email or enrollment.student_id.user_id.login or ""
            memberships = self._campus_memberships(enrollment)
            channels_done = sum(
                1
                for membership in memberships
                if getattr(membership, "completed", False)
            )
            summary_rows.append(
                [
                    email,
                    enrollment.student_id.name,
                    enrollment.student_id.id,
                    partner.id,
                    enrollment.batch_id.code,
                    enrollment.course_id.name,
                    enrollment.course_id.code,
                    flags["matricula_estado"],
                    _yesno(flags["matricula_finalizada"]),
                    flags["completion_porc"],
                    _yesno(flags["libreta_100"]),
                    len(memberships),
                    channels_done,
                    _yesno(flags["campus_completado"]),
                    flags["actividades_completadas"],
                    flags["actividades_publicadas"],
                    flags["progreso_catalogo"],
                ]
            )
            channel_rows.extend(self._channel_sheet_rows(enrollment, memberships))
            activity_rows.extend(self._activity_sheet_rows(enrollment, memberships))
            survey_rows.extend(self._survey_sheet_rows(enrollment, memberships))
            book, subjects, results = self._gradebook_sheet_rows(enrollment)
            book_rows.extend(book)
            subject_rows.extend(subjects)
            result_rows.extend(results)

        unmatched_rows = [
            [
                item.get("email") or "",
                item.get("course_code") or "",
                item.get("excel_row") or "",
                _("Sin matrícula en el lote"),
            ]
            for item in unmatched
        ]
        return {
            "Resumen alumnos": (summary_headers, summary_rows),
            "Progreso por asignatura": (
                [
                    "email",
                    "lote",
                    "codigo_asignatura",
                    "asignatura",
                    "canal_elearning",
                    "progreso_%",
                    "contenidos_completados",
                    "contenidos_totales",
                    "canal_completado",
                ],
                channel_rows,
            ),
            "Actividades": (
                [
                    "email",
                    "nombre",
                    "lote",
                    "canal",
                    "actividad",
                    "tipo",
                    "estado",
                    "completada",
                ],
                activity_rows,
            ),
            "Evaluaciones": (
                [
                    "email",
                    "nombre",
                    "lote",
                    "canal",
                    "actividad",
                    "estado_intento",
                    "puntuacion_%",
                    "aprobada",
                ],
                survey_rows,
            ),
            "Libreta alumnos": (
                [
                    "email",
                    "nombre",
                    "lote",
                    "estado_libreta",
                    "id_libreta",
                    "asignaturas",
                    "resultados_examen",
                ],
                book_rows,
            ),
            "Libreta asignaturas": (
                [
                    "email",
                    "lote",
                    "codigo_asignatura",
                    "asignatura",
                    "nota_final_asignatura",
                    "n_examenes",
                ],
                subject_rows,
            ),
            "Libreta examenes": (
                [
                    "email",
                    "nombre",
                    "lote",
                    "asignatura",
                    "tipo",
                    "nombre_resultado",
                    "nota",
                ],
                result_rows,
            ),
            "No encontrados": (
                ["email", "curso_listado", "fila_excel", "motivo"],
                unmatched_rows,
            ),
            "Metodologia": (
                ["Campo", "Valor"],
                methodology_rows(
                    batch_code=self.batch_id.code or "",
                    has_listado=has_listado,
                )[1:],
            ),
        }

    def _channel_sheet_rows(self, enrollment, memberships):
        partner = enrollment.student_id.partner_id
        rows = []
        for membership in memberships:
            slides = self._published_slides(membership.channel_id)
            done = self.env["slide.slide.partner"].search_count(
                [
                    ("partner_id", "=", partner.id),
                    ("slide_id", "in", slides.ids),
                    ("completed", "=", True),
                ]
            ) if slides else 0
            subject = membership.op_subject_id if "op_subject_id" in membership._fields else False
            rows.append(
                [
                    partner.email or "",
                    enrollment.batch_id.code,
                    subject.code if subject else "",
                    subject.name if subject else "",
                    membership.channel_id.name,
                    getattr(membership, "completion", "") or "",
                    done,
                    len(slides),
                    _yesno(getattr(membership, "completed", False)),
                ]
            )
        return rows

    def _activity_sheet_rows(self, enrollment, memberships):
        partner = enrollment.student_id.partner_id
        rows = []
        SlidePartner = self.env["slide.slide.partner"]
        for membership in memberships:
            for slide in self._published_slides(membership.channel_id):
                slide_partner = SlidePartner.search(
                    [
                        ("slide_id", "=", slide.id),
                        ("partner_id", "=", partner.id),
                    ],
                    limit=1,
                )
                if not slide_partner:
                    status = _("No iniciada")
                    completed = False
                elif slide_partner.completed:
                    status = _("Completada")
                    completed = True
                else:
                    status = _("En curso")
                    completed = False
                category = getattr(slide, "slide_category", "") or ""
                rows.append(
                    [
                        partner.email or "",
                        enrollment.student_id.name,
                        enrollment.batch_id.code,
                        membership.channel_id.name,
                        slide.name,
                        TYPE_LABEL.get(category, category),
                        status,
                        _yesno(completed),
                    ]
                )
        return rows

    def _survey_sheet_rows(self, enrollment, memberships):
        partner = enrollment.student_id.partner_id
        channel_ids = memberships.mapped("channel_id").ids
        if not channel_ids:
            return []
        Input = self.env["survey.user_input"]
        if "slide_id" not in Input._fields:
            return []
        inputs = Input.search(
            [
                ("partner_id", "=", partner.id),
                ("slide_id.channel_id", "in", channel_ids),
            ]
        )
        rows = []
        for attempt in inputs:
            rows.append(
                [
                    partner.email or "",
                    enrollment.student_id.name,
                    enrollment.batch_id.code,
                    attempt.slide_id.channel_id.name if attempt.slide_id else "",
                    attempt.slide_id.name if attempt.slide_id else "",
                    attempt.state,
                    attempt.scoring_percentage,
                    _yesno(bool(attempt.scoring_success)),
                ]
            )
        return rows

    def _gradebook_sheet_rows(self, enrollment):
        partner = enrollment.student_id.partner_id
        StudentBook = self.env["app.gradebook.student"]
        books = StudentBook.search(
            [
                ("partner_id", "=", partner.id),
                ("batch_id", "=", enrollment.batch_id.id),
            ]
        )
        if not books:
            books = StudentBook.search(
                [
                    ("partner_id", "=", partner.id),
                    ("course_id", "=", enrollment.course_id.id),
                ]
            )
        book_rows = []
        subject_rows = []
        result_rows = []
        email = partner.email or ""
        for book in books:
            exams = book.gradebook_subject_ids.mapped("gradebook_result_ids").filtered(
                lambda result: result.survey_type == "exam"
            )
            book_rows.append(
                [
                    email,
                    enrollment.student_id.name,
                    enrollment.batch_id.code,
                    book.state,
                    book.id,
                    len(book.gradebook_subject_ids),
                    len(exams),
                ]
            )
            for subject in book.gradebook_subject_ids:
                op_subject = subject.op_subject_id
                exam_qty = len(
                    subject.gradebook_result_ids.filtered(
                        lambda result: result.survey_type == "exam"
                    )
                )
                subject_rows.append(
                    [
                        email,
                        enrollment.batch_id.code,
                        op_subject.code if op_subject else "",
                        op_subject.name if op_subject else (subject.name or ""),
                        subject.final_subject_note,
                        exam_qty,
                    ]
                )
                for result in subject.gradebook_result_ids:
                    result_rows.append(
                        [
                            email,
                            enrollment.student_id.name,
                            enrollment.batch_id.code,
                            op_subject.name if op_subject else (subject.name or ""),
                            result.survey_type,
                            result.name or result.description or "",
                            result.scoring_total,
                        ]
                    )
        if not books:
            book_rows.append(
                [
                    email,
                    enrollment.student_id.name,
                    enrollment.batch_id.code,
                    _("Sin libreta"),
                    "",
                    "",
                    "",
                ]
            )
        return book_rows, subject_rows, result_rows
