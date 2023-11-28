import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, abort, url_for

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
SELECTED_TRAINER_ID = "10"
MY_LOC_ID = "104"
SELECTED_EVOLUTION_ITEM_ID = "300"
SELECTED_GIVE_ITEM_ID = "400"


# [*] ==== BEFORE_REQUEST ====
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


# [*] ==== TEARDOWN_REQUEST ====
@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    # g.conn.execute(text(f"""
    #                     UPDATE Settings
    #                     SET my_trainid = NULL, sel_trainid
    #                     """))
    g.conn.close()
  except Exception as e:
    pass

# [*] ======= INDEX ========
@app.route('/')
def index():

    _, my_train_name, _, my_loc_name = get_current()
    my_money = get_money()

    # [*] - get trainers excluding gym leaders
    cursor = g.conn.execute(text("SELECT T.name FROM trainer_located_in T LEFT JOIN gym_leader G ON T.trainid = G.gymid WHERE G.gymid IS NULL;"))
    g.conn.commit()


    trainer_names = []
    results = cursor.mappings().all()
    for result in results:
      trainer_names.append(result["name"])
    cursor.close()

    context = dict(data = trainer_names, my_train_name = my_train_name, my_loc_name = my_loc_name, my_money = my_money)
    
    return render_template("index.html", **context)

# [*] === BUTTON_CLICKED_SELECT_TRAINER ===
@app.route('/button_clicked_select_trainer/', methods=['POST'])
def button_clicked_select_trainer():
    row_data = request.form.get('row_data')
    # [*] get trainid using trainer name
    cursor = g.conn.execute(text(f"""
                                SELECT T.trainid
                                FROM Trainer_Located_In T
                                WHERE T.name = '{row_data}'
                                ORDER BY T.trainid
                                LIMIT 1
                                """))
    g.conn.commit()

    trainids = []
    results = cursor.mappings().all()
    for result in results:
      trainids.append(result["trainid"])
    cursor.close()
    trainid = trainids[0]

    # [*] update settings table
    g.conn.execute(text(f"""
                        UPDATE Settings
                        SET my_trainid = '{trainid}';
                        """))
    g.conn.commit()
    
    print(f"Button clicked for row: {row_data}")
    return redirect(url_for('location'))

# [*] ====== LOCATION ========
@app.route('/location')
def location():
    my_trainid, my_train_name, my_locid, my_loc_name = get_current()
    my_money = get_money()

    # [*] show current location

    cursor = g.conn.execute(text(f"""
                                SELECT L.locname 
                                FROM location L
                                WHERE L.LocID = '{my_locid}'
                                """))
    g.conn.commit()

    my_location = []
    results = cursor.mappings().all()
    for result in results:
      my_location.append(result["locname"])
    cursor.close()

    # [*] Add buttons to let you move locations
    # [*] get names of other locations
    cursor = g.conn.execute(text(f"""
                                SELECT L.locname 
                                FROM location L
                                WHERE L.LocID != '{my_locid}'
                                """))
    g.conn.commit()

    location_names = []
    results = cursor.mappings().all()
    for result in results:
      location_names.append(result["locname"])
    cursor.close()

    

    context = dict(data = location_names, my_data = my_location, my_train_name = my_train_name, my_loc_name = my_loc_name, my_money = my_money)

    return render_template("location.html", **context)

# [*] === BUTTON_CLICKED_CHANGE_LOCATION === 
@app.route('/button_clicked_change_location/', methods=['POST'])
def button_clicked_change_location():
    row_data = request.form.get('row_data')
    # [*] get locid using location name
    cursor = g.conn.execute(text(f"""
                                SELECT L.locid
                                FROM Location L
                                WHERE L.locname = '{row_data}'
                                ORDER BY L.locid
                                LIMIT 1
                                """))
    g.conn.commit()

    locids = []
    results = cursor.mappings().all()
    for result in results:
      locids.append(result["locid"])
    cursor.close()
    locid = locids[0]

    # [*] update settings table
    g.conn.execute(text(f"""
                        UPDATE Settings
                        SET my_locid = '{locid}';
                        """))
    g.conn.commit()
    
    print(f"Button clicked for row: {row_data}")
    return redirect(url_for('location'))

