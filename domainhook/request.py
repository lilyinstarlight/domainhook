import logging
import time

import fooster.db

from domainhook import config


log = logging.getLogger('domainhook.request')

db = fooster.db.Database(config.dir + '/requests.db', ['id', 'expire'])


def prune():
    now = time.time()

    todo = []

    for entry in db:
        if entry.expire <= now:
            todo.append(entry.id)

    if todo:
        log.info('Found request entries to prune')

        for request_id in todo:
            del db[request_id]


def add(request_id, expire=None):
    if not expire:
        expire = time.time() + config.expire

    db[request_id] = db.Entry(expire=expire)


def exists(request_id):
    prune()

    return request_id in db
