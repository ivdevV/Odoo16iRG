import json


group_user = env.ref('base.group_user')
group_system = env.ref('base.group_system')
users = env['res.users'].sudo().with_context(no_reset_password=True)
course_model = env['op.course'].sudo()
batch_model = env['op.batch'].sudo()
forum_model = env['forum.forum'].sudo()
post_model = env['forum.post'].sudo()

course_a = course_model.create({'name': 'Evidence Course A', 'code': 'EVGS-A'})
course_b = course_model.create({'name': 'Evidence Course B', 'code': 'EVGS-B'})
dates = {'start_date': '2026-07-20', 'end_date': '2026-12-31'}
batch_a = batch_model.create({
    'name': 'Evidence Batch A', 'code': 'EVGS-BA',
    'course_id': course_a.id, **dates,
})
batch_b = batch_model.create({
    'name': 'Evidence Batch B', 'code': 'EVGS-BB',
    'course_id': course_b.id, **dates,
})
multicourse = users.create({
    'name': 'Evidence Multicourse',
    'login': 'evidence-multi@example.test',
    'password': 'evidence-validator',
    'groups_id': [(6, 0, group_user.ids)],
    'op_batch_ids': [(6, 0, (batch_a | batch_b).ids)],
})
second = users.create({
    'name': 'Evidence Second',
    'login': 'evidence-second@example.test',
    'password': 'evidence-validator',
    'groups_id': [(6, 0, (group_user | group_system).ids)],
})
courseless = users.create({
    'name': 'Evidence Courseless',
    'login': 'evidence-courseless@example.test',
    'password': 'evidence-validator',
    'groups_id': [(6, 0, (group_user | group_system).ids)],
})
env.invalidate_all()
assert set((course_a | course_b).ids).issubset(
    set(multicourse.forum_effective_course_ids.ids)
)
assert set((batch_a | batch_b).ids).issubset(
    set(multicourse.forum_effective_batch_ids.ids)
)
assert not courseless.forum_effective_course_ids

forum = forum_model.create({
    'name': 'Evidence Forum',
    'visibility_course_ids': [(6, 0, (course_a | course_b).ids)],
})
multi_post = post_model.create({
    'name': 'Aviso evidence multicurso',
    'forum_id': forum.id,
    'content': 'Evidence multicourse',
})
multi_post.active = False
excluded_forum = forum_model.create({'name': 'Evidence Excluded Forum'})
excluded_post = post_model.create({
    'name': 'Aviso evidence excluido',
    'forum_id': excluded_forum.id,
    'content': 'Evidence excluded',
    'excluded_visibility_batch_ids': [(6, 0, batch_a.ids)],
})
excluded_post.active = False
assert not excluded_post._is_visible_for_user(multicourse)
courseless_forum = forum_model.create({'name': 'Evidence Courseless Forum'})
courseless_post = post_model.create({
    'name': 'Aviso evidence sin curso',
    'forum_id': courseless_forum.id,
    'content': 'Evidence courseless',
})
assert courseless_post._is_visible_for_user(courseless)
env.cr.commit()
print(json.dumps({
    'batch_a': batch_a.id,
    'course_a': course_a.id,
    'course_b': course_b.id,
    'courseless': courseless.id,
    'courseless_post': courseless_post.id,
    'excluded_post': excluded_post.id,
    'multi_post': multi_post.id,
    'multicourse': multicourse.id,
    'second': second.id,
}, sort_keys=True))