# [**] ======= TRAINER =======
@app.route('/trainer/')
def trainer():

    # [*] Add battle, buy, and sell buttons
    my_trainid, my_train_name, my_locid, my_loc_name = get_current()
    my_money = get_money()

    # [*] get trainers
    # [*] exclude yourself
    # [*] filter by current location
    cursor = g.conn.execute(text(f"""
                                 SELECT T.name, T.money 
                                 FROM trainer_located_in T 
                                 LEFT JOIN gym_leader G ON T.trainid = G.gymid
                                 WHERE G.gymid IS NULL
                                 AND T.trainid != '{my_trainid}'
                                 AND T.locid = '{my_locid}'
                                 """))


    # [*] display trainer data in a table
    trainers = []
    results = cursor.mappings().all()
    for result in results:
      trainers.append(result)
    cursor.close()

    # [*] get gym_leaders
    cursor = g.conn.execute(text(f"""
                                SELECT T.name, T.money, G.reward
                                FROM gym_leader G
                                JOIN trainer_located_in T ON T.trainid = G.gymid
                                WHERE T.locid = '{my_locid}'
                                """))

    gym_leaders = []
    results = cursor.mappings().all()
    for result in results:
      gym_leaders.append(result)
    cursor.close()


    context = dict(t_data = trainers, gl_data = gym_leaders, my_train_name = my_train_name, my_loc_name = my_loc_name, my_money = my_money)
    
    return render_template("trainer.html", **context)

# [**] BUTTON_CLICKED_BATTLE_TRAINER
@app.route('/button_clicked_battle_trainer/', methods=['POST'])
def button_clicked_battle_trainer():
    row_data = request.form.get('row_data')
    
    print(f"Button clicked for row: {row_data}")
    return redirect(url_for('trainer'))

# [*] BUTTON_CLICKED_BUY_TRAINER
@app.route('/button_clicked_buy_trainer/', methods=['POST'])
def button_clicked_buy_trainer():
    row_data = request.form.get('row_data')
    
    # [*] get trainid using trainer name
    cursor = g.conn.execute(text(f"""
                                SELECT T.trainid
                                FROM Trainer_Located_In T
                                WHERE T.name = '{row_data}'
                                ORDER BY T.trainid
                                LIMIT 1
                                """))
    g.conn.commit()

    trainids = []
    results = cursor.mappings().all()
    for result in results:
      trainids.append(result["trainid"])
    cursor.close()
    trainid = trainids[0]

    # [*] update settings table
    g.conn.execute(text(f"""
                        UPDATE Settings
                        SET sel_trainid = '{trainid}';
                        """))
    g.conn.commit()

    print(f"Button clicked for row: {row_data}")
    return redirect(url_for('trainer_buy'))

# [*] BUTTON_CLICKED_BUY_TRAINER_ASSET
@app.route('/button_clicked_buy_trainer_asset/', methods=['POST'])
def button_clicked_buy_trainer_asset():
    # row_data is asset_id
    row_data = request.form.get('row_data')
    
    print(f"Button clicked for row: {row_data}")

    my_trainid, _, _, _  = get_current()
    sel_trainid, _ = get_selected_trainer()

    # [*] get cost
    cursor = g.conn.execute(text(f"""
                                SELECT A.cost
                                FROM Asset A
                                WHERE A.asset_id = '{row_data}'
                                """))
    g.conn.commit()

    cost = cursor.fetchone()[0]

    cursor.close()

    # [*] update my money
    cursor = g.conn.execute(text(f"""
                                SELECT T.money
                                FROM Trainer_Located_In T
                                WHERE T.TrainID = '{my_trainid}'
                                """))
    g.conn.commit()

    my_money_before = cursor.fetchone()[0]
    
    cursor.close()

    my_money_after = my_money_before - cost

    g.conn.execute(text(f"""
                        UPDATE Trainer_Located_In
                        SET Money = '{my_money_after}'
                        WHERE TrainID = '{my_trainid}'
                        """))
    g.conn.commit()

    # [*] update cpu money
    cursor = g.conn.execute(text(f"""
                                SELECT T.money
                                FROM Trainer_Located_In T
                                WHERE T.TrainID = '{sel_trainid}'
                                """))
    g.conn.commit()

    cpu_money_before = cursor.fetchone()[0]

    cursor.close()

    cpu_money_after = cpu_money_before + cost

    g.conn.execute(text(f"""
                        UPDATE Trainer_Located_In
                        SET Money = '{cpu_money_after}'
                        WHERE TrainID = '{sel_trainid}'
                        """))
    g.conn.commit()

    # [*] transfer ownership
    g.conn.execute(text(f"""
                        UPDATE Owns
                        SET TrainID = '{my_trainid}'
                        WHERE Asset_ID = '{row_data}'
                        """))
    g.conn.commit()
    
    return redirect(url_for('trainer'))

