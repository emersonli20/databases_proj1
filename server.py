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

# [**] Initialize global variables
MY_TRAINER_ID = "1"
MY_LOC_ID = "104"

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

    # [*] show current location

    cursor = g.conn.execute(text(f"""
                                SELECT L.locname 
                                FROM location L
                                WHERE L.LocID = '{MY_LOC_ID}'
                                """))
    g.conn.commit()

    my_location = []
    results = cursor.mappings().all()
    for result in results:
      my_location.append(result["locname"])
    cursor.close()

    # [**] Add buttons to let you move locations
    # [*] get names of other locations
    cursor = g.conn.execute(text(f"""
                                SELECT L.locname 
                                FROM location L
                                WHERE L.LocID != '{MY_LOC_ID}'
                                """))
    g.conn.commit()

    location_names = []
    results = cursor.mappings().all()
    for result in results:
      location_names.append(result["locname"])
    cursor.close()

    context = dict(data = location_names, my_data = my_location)
    
    return render_template("location.html", **context)

@app.route('/trainer')
def trainer():

    # [***] Add battle, buy, and sell buttons
    # [***] filter by current location

    # [*] get trainers
    # [*] exclude yourself
    cursor = g.conn.execute(text(f"""
                                 SELECT T.name, T.money 
                                 FROM trainer_located_in T 
                                 LEFT JOIN gym_leader G ON T.trainid = G.gymid
                                 WHERE G.gymid IS NULL
                                 AND T.trainid != '{MY_TRAINER_ID}'
                                 AND T.locid = '{MY_LOC_ID}'
                                 """))


    # [**] display trainer data in a table
    trainers = []
    results = cursor.mappings().all()
    for result in results:
      trainers.append(result)
    cursor.close()

    # [**] get gym_leaders
    cursor = g.conn.execute(text(f"""
                                SELECT T.name, T.money, G.reward
                                FROM gym_leader G
                                JOIN trainer_located_in T ON T.trainid = G.gymid
                                WHERE T.locid = '{MY_LOC_ID}'
                                """))

    gym_leaders = []
    results = cursor.mappings().all()
    for result in results:
      gym_leaders.append(result)
    cursor.close()


    context = dict(t_data = trainers, gl_data = gym_leaders)
    
    return render_template("trainer.html", **context)

@app.route('/bag')
def bag():

    # [*] get evolution items
    cursor = g.conn.execute(text(f"""
                                 SELECT A.Name, E.Evolves_From, E.Evolves_Into 
                                 FROM Evolution_Item E
                                 JOIN Asset A ON A.Asset_ID = E.ItemID
                                 JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                 WHERE O.TrainID = '{MY_TRAINER_ID}'
                                 AND A.Asset_ID NOT IN 
                                    (
                                    SELECT H.ItemID
                                    FROM Holds H
                                    )
                                 """))
                                 
                                #  LEFT JOIN Item I
                                #     ON E.ItemID = I.ItemID
                                #  WHERE E.ItemID IS NOT NULL"""))
    evolution_items = []
    results = cursor.mappings().all()
    for result in results:
      evolution_items.append(result)
    cursor.close()

    # [**] get battle items
    cursor = g.conn.execute(text(f"""
                                 SELECT A.Name, B.PowerLVL 
                                 FROM Battle_Item B
                                 JOIN Asset A ON A.Asset_ID = B.ItemID
                                 JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                 WHERE O.TrainID = '{MY_TRAINER_ID}'
                                 AND A.Asset_ID NOT IN 
                                    (
                                    SELECT H.ItemID
                                    FROM Holds H
                                    )
                                 """))
    battle_items = []
    results = cursor.mappings().all()
    for result in results:
      battle_items.append(result)
    cursor.close()

    # [**] get other items
    cursor = g.conn.execute(text(f"""
                                SELECT A.Name, A.Cost
                                FROM Item I
                                JOIN Asset A ON A.Asset_ID = I.ItemID
                                LEFT JOIN Evolution_Item E ON I.ItemID = E.ItemID
                                JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                WHERE E.ItemID IS NULL
                                AND O.TrainID = '{MY_TRAINER_ID}'
                                AND A.Asset_ID NOT IN 
                                    (
                                    SELECT H.ItemID
                                    FROM Holds H
                                    )
                                INTERSECT
                                SELECT A.Name, A.Cost
                                FROM Item I
                                JOIN Asset A ON A.Asset_ID = I.ItemID
                                LEFT JOIN Battle_Item B ON I.ItemID = B.ItemID
                                JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                WHERE B.ItemID IS NULL
                                AND O.TrainID = '{MY_TRAINER_ID}'
                                AND A.Asset_ID NOT IN 
                                    (
                                    SELECT H.ItemID
                                    FROM Holds H
                                    )
                                """))
    other_items = []
    results = cursor.mappings().all()
    for result in results:
      other_items.append(result)
    cursor.close()
    
    context = dict(ei_data = evolution_items, bi_data = battle_items, oi_data = other_items)

    # [**] display bag data in a table
    return render_template("bag.html", **context)

@app.route('/pokemon')
def pokemon():

    # [**] get my pokemon
    cursor = g.conn.execute(text(f"""
                                SELECT P.PokeID, A.Name, P.PowerLVL, A.Cost, A2.Name AS "Held Item"
                                FROM Pokemon P
                                INNER JOIN Owns O ON O.Asset_ID = P.PokeID
                                INNER JOIN Asset A ON A.Asset_ID = O.Asset_ID
                                INNER JOIN Holds H ON H.PokeID = P.PokeID
                                INNER JOIN Asset A2 ON A2.Asset_ID = H.ItemID
                                WHERE O.TrainID = '{MY_TRAINER_ID}'
                                """))


    # [**] display pokemon data in a table
    pokemon = []
    results = cursor.mappings().all()
    for result in results:
      pokemon.append(result)
    cursor.close()

    print(pokemon)

    context = dict(data = pokemon)

    return render_template("pokemon.html", **context)

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