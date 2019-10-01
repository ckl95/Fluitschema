from flask import flash, redirect, render_template, request, session, abort, send_file, Flask
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import sys
from os import environ
import psycopg2
import numpy as np
import pandas as pd
from io import BytesIO
from flask_sqlalchemy import SQLAlchemy
from database import app, database
from models import users, schedule

database.create_all()

from helpers import login_required, create_duty_amounts, get_username, DutyTable, TeamsTable, GameSchedule
from to_html import to_html_file_writer

@app.after_request
# Ensure responses aren't cached
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/change", methods=["GET", "POST"])
@login_required
def change():

    username = get_username()
    if request.method == "POST" and "schedule" in request.form:

        # Retrieve the sql tables from the current user
        df_schedule = DutyTable("sql")
        
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df_schedule.df_duty_table.to_excel(writer, sheet_name="schedule", index=False)
        writer.save()
        output.seek(0)
        
        return send_file(output, as_attachment=True, attachment_filename='schedule.xlsx')
    
    elif request.method == "POST" and "update" in request.form:

        # if file is missing
        if 'update' not in request.files:
            abort(400, "Missing File")
        file = request.files["update"]

        # prepares the new duty table
        df_schedule_updated = pd.read_excel(file, sheet_name=0) # turn the excel sheet into pandas dataframe
        df_schedule_updated = df_schedule_updated.dropna(how = "all").reset_index().drop(columns = "index") # delete empty rows
        df_schedule_updated["username"] = username # make sure username = current username

        # Deletes former schedule
        schedule.query.filter_by(username=username).delete()
        database.session.commit()

        # deletes former schedule
        #db = conn.cursor()
        #db.execute("DELETE FROM schedule WHERE username=:username", {"username": username[0]})
            
        # adds current updated schedule
        df_schedule_updated.to_sql("schedule", database.session.bind, if_exists='append', index=False)

        return redirect("/", code=302)

    else:
        return render_template("change.html")     


@app.route("/download")
@login_required
def download():

    # Create the dataframe containing the teams and the players
    df_teams_table = TeamsTable("duty_table")
  
    # Create the tables that are to be exported
    df_players = df_teams_table.create_playerduties_table()
    df_teams = df_teams_table.create_teamduties_table()
    
    # write to an excel file
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    df_players.to_excel(writer, sheet_name="players", index=False)
    df_teams.to_excel(writer, sheet_name="teams", index=False)
    
    writer.close()
    output.seek(0)

    return send_file(output, as_attachment=True, attachment_filename='duties.xlsx')