# [*] BUTTON_CLICKED_SELL_TRAINER
@app.route('/button_clicked_sell_trainer/', methods=['POST'])
def button_clicked_sell_trainer():
    row_data = request.form.get('row_data')
    
    # [*] get trainid using trainer name
    cursor = g.conn.execute(text(f"""
                                SELECT T.trainid
                                FROM Trainer_Located_In T
                                WHERE T.name = '{row_data}'
                                ORDER BY T.trainid
                                LIMIT 1
                                """))
    g.conn.commit()

    trainids = []
    results = cursor.mappings().all()
    for result in results:
      trainids.append(result["trainid"])
    cursor.close()
    trainid = trainids[0]

    # [*] update settings table
    g.conn.execute(text(f"""
                        UPDATE Settings
                        SET sel_trainid = '{trainid}';
                        """))
    g.conn.commit()

    print(f"Button clicked for row: {row_data}")
    return redirect(url_for('trainer_sell'))

# [**] BUTTON_CLICKED_SELL_TRAINER_ASSET
@app.route('/button_clicked_sell_trainer_asset/', methods=['POST'])
def button_clicked_sell_trainer_asset():
    # row_data is asset_id
    row_data = request.form.get('row_data')
    
    my_trainid, _, _, _  = get_current()
    sel_trainid, _ = get_selected_trainer()

    # [*] get cost
    cursor = g.conn.execute(text(f"""
                                SELECT A.cost
                                FROM Asset A
                                WHERE A.asset_id = '{row_data}'
                                """))
    g.conn.commit()

    cost = cursor.fetchone()[0]

    cursor.close()

    # [*] update my money
    cursor = g.conn.execute(text(f"""
                                SELECT T.money
                                FROM Trainer_Located_In T
                                WHERE T.TrainID = '{my_trainid}'
                                """))
    g.conn.commit()

    my_money_before = cursor.fetchone()[0]
    
    cursor.close()

    my_money_after = my_money_before + cost

    g.conn.execute(text(f"""
                        UPDATE Trainer_Located_In
                        SET Money = '{my_money_after}'
                        WHERE TrainID = '{my_trainid}'
                        """))
    g.conn.commit()

    # [*] update cpu money
    cursor = g.conn.execute(text(f"""
                                SELECT T.money
                                FROM Trainer_Located_In T
                                WHERE T.TrainID = '{sel_trainid}'
                                """))
    g.conn.commit()

    cpu_money_before = cursor.fetchone()[0]

    cursor.close()

    cpu_money_after = cpu_money_before - cost

    g.conn.execute(text(f"""
                        UPDATE Trainer_Located_In
                        SET Money = '{cpu_money_after}'
                        WHERE TrainID = '{sel_trainid}'
                        """))
    g.conn.commit()

    # [*] transfer ownership
    g.conn.execute(text(f"""
                        UPDATE Owns
                        SET TrainID = '{sel_trainid}'
                        WHERE Asset_ID = '{row_data}'
                        """))
    g.conn.commit()

    print(f"Button clicked for row: {row_data}")
    return redirect(url_for('trainer'))

