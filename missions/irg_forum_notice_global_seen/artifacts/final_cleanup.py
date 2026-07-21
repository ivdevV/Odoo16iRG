import psycopg2


params = {
    'host': 'pgodoo_local',
    'port': 5432,
    'user': 'odoo',
    'password': 'odoo',
}
connection = psycopg2.connect(
    dbname='test_irg_forum_global_seen', **params
)
cursor = connection.cursor()
checks = (
    ("SELECT count(*) FROM res_users WHERE login LIKE 'evidence-%@example.test'", 3),
    ("SELECT count(*) FROM op_course WHERE code IN ('EVGS-A', 'EVGS-B')", 2),
    ("SELECT count(*) FROM op_batch WHERE code IN ('EVGS-BA', 'EVGS-BB')", 2),
    ("SELECT count(*) FROM forum_post WHERE name LIKE 'Aviso evidence %'", 3),
)
for query, expected in checks:
    cursor.execute(query)
    assert cursor.fetchone()[0] == expected
connection.close()
print('fixtures_identified: 3 users, 2 courses, 2 batches, 3 posts')

admin = psycopg2.connect(dbname='postgres', **params)
admin.autocommit = True
cursor = admin.cursor()
cursor.execute(
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
    "WHERE datname='test_irg_forum_global_seen' "
    "AND pid <> pg_backend_pid()"
)
cursor.execute('DROP DATABASE test_irg_forum_global_seen')
cursor.execute(
    "SELECT count(*) FROM pg_database "
    "WHERE datname='test_irg_forum_global_seen'"
)
assert cursor.fetchone()[0] == 0
admin.close()
print('isolated_database_removed: PASS')
