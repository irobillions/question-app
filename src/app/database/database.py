from flask import g
import psycopg2
from psycopg2.extras import DictCursor


def connect_db():
    conn = psycopg2.connect(
        'postgres://bgbnqaqewclesp:b2395d57ab343efaa44bbc00ac44708f58d1bc0c9d4d6dc6aac488e880d6dfbe@ec2-54-75-246-118.eu-west-1.compute.amazonaws.com:5432/dd48fd2e249r67',
        cursor_factory=DictCursor)
    conn.autocommit = True
    sql = conn.cursor()
    return conn, sql


def get_db():
    db = connect_db()

    if not hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn = db[0]

    if not hasattr(g, 'psotgres_db_cur'):
        g.postgres_db_cur = db[1]

    return g.postgres_db_cur


def init_db():
    db = connect_db()
    db[1].execute(open('schema.sql', 'r').read())
    db[1].close()

    db[0].close()