# [*] === TRAINER/BUY ===
@app.route('/trainer/buy')
def trainer_buy():
    
    _, my_train_name, _, my_loc_name = get_current()
    my_money = get_money()
    sel_trainid, sel_train_name = get_selected_trainer()

    # [*] get pokemon
    cursor = g.conn.execute(text(f"""
                                SELECT P.PokeID, A.Name, P.PowerLVL, A.Cost, A2.Name AS "Held Item"
                                FROM Pokemon P
                                INNER JOIN Owns O ON O.Asset_ID = P.PokeID
                                INNER JOIN Asset A ON A.Asset_ID = O.Asset_ID
                                LEFT JOIN Holds H ON H.PokeID = P.PokeID
                                LEFT JOIN Asset A2 ON A2.Asset_ID = H.ItemID
                                WHERE O.TrainID = '{sel_trainid}'
                                """))


    # [*] display pokemon data in a table
    pokemon = []
    results = cursor.mappings().all()
    for result in results:
      pokemon.append(result)
    cursor.close()
    
   # [*] get evolution items
    cursor = g.conn.execute(text(f"""
                                 SELECT A.Asset_ID, A.Name, E.Evolves_From, E.Evolves_Into, A.Cost
                                 FROM Evolution_Item E
                                 JOIN Asset A ON A.Asset_ID = E.ItemID
                                 JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                 WHERE O.TrainID = '{sel_trainid}'
                                 """))
                                 
    evolution_items = []
    results = cursor.mappings().all()
    for result in results:
      evolution_items.append(result)
    cursor.close()

    # [*] get battle items
    cursor = g.conn.execute(text(f"""
                                 SELECT A.Asset_ID, A.Name, B.PowerLVL, A.Cost 
                                 FROM Battle_Item B
                                 JOIN Asset A ON A.Asset_ID = B.ItemID
                                 JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                 WHERE O.TrainID = '{sel_trainid}'
                                 """))
    battle_items = []
    results = cursor.mappings().all()
    for result in results:
      battle_items.append(result)
    cursor.close()

    # [*] get other items
    cursor = g.conn.execute(text(f"""
                                SELECT A.Asset_ID, A.Name, A.Cost
                                FROM Item I
                                JOIN Asset A ON A.Asset_ID = I.ItemID
                                LEFT JOIN Evolution_Item E ON I.ItemID = E.ItemID
                                JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                WHERE E.ItemID IS NULL
                                AND O.TrainID = '{sel_trainid}'
                                INTERSECT
                                SELECT A.Asset_ID, A.Name, A.Cost
                                FROM Item I
                                JOIN Asset A ON A.Asset_ID = I.ItemID
                                LEFT JOIN Battle_Item B ON I.ItemID = B.ItemID
                                JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                WHERE B.ItemID IS NULL
                                AND O.TrainID = '{sel_trainid}'
                                """))
                                # AND A.Asset_ID NOT IN 
                                #     (
                                #     SELECT H.ItemID
                                #     FROM Holds H
                                #     )
                                # AND A.Asset_ID NOT IN 
                                #     (
                                #     SELECT H.ItemID
                                #     FROM Holds H
                                #     )
    other_items = []
    results = cursor.mappings().all()
    for result in results:
      other_items.append(result)
    cursor.close()
    
    context = dict(pokemon_data = pokemon, ei_data = evolution_items, bi_data = battle_items, oi_data = other_items, my_train_name = my_train_name, my_loc_name = my_loc_name, sel_train_name = sel_train_name, my_money = my_money)

    return render_template("trainer_buy.html", **context)
   

