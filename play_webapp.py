# encoding=utf8  
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')
from flask import Flask, session, request, render_template, url_for, redirect
import os
import logging
from logging.handlers import RotatingFileHandler
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.getcwd() + "/resources")
sys.path.insert(0, os.getcwd() + "/ui") 
from ClimateConversationsCore import *

app = Flask(__name__)

game_cache = {}



@app.route("/")
def main():
    return render_template('index.html')

@app.route("/setup")
def game_setup():
    return render_template("setup.html")

@app.route("/setup/save", methods=['POST'])
def save_game_setup():
    global game_cache
    form_data = request.form
    n_rounds = int(form_data.get("num_rounds"))
    app.logger.info("Saved n_rounds: %d" % n_rounds)
    players = []

    # TODO remove this hardcoding!!
    p1_name = form_data.get("name-p1")
    p1_byear = int(form_data.get("birthyear-p1"))
    p1 = Player(p1_name, p1_byear)
    players.append(p1)

    p2_name = form_data.get("name-p2")
    p2_byear = int(form_data.get("birthyear-p2"))
    if p2_name:
        p2 = Player(p2_name, p2_byear)
        players.append(p2)
    else:
        pass

    p3_name = form_data.get("name-p3")
    p3_byear = int(form_data.get("birthyear-p3"))
    if p3_name:
        p3 = Player(p3_name, p3_byear)
        players.append(p3)
    else:
        pass

    p4_name = form_data.get("name-p4")
    p4_byear = int(form_data.get("birthyear-p4"))
    if p4_name:
        p4 = Player(p4_name, p4_byear)
        players.append(p4)
    else:
        pass

    p5_name = form_data.get("name-p5")
    p5_byear = int(form_data.get("birthyear-p5"))
    if p5_name:
        p5 = Player(p5_name, p5_byear)
        players.append(p5)
    else:
        pass

    p6_name = form_data.get("name-p6")
    p6_byear = int(form_data.get("birthyear-p6"))
    if p6_name:
        p6 = Player(p6_name, p6_byear)
        players.append(p6)
    else:
        pass

    # The code below uses the same session key if they've played before
    # HOWEVER, this is not what we want. We should start a new session if
    # the user starts a new round. In the future if we did this more 
    # intelligently, it would be nice to save the questions they got previously
    # so they didn't get the same questions in a new round. Removing for now.
    # try:
    #     user_key = session['user_key']
    # except:
    #     user_key = os.urandom(24)
    #     session['user_key'] = user_key  

    player_string = "\n".join([str(p) for p in players])
    app.logger.info("Added players: \n%s" % player_string)

    user_key = os.urandom(24)
    app.logger.info("Assigned session key: %s" % user_key)
    session['user_key'] = user_key  # players

    convo = Conversation(n_rounds = n_rounds, players=players,
                         gdrive_key="1fiI18O4inR-Pm7XFnFitCrbfoGjXpZX_D_On348y4j8") # Subset of 10 questions
                         #gdrive_key="183SABhCyJmVheVwu_1rWzY7jOjvtyfbmG58ow321a3g") # Original set of 70ish questions
                         #events_file="data/firstHistoricClimateEvents.xlsx") # Locally stored copy
    game_cache[user_key] = convo

    return redirect("/play", code=302)


@app.route("/play")
def play_game():
    global game_cache
    app.logger.info("Loading convo from cache")
    user_key = session['user_key']
    convo = game_cache.get(user_key)
    app.logger.info("Successfully retrieved conversation")
    player = convo.get_current_player()
    app.logger.info("Asked the game for a player, got: %s" % str(player))

    # Case: Game returned 'None' for the player.
    #       This usually means that we ran out of rounds, so we end.
    if player is None:
        app.logger.info("No player returned (probably no more rounds). Serving up 'OUT OF QUESTIONS.'")
        game_cache.pop(user_key)
        return render_template("feedback.html", event='Game over! Thanks for playing :)', next_button_text="Play again?", next_button_target="/setup")

    incr = convo.increment_player()
    app.logger.info("Incremented player")
    e_idx, event = convo.get_next_event(player)

    # Case: Game returned 'None' for the event index.
    #       This usually means that there are no more events left for this player.
    #       Currently choosing to just keep going without that player.
    if e_idx is None:
        app.logger.info("No event index returned. Likely no more questions available for this player. Serving up 'OUT OF QUESTIONS' and removing player")
        convo.remove_player(player.name, player.birth_year)
        return render_template("play.html", player_name="", question='Sorry, out of questions for %s' % player.name, event="", next_button_text="Keep going with other players", next_button_target="/play")

    app.logger.debug("Got event %d: %s" % (e_idx, event))
    question = convo.get_question(e_idx)
    app.logger.debug("Got question: %s" % question)

    # Case: Successfully retrieved player, event, and question
    #       Display the question on the page!    
    return render_template("play.html", player_name=player.name, event=event, question=question, next_button_text="Next person", next_button_target="/play")
    

if __name__ == "__main__":
    handler = RotatingFileHandler('logs/webapp.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    # formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    formatter = logging.Formatter( "%(asctime)s | %(pathname)s:%(lineno)d | %(funcName)s | %(levelname)s | %(message)s ")
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.secret_key = os.urandom(32)
    app.run(debug=True)