@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    username = get_username()
    print(username)
    c_2 = schedule.query.filter_by(username=username).group_by(schedule.username, schedule.days, schedule.times, schedule.hometeam, schedule.awayteam).all()
    weeks = []
    for week in c_2:
        if week.days not in weeks:
            weeks.append(week.days)

    weeks.sort()
    
    data = [[]]
    new_ls = ["t06"]

    if request.method == "POST":

        # When a week is not selected
        if not request.form.get("weeks"):
            return abort(400, "must select week")

        data = schedule.query.filter_by(username=username, days=request.form.get("weeks")).all()

        # Formatting the zaalco duty data
        zaalcos = []
        for game in data:
            if game.zaalco == None:
                zaalcos.append("")
            else:
                zaalcos.append(game.zaalco)

        # Formatting the table duty data
        tables = []
        for game in data:
            table_string = ""
            if game.table1 != None:
                table_string = table_string + game.table1
            if game.table2 != None:
                table_string = table_string + ", " + game.table2
            if game.table3 != None:
                table_string = table_string + ", " + game.table3
                
            table_string = table_string.replace(", , ", ", ")
            if table_string[-2:] == ", ":
                table_string = table_string[:-2]
            if table_string[:2] == ", ":
                table_string = table_string[2:]
            tables.append(table_string)

        # Formatting the referees
        referees = []
        for game in data:
            referee_string = ""
            if game.referee1 != None:
                referee_string = referee_string + game.referee1
            if game.referee2 != None:
                referee_string = referee_string + ", " + game.referee2

            if referee_string[-2:] == ", ":
                referee_string = referee_string[:-2]
            if referee_string[:2] == ", ":
                referee_string = referee_string[2:]
            referees.append(referee_string)

        # Getting the right css id
        a = 6
        for i in range(len(data) - 1):
            if data[i + 1].times == data[i].times:
                b = "t0" + str(a)
                new_ls.append(b)
            else:
                if a == 6:
                    a += 1
                elif a == 7:
                    a = a - 1
                b = "t0" + str(a)
                new_ls.append(b)
        return render_template("index.html", weeks=weeks, tables=tables, referees=referees, zaalcos=zaalcos, data=data, length=len(data), new_ls=new_ls)
    else:
        return render_template("index.html", weeks=weeks, data=data, length=0)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            print("Missing username")
            flash("Missing Username")
            return redirect("/login")

        # Ensure password was submitted
        elif not request.form.get("password"):
            print("Missing password")
            flash("Missing Password")
            return redirect("/login")

        # Query database for username
        rows = users.query.filter_by(username=request.form.get("username")).first()

        # Ensure username exists and password is correct
        try:
            check_password_hash(rows.hash, request.form.get("password"))
        except AttributeError:
            print("Username and or password are incorrect")
            flash("Username or password is incorrect")
            return redirect("/login")

        # Remember which user has logged in
        print(rows.id)
        session["user_id"] = rows.id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """ adds an file to the server"""

    if request.method == "POST":

        # Read files
        if 'file' not in request.files:
            abort(400, "missing file")
        game_members = request.files["file"]

        if 'file2' not in request.files:
            abort(400, "missing file")
        game_schedule = request.files["file2"]

        # Creates TeamsTable from file
        df_game_members = pd.read_excel(game_members, sheet_name=0) # Turns the congressus file into a dataframe
        df_teams = TeamsTable("congressus", df_game_members) 

        # Prepares the gameschedule
        df_game_schedule = pd.read_excel(game_schedule, sheet_name=0) # Turns game schedule into a pandas dataframe                
        df_game_schedule = GameSchedule.delete_away_games(df_game_schedule)        
        df_game_schedule = GameSchedule.change_time_format(df_game_schedule)

        # Creates the table and referees amount dataframe.
        df_duty_amounts = create_duty_amounts()   

        # Creates the duty table
        duty_table = DutyTable("scratch", df_game_schedule, df_teams.df_teams_table, df_duty_amounts) 
        duty_table.to_sql() # Puts the duty table into SQL

        return redirect("/", code=302)

    else:
        return render_template("new.html")


@app.route("/read_me")
@login_required
def read_me():
    """ sends an readme.text to the client."""

    return send_file("ReadMe.txt", as_attachment=True, attachment_filename='ReadMe.txt')


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return abort(400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return abort(400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return abort(400)

        # Ensure password matches the confirmation
        elif request.form.get("confirmation") != request.form.get("password"):
            return abort(400)

        # Makes an hash out of the password
        hash = generate_password_hash(request.form.get("password"))

        #insert user into users table
        new_user = users(username=request.form.get("username"), hash=hash)
        database.session.add(new_user)

        # Save SQL table
        database.session.commit()

        # Query database for username
        c = users.query.filter_by(username=request.form.get("username")).first()

        # Remember which user has logged in
        session["user_id"] = c.id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/to_html", methods=["GET", "POST"])
def to_html():
    if request.method == "POST" and "excel_file" in request.form:
    
        # if file is missing
        if 'excel_file' not in request.files:
            abort(400, "Missing File")
        file = request.files["excel_file"]

        # Opens the excel table and formats it
        df_schedule = pd.read_excel(file)
        df_schedule = df_schedule.fillna('')

        # Create new file
        #f = open("new.txt", "w", encoding="utf-8")
        output = BytesIO()
        to_html_file_writer(df_schedule, output)
        output.seek(0)
        return send_file(output, as_attachment=True, attachment_filename='new.txt')

    elif request.method == "POST" and "example" in request.form:

        return send_file("5-okt.xlsx", as_attachment=True, attachment_filename="example_file.xlsx")

    else:
        return render_template("to_html.html")


