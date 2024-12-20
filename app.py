from flask import Flask, render_template, session, flash, request

import cards
import random

import DBcm

creds = {
    "host": "localhost",
    "user": "gofishappuser",
    "password": "gofishpasswd",
    "database": "gofishappdb",
}

results = []
currentUser = "Test7"
score = 6969

app = Flask(__name__)
app.secret_key = "awdlwaspdlwphfksmdkelfkdseofpdklsmelkf"

@app.get("/restart")
def reset_state():
    session["deck"] = cards.build_deck()

    session["computer"] = []
    session["player"] = []
    session["player_pairs"] = []
    session["computer_pairs"] = []

    for _ in range(7):
        session["computer"].append(session["deck"].pop())
        session["player"].append(session["deck"].pop())

    session["player"], pairs = cards.identify_remove_pairs(session["player"])
    session["player_pairs"].extend(pairs)
    session["computer"], pairs = cards.identify_remove_pairs(session["computer"])
    session["computer_pairs"].extend(pairs)

    session["gameover"] = False
    session["state"] = ""

@app.get("/")
def enterUser():


    reset_state()
    card_images = [ card.lower().replace(" ","_") + ".png" for card in session["player"]]
    print(card_images)

    return render_template(
        "intro.html",
        title = "Welcome to GoFish for the Web",
        cards = card_images, # available in the template as {{ cards }}
        player_pairs = int(len(session["player_pairs"]) / 2),
        computer_pairs = int(len(session["computer_pairs"]) / 2),
        n_computer = len(session["computer"]), #available in the template as {{ n_computer }}
        n_deck = len(session["deck"])
    )

@app.route('/startgame', methods = ['POST'])
def start():

    currentUser = request.form["username"]
    reset_state()
    card_images = [ card.lower().replace(" ","_") + ".png" for card in session["player"]]
    print(card_images)
    return render_template(
        "startgame.html",
        title = "Welcome to GoFish for the Web",
        cards = card_images, # available in the template as {{ cards }}
        player_pairs = int(len(session["player_pairs"]) / 2),
        computer_pairs = int(len(session["computer_pairs"]) / 2),
        n_computer = len(session["computer"]), #available in the template as {{ n_computer }}
        n_deck = len(session["deck"])
    )

@app.get("/select/<value>")
def process_card_selection(value):
    

    found_it = False
    for n, card in enumerate(session["computer"]):
        if card.startswith(value):
            found_it = n
            break
    if isinstance(found_it, bool):
        flash("Go Fish!")
        session["player"].append(session["deck"].pop())
        flash(f"You drew a {session["player"][-1]}.")

        ##if len(session["deck"]) == 0:
        ##    break
    else:
        flash(f"Here is your card from the computer: {session["computer"][n]}.")
        session["player"].append(session["computer"].pop(n))

    session["player"], pairs = cards.identify_remove_pairs(session["player"])
    session["player_pairs"].extend(pairs)

    # if len(player) == 0:
    #     print("The Game is over. The player won.")
    #     break
    # if len(computer) == 0:
    #     print("The Game is over. The computer won.")
    #     break

    card = random.choice(session["computer"])
    the_value = card[: card.find(" ")]

    card_images = [ card.lower().replace(" ","_") + ".png" for card in session["player"]]

    check_game_over()
    if(session["gameover"] == True):

        score = session["player_pairs"] * 100

        scoreStr = str(score)
        query = createSQLQuery(currentUser, scoreStr)

        addScore(query)
        results = setupBoard()
        return render_template(
             "gameover.html",
             title = "Game Over",
             state = session["state"],
             leader = results
        )

    return render_template(
        "pickcard.html",
        title = "The computer wants to know",
        value = the_value,
        cards = card_images, # available in the template as {{ cards }}
    )

@app.get("/pick/<value>")
def process_the_picked_card(value):
    

    if value == "0":
            session["computer"].append(session["deck"].pop())
    else:
        for n, card in enumerate(session["player"]):
                if card.startswith(value.title()):
                    break
        session["computer"].append(session["player"].pop(n))

    session["computer"], pairs = cards.identify_remove_pairs(session["computer"])
    session["computer_pairs"].extend(pairs)

    card_images = [ card.lower().replace(" ","_") + ".png" for card in session["player"]]
    check_game_over()
    if(session["gameover"] == True):
       
        score = session["player_pairs"] * 100

        scoreStr = str(score)
        query = createSQLQuery(currentUser, scoreStr)

        addScore(query)
        results = setupBoard()
        return render_template(
             "gameover.html",
             title = "Game Over",
             state = session["state"],
             leader = results
        )
    
    return render_template(
        "startgame.html",
        title = "Keep Playing",
        cards = card_images, # available in the template as {{ cards }}
        player_pairs = int(len(session["player_pairs"]) / 2),
        computer_pairs = int(len(session["computer_pairs"]) / 2),
        n_computer = len(session["computer"]), #available in the template as {{ n_computer }}
        n_deck = len(session["deck"])
    )
    
@app.get("/gameover")
def check_game_over():
    if(len(session["player"]) == 0):
        session["state"] = "Player Wins!"
        session["gameover"] = True
        return

    if(len(session["computer"]) == 0):
        session["state"] = "Computer Wins!"
        session["gameover"] = True
        return

    if(len(session["deck"]) == 0):
        if(session["computer_pairs"] == session["player_pairs"]):
            session["state"] = "Draw"
            session["gameover"] = True
            return

        if(session["computer_pairs"] > session["player_pairs"]):
            session["state"] = "Computer Wins!"
            session["gameover"] = True
            return
        else:
            session["state"] = "Player Wins!"
            session["gameover"] = True
            return

def addScore(query):
    with DBcm.UseDatabase(creds) as db:
        db.execute("select * from players")
        results = db.fetchall()

    for r in results:
        if currentUser == r[0]:
            with DBcm.UseDatabase(creds) as db:
                db.execute("update players set score = 99999 where username = 'Test4'")
                return

    with DBcm.UseDatabase(creds) as db:
            db.execute(query)
    


        
   

def setupBoard():
    with DBcm.UseDatabase(creds) as db:
        db.execute("select * from players order by score desc limit 10")
        results = db.fetchall()

    return results

def createSQLQuery(username, score):
    
    query = "insert into players (username, score, wins, loss) values ('" + username + "'," + score + ", 0, 0)"

    return query

app.run(debug=True)