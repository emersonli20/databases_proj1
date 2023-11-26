import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, abort

# [*] Create Flask App
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

# [*] Set Database URI
DATABASEURI = "postgresql://sa4116:701271@34.74.171.121/proj1part2"

# [*] Connect to database
engine = create_engine(DATABASEURI)
conn = engine.connect()

# [*] BEFORE_REQUEST
@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

# [*] TEARDOWN_REQUEST
@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

# [**] INDEX
@app.route('/')
def index():
    # [*] - get trainers excluding gym leaders
    cursor = g.conn.execute(text("SELECT T.name FROM trainer_located_in T LEFT JOIN gym_leader G ON T.trainid = G.gymid WHERE G.gymid IS NULL;"))
    g.conn.commit()

    # [***] Add buttons to let you Select Trainer

    trainer_names = []
    results = cursor.mappings().all()
    for result in results:
      trainer_names.append(result["name"])
    cursor.close()

    context = dict(data = trainer_names)
    
    return render_template("index.html", **context)


@app.route('/location')
def location():
    # [***] set default location

    # [***] show current location

    # [*] - get names of locations
    cursor = g.conn.execute(text("SELECT L.locname FROM location L;"))
    g.conn.commit()

    # [**] Add buttons to let you move locations

    location_names = []
    results = cursor.mappings().all()
    for result in results:
      location_names.append(result["locname"])
    cursor.close()

    context = dict(data = location_names)
    
    return render_template("location.html", **context)

@app.route('/trainer')
def trainer():
    # [***] exclude yourself

    # [***] filter by current location

    # [*] - get trainers
    cursor = g.conn.execute(text("SELECT T.trainid, T.name, T.money FROM trainer_located_in T LEFT JOIN gym_leader G ON T.trainid = G.gymid WHERE G.gymid IS NULL;"))

    # [***] Add battle, buy, and sell buttons

    # [**] display trainer data in a table
    trainers = []
    results = cursor.mappings().all()
    for result in results:
      trainers.append(result)
    cursor.close()

    context = dict(data = trainers)

    # [***] get gym_leaders
    
    return render_template("trainer.html", **context)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python3 server.py

    Show the help text using:

        python3 server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()