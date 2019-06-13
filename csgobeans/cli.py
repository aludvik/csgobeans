import os

import click
import flask

from . import ctx
from . import db

@click.command('init')
@flask.cli.with_appcontext
def init():
    init_db(flask.current_app)
    click.echo('Initialized the database')

def init_db(app):
    os.makedirs(app.instance_path, exist_ok=True)
    database = db.Database(ctx.database_local_path(app))
    click.echo('Initializing from schema')
    database.initialize_from_schema()
    click.echo('Populating with beans')
    database.populate_beans_from_file()

def init_cli(app):
    app.cli.add_command(init)