# [**] === TRAINER/SELL ===
@app.route('/trainer/sell/')
def trainer_sell():
    # [*] specify who are selling to
    my_trainid, my_train_name, _, my_loc_name = get_current()
    my_money = get_money()
    sel_trainid, sel_train_name = get_selected_trainer()

    # [*] get pokemon
    cursor = g.conn.execute(text(f"""
                                SELECT P.PokeID, A.Name, P.PowerLVL, A.Cost, A2.Name AS "Held Item"
                                FROM Pokemon P
                                INNER JOIN Owns O ON O.Asset_ID = P.PokeID
                                INNER JOIN Asset A ON A.Asset_ID = O.Asset_ID
                                LEFT JOIN Holds H ON H.PokeID = P.PokeID
                                LEFT JOIN Asset A2 ON A2.Asset_ID = H.ItemID
                                WHERE O.TrainID = '{my_trainid}'
                                """))


    # [*] display pokemon data in a table
    pokemon = []
    results = cursor.mappings().all()
    for result in results:
      pokemon.append(result)
    cursor.close()
    
        # [*] get evolution items
    cursor = g.conn.execute(text(f"""
                                 SELECT A.Name, E.Evolves_From, E.Evolves_Into, A.Cost
                                 FROM Evolution_Item E
                                 JOIN Asset A ON A.Asset_ID = E.ItemID
                                 JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                 WHERE O.TrainID = '{my_trainid}'
                                 AND A.Asset_ID NOT IN 
                                    (
                                    SELECT H.ItemID
                                    FROM Holds H
                                    )
                                 """))
                                 
    evolution_items = []
    results = cursor.mappings().all()
    for result in results:
      evolution_items.append(result)
    cursor.close()

    # [*] get battle items
    cursor = g.conn.execute(text(f"""
                                 SELECT A.Name, B.PowerLVL, A.Cost
                                 FROM Battle_Item B
                                 JOIN Asset A ON A.Asset_ID = B.ItemID
                                 JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                 WHERE O.TrainID = '{my_trainid}'
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

    # [*] get other items
    cursor = g.conn.execute(text(f"""
                                SELECT A.Name, A.Cost
                                FROM Item I
                                JOIN Asset A ON A.Asset_ID = I.ItemID
                                LEFT JOIN Evolution_Item E ON I.ItemID = E.ItemID
                                JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                WHERE E.ItemID IS NULL
                                AND O.TrainID = '{my_trainid}'
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
                                AND O.TrainID = '{my_trainid}'
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
    
    context = dict(pokemon_data = pokemon, ei_data = evolution_items, bi_data = battle_items, oi_data = other_items, my_train_name = my_train_name, my_loc_name = my_loc_name, sel_train_name = sel_train_name, my_money = my_money)

    return render_template("trainer_sell.html", **context)

# [**] ======== BAG =========
@app.route('/bag/')
def bag():

    my_trainid, my_train_name, _, my_loc_name = get_current()
    print(f"my_trainid: {my_trainid}")

    # [*] get evolution items
    cursor = g.conn.execute(text(f"""
                                 SELECT A.Name, E.Evolves_From, E.Evolves_Into, A.Cost
                                 FROM Evolution_Item E
                                 JOIN Asset A ON A.Asset_ID = E.ItemID
                                 JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                 WHERE O.TrainID = '{my_trainid}'
                                 """))
                                #  AND A.Asset_ID NOT IN 
                                #     (
                                #     SELECT H.ItemID
                                #     FROM Holds H
                                #     )
                                 
    evolution_items = []
    results = cursor.mappings().all()
    for result in results:
      evolution_items.append(result)
    cursor.close()

    # [*] get battle items
    cursor = g.conn.execute(text(f"""
                                 SELECT A.Name, B.PowerLVL, A.Cost
                                 FROM Battle_Item B
                                 JOIN Asset A ON A.Asset_ID = B.ItemID
                                 JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                 WHERE O.TrainID = '{my_trainid}'
                                 """))
                                #  AND A.Asset_ID NOT IN 
                                #     (
                                #     SELECT H.ItemID
                                #     FROM Holds H
                                #     )
    battle_items = []
    results = cursor.mappings().all()
    for result in results:
      battle_items.append(result)
    cursor.close()

    # [*] get other items
    cursor = g.conn.execute(text(f"""
                                SELECT A.Name, A.Cost
                                FROM Item I
                                JOIN Asset A ON A.Asset_ID = I.ItemID
                                LEFT JOIN Evolution_Item E ON I.ItemID = E.ItemID
                                JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                WHERE E.ItemID IS NULL
                                AND O.TrainID = '{my_trainid}'
                                INTERSECT
                                SELECT A.Name, A.Cost
                                FROM Item I
                                JOIN Asset A ON A.Asset_ID = I.ItemID
                                LEFT JOIN Battle_Item B ON I.ItemID = B.ItemID
                                JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                WHERE B.ItemID IS NULL
                                AND O.TrainID = '{my_trainid}'
                                """))
                                # AND A.Asset_ID NOT IN 
                                #     (
                                #     SELECT H.ItemID
                                #     FROM Holds H
                                #     )
                                # AND A.Asset_ID NOT IN 
                                #     (
                                #     SELECT H.ItemID
                                #     FROM Holds H
                                #     )
    other_items = []
    results = cursor.mappings().all()
    for result in results:
      other_items.append(result)
    cursor.close()
    
    context = dict(ei_data = evolution_items, bi_data = battle_items, oi_data = other_items)

    # [**] display bag data in a table
    return render_template("bag.html", **context)

# [*] BUTTON_CLICKED_GIVE_ITEM
@app.route('/button_clicked_give_item/', methods=['POST'])
def button_clicked_give_item():
    row_data = request.form.get('row_data')
    
    # [*] get asset_id using item name
    cursor = g.conn.execute(text(f"""
                                SELECT A.asset_id
                                FROM Asset A
                                WHERE A.name = '{row_data}'
                                ORDER BY A.asset_id
                                LIMIT 1
                                """))
    g.conn.commit()

    asset_ids = []
    results = cursor.mappings().all()
    for result in results:
      asset_ids.append(result["asset_id"])
    cursor.close()
    asset_id = asset_ids[0]

    # [*] update settings table
    g.conn.execute(text(f"""
                        UPDATE Settings
                        SET sel_give_itemid = '{asset_id}';
                        """))
    g.conn.commit()
    
    print(f"Button clicked for row: {row_data}")
    return redirect(url_for('bag_give_item'))

# [**] BUTTON_CLICKED_GIVE_ITEM_POKEMON
@app.route('/button_clicked_give_item_pokemon/', methods=['POST'])
def button_clicked_give_item_pokemon():
    pokeid = request.form.get('pokeid')
    itemid = request.form.get('itemid')
    sel_give_itemid, _ = get_selected_give_item()
    
    print(f"[775] Button clicked for row: {pokeid}")
    print(f"Button clicked for row: {itemid}")

    cursor = g.conn.execute(text(f"""
                                SELECT *
                                FROM Holds H
                                WHERE H.pokeid = '{pokeid}'
                                """))
    g.conn.commit()

    holding = cursor.fetchone()
    cursor.close()

    if holding:
        print("Pokemon is already holding an item")
        pass
    else:
        print("Gave the item")
        g.conn.execute(text(f"""
                            INSERT INTO Holds(pokeid, itemid)
                            VALUES ('{pokeid}', '{sel_give_itemid}')
                            """))
        g.conn.commit()

        g.conn.execute(text(f"""
                            DELETE
                            FROM Owns O
                            WHERE O.asset_id = '{sel_give_itemid}'
                            """))
        g.conn.commit()

    
    return redirect(url_for('bag'))

# [**] BUTTON_CLICKED_USE_EVO_ITEM
@app.route('/button_clicked_use_evo_item/', methods=['POST'])
def button_clicked_use_evo_item():
    row_data = request.form.get('row_data')
    
    print(f"Button clicked for row: {row_data}")
    return redirect(url_for('bag_use_evolution_item'))

# [**] ======= BAG/USE_EVOLUTION_ITEM =========
@app.route('/bag/use_evolution_item/')
def bag_use_evolution_item():
   # [*] get my pokemon
    #    [***] Make sure you can only use evolution item on pokemon that is not holding an item
    cursor = g.conn.execute(text(f"""
                                SELECT P.PokeID, A.Name, P.PowerLVL, A2.Name AS "Held Item"
                                FROM Pokemon P
                                JOIN Asset A ON A.Asset_ID = P.PokeID
                                JOIN Owns O ON O.Asset_ID = A.Asset_ID
                                LEFT JOIN Holds H ON H.PokeID = P.PokeID
                                LEFT JOIN Asset A2 ON A2.Asset_ID = H.ItemID
                                WHERE A.Name = 
                                    (
                                    SELECT E.Evolves_From
                                    FROM Evolution_Item E
                                    WHERE E.ItemID = '{SELECTED_EVOLUTION_ITEM_ID}'
                                    )
                                AND O.TrainID = '{MY_TRAINER_ID}'
                                """))


    # [**] display pokemon data in a table
    pokemon = []
    results = cursor.mappings().all()
    for result in results:
      pokemon.append(result)
    cursor.close()

    context = dict(data = pokemon)

    return render_template("bag_use_evolution_item.html", **context)


# [**] ======= BAG/GIVE_ITEM ========
@app.route('/bag/give_item/')
def bag_give_item():
    my_trainid, my_train_name, _, my_loc_name = get_current()
    sel_give_itemid, sel_give_item_name = get_selected_give_item()
    
   # [*] get my pokemon
    # [***] Make sure you can only give item to pokemon that doesn't have an item
    cursor = g.conn.execute(text(f"""
                                SELECT P.PokeID, A.Name, P.PowerLVL, A2.Name AS "Held Item", A2.Asset_ID AS ItemID
                                FROM Pokemon P
                                INNER JOIN Owns O ON O.Asset_ID = P.PokeID
                                INNER JOIN Asset A ON A.Asset_ID = O.Asset_ID
                                LEFT JOIN Holds H ON H.PokeID = P.PokeID
                                LEFT JOIN Asset A2 ON A2.Asset_ID = H.ItemID
                                WHERE O.TrainID = '{my_trainid}'
                                """))


    # [**] display pokemon data in a table
    pokemon = []
    results = cursor.mappings().all()
    for result in results:
      pokemon.append(result)
    cursor.close()

    context = dict(data = pokemon, sel_give_item_name = sel_give_item_name)

    return render_template("bag_give_item.html", **context)


# [**] ======= POKEMON =======
@app.route('/pokemon/')
def pokemon():

    my_trainid, my_train_name, my_locid, my_loc_name = get_current()

    # [**] get my pokemon
    # [*] also display pokemon that don't hold an item
    cursor = g.conn.execute(text(f"""
                                SELECT P.PokeID, A.Name, P.PowerLVL, A.Cost, A2.Name AS "Held Item"
                                FROM Pokemon P
                                INNER JOIN Owns O ON O.Asset_ID = P.PokeID
                                INNER JOIN Asset A ON A.Asset_ID = O.Asset_ID
                                LEFT JOIN Holds H ON H.PokeID = P.PokeID
                                LEFT JOIN Asset A2 ON A2.Asset_ID = H.ItemID
                                WHERE O.TrainID = '{my_trainid}'
                                """))


    # [**] display pokemon data in a table
    pokemon = []
    results = cursor.mappings().all()
    for result in results:
      pokemon.append(result)
    cursor.close()

    context = dict(data = pokemon)

    return render_template("pokemon.html", **context)

# [**] BUTTON_CLICKED_TAKE_ITEM
@app.route('/button_clicked_take_item/', methods=['POST'])
def button_clicked_take_item():
    # row_data contains pokeid
    row_data = request.form.get('row_data')
    
    # [***] update pokemon table

    # [***] update holds table

    print(f"Button clicked for row: {row_data}")
    return redirect(url_for('pokemon'))

# [*] ======= GET_CURRENT =========
def get_current():
   # [*] get current trainer id
    cursor = g.conn.execute(text(f"""
                                SELECT S.my_trainid
                                FROM settings S
                                ORDER BY S.my_trainid
                                LIMIT 1
                                """))
    g.conn.commit()

    my_trainids = []
    results = cursor.mappings().all()
    for result in results:
      my_trainids.append(result["my_trainid"])
    cursor.close()

    my_trainid = my_trainids[0]

    # [*] get current trainer name
    cursor = g.conn.execute(text(f"""
                                SELECT T.name
                                FROM Trainer_Located_In T
                                WHERE T.trainid = '{my_trainid}'
                                ORDER BY T.trainid
                                LIMIT 1
                                """))
    g.conn.commit()

    my_train_names = []
    results = cursor.mappings().all()
    for result in results:
      my_train_names.append(result["name"])
    cursor.close()

    my_train_name = my_train_names[0]

    # [*] get current location id
    cursor = g.conn.execute(text(f"""
                                SELECT S.my_locid
                                FROM settings S
                                ORDER BY S.my_locid
                                LIMIT 1
                                """))
    g.conn.commit()

    my_locids = []
    results = cursor.mappings().all()
    for result in results:
      my_locids.append(result["my_locid"])
    cursor.close()

    my_locid = my_locids[0]

    # [*] get current location name
    cursor = g.conn.execute(text(f"""
                                SELECT L.locname
                                FROM Location L
                                WHERE L.locid = '{my_locid}'
                                ORDER BY L.locid
                                LIMIT 1
                                """))
    g.conn.commit()

    my_loc_names = []
    results = cursor.mappings().all()
    for result in results:
      my_loc_names.append(result["locname"])
    cursor.close()

    my_loc_name = my_loc_names[0]

    return my_trainid, my_train_name, my_locid, my_loc_name

# [**] === GET_MONEY ===
def get_money():
    # [*] get current trainer id
    cursor = g.conn.execute(text(f"""
                                SELECT S.my_trainid
                                FROM settings S
                                ORDER BY S.my_trainid
                                LIMIT 1
                                """))
    g.conn.commit()

    my_trainids = []
    results = cursor.mappings().all()
    for result in results:
      my_trainids.append(result["my_trainid"])
    cursor.close()

    my_trainid = my_trainids[0]

    # [**] get money
    cursor = g.conn.execute(text(f"""
                                SELECT T.money
                                FROM Trainer_Located_In T
                                WHERE T.TrainID = '{my_trainid}'
                                ORDER BY T.TrainID
                                LIMIT 1
                                """))
    g.conn.commit()

    moneys = []
    results = cursor.mappings().all()
    for result in results:
      moneys.append(result["money"])
    cursor.close()

    my_money = moneys[0]
    return my_money

# [*] === GET_SELECTED_TRAINER ===
def get_selected_trainer():
   # [*] get selected trainer id
    cursor = g.conn.execute(text(f"""
                                SELECT S.sel_trainid
                                FROM settings S
                                ORDER BY S.sel_trainid
                                LIMIT 1
                                """))
    g.conn.commit()

    sel_trainids = []
    results = cursor.mappings().all()
    for result in results:
      sel_trainids.append(result["sel_trainid"])
    cursor.close()

    sel_trainid = sel_trainids[0]

    # [*] get selected trainer name
    cursor = g.conn.execute(text(f"""
                                SELECT T.name
                                FROM Trainer_Located_In T
                                WHERE T.trainid = '{sel_trainid}'
                                ORDER BY T.trainid
                                LIMIT 1
                                """))
    g.conn.commit()

    sel_train_names = []
    results = cursor.mappings().all()
    for result in results:
      sel_train_names.append(result["name"])
    cursor.close()

    sel_train_name = sel_train_names[0]

    return sel_trainid, sel_train_name

# [*] === GET_SELECTED_GIVE_ITEM ===
def get_selected_give_item():
   # [*] get selected give item id
    cursor = g.conn.execute(text(f"""
                                SELECT S.sel_give_itemid
                                FROM settings S
                                ORDER BY S.sel_give_itemid
                                LIMIT 1
                                """))
    g.conn.commit()

    sel_give_itemids = []
    results = cursor.mappings().all()
    for result in results:
      sel_give_itemids.append(result["sel_give_itemid"])
    cursor.close()

    sel_give_itemid = sel_give_itemids[0]

    # [*] get selected give item name
    cursor = g.conn.execute(text(f"""
                                SELECT A.name
                                FROM Asset A
                                WHERE A.asset_id = '{sel_give_itemid}'
                                ORDER BY A.asset_id
                                LIMIT 1
                                """))
    g.conn.commit()

    sel_give_item_names = []
    results = cursor.mappings().all()
    for result in results:
      sel_give_item_names.append(result["name"])
    cursor.close()

    sel_give_item_name = sel_give_item_names[0]

    return sel_give_itemid, sel_give_item_name

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