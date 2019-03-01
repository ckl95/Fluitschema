from flask import redirect, session, abort, flash
from functools import wraps, reduce
import operator
import sqlite3
import numpy as np
import pandas as pd

sqlite3.register_adapter(np.int64, lambda val: int(val))
sqlite3.register_adapter(np.int32, lambda val: int(val))

# connenct SQLite to project.db
conn = sqlite3.connect("project.db")


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def get_username():
    """ Retrieve the username"""
    
    #  Import username to insert into SQL
    db = conn.cursor()
    c = db.execute(""" SELECT username FROM users WHERE id = :id""", {"id": session["user_id"]})
    username = c.fetchone()
    db.close()
    return username


class TeamsTable:
    """ Operations that include the teams table"""

    def __init__(self, method, file=None):
        if method == "congressus":
            self.from_congressus(file)
        elif method == "duty_table":
            self.from_duty_table()
        return

    def from_congressus(self, df_game_members):
        """ Formats the congressus table in a pandas dataframe containing all teams"""

        # Selects the usable parts of the congressus table
        df_slice = df_game_members.loc[:,["Voornaam","Tussenvoegsel", "Achternaam","Huidige groepslidmaatschappen"]]

        # Each player is assigned to a team 
        data = {}
        for index, row in df_slice.iterrows():

            # empty cells are ignored
            if pd.isna(row["Huidige groepslidmaatschappen"]) == True:
                continue

            # Coaches are not selected
            if "Coach" in row["Huidige groepslidmaatschappen"]:
                continue

            # Board members are not selected
            if "Bestuur" in row["Huidige groepslidmaatschappen"]:
                continue


            # Teams are filtered out of the groups
            result = map(str.strip, row["Huidige groepslidmaatschappen"].split(','))
            for team in result:
                cond1 = any(name in team for name in ('De Groene Uilen', 'Moestasj'))
                cond2 = any(name in team for name in ('Heren', 'Dames'))
                if cond1 == False or cond2 == False:
                    continue

                # for consistency with the schedule file
                if "Heren" in team:
                    team = team.replace("Heren", "MSE")
                elif "Dames" in team:
                    team = team.replace("Dames", "VSE")
            
                # contaminate the name
                if pd.isna(row["Tussenvoegsel"]) == True:
                    name = row["Voornaam"] + " " + row["Achternaam"]
                else:
                    name = row["Voornaam"] + " " + row["Tussenvoegsel"] + " " + row["Achternaam"]
            
                # if team already in dict, append. Else create new key.
                if team in data.keys():
                    data[team].append(name)
                else:
                    data[team] = [name]
    
        # create dataframe
        new_df = pd.DataFrame.from_dict(data, orient="index")
        new_df = new_df.transpose()
        self.df_teams_table = new_df

        self.df_teams_table = self.__objectify()

    def from_duty_table(self):
        """ Formats a schedule dataframe in a pandas dataframe containing all teams"""
        
        df_duty_table = DutyTable("sql")
        df_duty_table = df_duty_table.df_duty_table

        keys = list(df_duty_table.keys())
        table1_index = keys.index("table1")
    
        data = {}
        # if team already in dict, append. Else create new key.
        for index, row in df_duty_table.iterrows():
            for player in range(table1_index, table1_index + 11, 2):

                if pd.isna(row[player]) == True:
                    continue

                if row[player] == "":
                    continue

                if row[player + 1] in data.keys():

                    if row[player] in data[row[player + 1]]:
                        continue
                    else:
                        data[row[player + 1]].append(row[player])

                else:
                    data[row[player + 1]] = [row[player]]

        # create dataframe
        new_df = pd.DataFrame.from_dict(data, orient="index")
        new_df = new_df.transpose()

        self.df_teams_table = new_df

        self.df_teams_table = self.__objectify()

    def create_playerduties_table(self):
        """fff"""
        
        try:
            self.df_teams_table.iloc[0,0].name

        except:
            self.__objectify()

        df_players = pd.DataFrame({"player":[],"total":[],"tables":[],"referee":[]})

        for index, row in self.df_teams_table.iterrows():
            for player in row:
                if pd.isna(player):
                    continue

                if player == "":
                    continue

                df_temp = pd.DataFrame({"player":[player.name],"total":[player.duties],"tables":[player.table],"referee":[player.referee]})
                df_players = df_players.append(df_temp)

        df_players = df_players.astype({"total": int, "tables": int, "referee":int})


        return df_players

    def create_teamduties_table(self):
        """dfdfd"""

        try:
            self.df_teams_table.iloc[0,0].name

        except:
            self.__objectify()

        df_teams = pd.DataFrame({"team":[],"total":[],"tables":[],"referee":[], "dut_gam":[], "games":[]})

        for team in self.df_teams_table.keys():

            if pd.isna(team):
                continue

            if team == "":
                continue

            df_temp = pd.DataFrame({"team":[team.name],"total":[team.duties],"tables":[team.table],"referee":[team.referee], "dut_gam":[team.duties / team.games], "games":[team.games]})
            df_teams = df_teams.append(df_temp)

    
        df_teams = df_teams.astype({"total": int, "tables": int, "referee":int, "games":int})
        df_teams = df_teams.round({"dut_gam":3})

        return df_teams

    def __objectify(self):
        """ Turn the names of the teams dataframe into objects"""

        # Retrieve username
        df_duty_table = DutyTable("sql")

        self.__teams_to_column(df_duty_table.df_duty_table)
        self.__players_to_table(df_duty_table.df_duty_table)
        return self.df_teams_table

    def __teams_to_column(self, df_duty_table):
        """ Turn the columns into TeamName objects"""

        for team in range(len(self.df_teams_table.columns)):

            # Determine the totals of the team
            table_total = (df_duty_table[["team_table1", "team_table2", "team_table3", "team_zaalco"]] == self.df_teams_table.columns[team]).sum().sum()
            referee_total = (df_duty_table[["team_referee1", "team_referee2"]] == self.df_teams_table.columns[team]).sum().sum()
            games_total = (df_duty_table[["hometeam"]] == self.df_teams_table.columns[team]).sum().sum()

            # Change the column into an object
            self.df_teams_table = self.df_teams_table.rename(columns={self.df_teams_table.columns[team]: TeamName(self.df_teams_table.columns[team])})
            
            # retrieves the object variables
            self.df_teams_table.columns[team].duties = table_total + referee_total
            self.df_teams_table.columns[team].table = table_total
            self.df_teams_table.columns[team].referee = referee_total
            self.df_teams_table.columns[team].games = games_total
            self.df_teams_table.columns[team].length = len(self.df_teams_table[self.df_teams_table.columns[team]].dropna())

    def __players_to_table(self, df_duty_table):
        """ Turn the cells into PlayerName objects"""

        for index, row in self.df_teams_table.iterrows():
        
            # Go over every player in the row
            for player in range(len(row)):
                if pd.isna(self.df_teams_table.iloc[index, player]):
                    continue

                # Calculate the total numbers of table_duty and referee
                table_total = (df_duty_table[["table1", "table2", "table3", "zaalco"]] == row[player]).sum().sum()
                referee_total = (df_duty_table[["referee1", "referee2"]] == row[player]).sum().sum()

                # Make an object out of an player
                self.df_teams_table.iloc[index, player] = PlayerName(self.df_teams_table.iloc[index, player], self.df_teams_table.columns[player].name)

                # When player exists, import numbers
                self.df_teams_table.iloc[index, player].duties = table_total + referee_total
                self.df_teams_table.iloc[index, player].table = table_total
                self.df_teams_table.iloc[index, player].referee = referee_total


class DutyTable:
    """ Operations that include the duties table"""

    def __init__(self, method, df_game_schedule=None, df_teams_table=None, df3=None):
        if method == "sql":
            self.from_sql()
        elif method == "scratch":
            self.from_scratch(df_game_schedule, df_teams_table, df3)
        return

    def from_sql(self):

        # Retrieve username
        username = get_username()

        # read duty table
        self.df_duty_table = pd.read_sql("""SELECT username, day, time, hometeam, awayteam, table1, team_table1, 
                                        table2, team_table2, table3, team_table3, zaalco, team_zaalco, 
                                        referee1, team_referee1, referee2, team_referee2 FROM
                                        schedule WHERE username = :username""", conn, 
                                        params={"username": username[0]})

    def from_scratch(self, df_game_schedule, df_teams_table, df3):
        
        self.df_duty_table = self.__create_duty_table() # Creates an empty duty table dataframe

        # makes a list containing all the days.
        df_slice = GameSchedule.days(df_game_schedule)

        # Duties are assigned per day
        for day in df_slice:
            
            self.__create_schedule(df_game_schedule, df_teams_table, day)

            # Assigns duties to the players
            self.__duty_assigner(df_game_schedule, df_teams_table, df3, 'table')
            self.__duty_assigner(df_game_schedule, df_teams_table, df3, 'referee')
        return
    
    def to_sql(self):

        try:
            self.df_duty_table.to_sql("schedule", conn, if_exists='append', index=False)
        except sqlite3.IntegrityError:
            flash("A game has been added twice, all changes are discarded")
        return


    def __create_duty_table(self):
        data = {"username":[],"day":[],"time":[],"hometeam":[],"awayteam":[],"table1":[],
            "team_table1":[],"table2":[],"team_table2":[],"table3":[],"team_table3":[],
            "zaalco":[],"team_zaalco":[],"referee1":[],"team_referee1":[],"referee2":[],
            "team_referee2":[]}
        df_duty_table = pd.DataFrame(data)
        return df_duty_table

    def __create_schedule(self, df_game_schedule, df_teams_table, day):

        # The schedule of the current day
        self.__schedule = df_game_schedule[df_game_schedule["Datum"] == day].drop_duplicates().reset_index(drop=True)

        # Makes sure everything is appended in the right row
        if self.df_duty_table.empty == True:
            self.__last_row = 0
        else:
            self.__last_row = self.df_duty_table.iloc[-1].name + 1

        self.__day = day # The current day 
        self.__add_game_data() # adds information of the current day
        self.__add_timeslot_column_to_schedule() # adds a column with a timeslot
        self.__assign_team_to_timeslot(df_teams_table) # A team is assigned to a timeslot
        return

    def __add_game_data(self):
        username = get_username()
        for index, row in self.__schedule.iterrows():
            self.df_duty_table.loc[index + self.__last_row, "username"] = username[0]
            self.df_duty_table.loc[index + self.__last_row, "day"] = row["Datum"]
            self.df_duty_table.loc[index + self.__last_row, "time"] = row["Tijd"]
            self.df_duty_table.loc[index + self.__last_row, "hometeam"] = row["Thuisteam"]
            self.df_duty_table.loc[index + self.__last_row, "awayteam"] = row["Uitteam"]
        return

    def __add_timeslot_column_to_schedule(self):
        """ timeslot starts at 0. +1 with each timechange """

        # Creates a list containing all the times
        df_time = self.__schedule["Tijd"].drop_duplicates().reset_index(drop=True)

        # Creates a column with all timeframe indexes
        self.__schedule["Timeframe"] = 0
        for index, row in self.__schedule.iterrows():
            for i in range(len(df_time)):
                if row["Tijd"] == df_time[i]:
                    self.__schedule.loc[index, "Timeframe"] = i
        return

    def __assign_team_to_timeslot(self, df_teams_table):
        """ Assigns a timeslot to a team. 
        Also renames several team names so that team names are equal in all 
        the dataframes. 
        Also counts the amount of games of each team"""

        # Resets the timeslots
        for team in df_teams_table.keys():
            team.timeframe_backup = -5
            team.timeframe = -5

        for index, row in self.__schedule.iterrows():
            for team in df_teams_table.keys():
                if team.name in row["Thuisteam"]:
                    self.__schedule.loc[index, "Thuisteam"] = team.name
                    self.df_duty_table.loc[index + self.__last_row, "hometeam"] = team.name
                    team.games += 1
                    team.change()
                    team.timeframe_backup = row["Timeframe"]
                if team.name in row["Uitteam"]:
                    self.__schedule.loc[index, "Uitteam"] = team.name
                    self.df_duty_table.loc[index + self.__last_row, "awayteam"] = team.name
                    team.games += 1
                    team.change()
                    team.timeframe_backup = row["Timeframe"]
        return

    def __duty_assigner(self, df_game_schedule, df_teams_table, df3, duty):
        """ Assigns referee/table duties to the right people and teams.
        """

        for index, row in self.__schedule.iterrows():
        
            # timeslot is reset
            for team in df_teams_table.keys():
                team.timeframe = team.timeframe_backup

            # Checks whether a zaalco is needed for this game
            zaalco = self.__check_zaalco(duty, index)

            # Amount of duties needed for this game
            if duty == "referee":
                max_duties = df3.loc[1, row["Thuisteam"]] + zaalco
            else:
                max_duties = df3.loc[0, row["Thuisteam"]] + zaalco

            # Assigns the duties
            for i in range(max_duties):
              
                team = self.__select_team(df_teams_table.keys(), row["Timeframe"])
                if team == None:
                    break # No more duties will be added to the game

                player = self.__select_player(df_teams_table, team, duty)
                if player == None:
                    team.timeframe = -5 # This prevents the team from being selected again
                    continue

                self.__append_player_to_duty(duty, player, team, zaalco, index) # player is added to the duty table
                self.__count_duties(team, player, duty) # Either table or referee duties are counted for team and player.
                continue

    def __check_zaalco(self, duty, index):
        """Checks whether a zaalco is needed for the game"""

        # A zaalco is not needed for the last timeslot.
        zaalco = False if self.__schedule.loc[index, "Timeframe"] == self.__schedule["Timeframe"].max() else True
           
        # A zaalco is only needed ones every timeslot
        try:
            if self.__schedule.loc[index, "Timeframe"] == self.__schedule.loc[index -1, "Timeframe"]:
                zaalco = False
        except:
            pass

        # Putting in referee duties, does not require zaalco
        if duty == "referee":
            zaalco = False

        return zaalco

    def __select_team(self, teams, timeframe):
        """ Select the team to add the duty to """

        team_order = sorted(teams, key=operator.attrgetter('duties'))
        team_order = sorted(team_order, key=operator.attrgetter('amount'))
        for team in team_order:
            
            # Selects the first team that plays in the timeframe
            # Only the teams who play before or after the timeframe are selected
            timeframe_difference = timeframe - team.timeframe
            if (timeframe_difference == 1 or timeframe_difference == -1):
                # Team gets assigned a duty
                return team
       
        return None

    def __select_player(self, df_teams_table, team, duty):
        """ Select player from player_list who doesn't have a duty"""

        # Sort the player_list on duties
        # Player with least duties gets duty assigned

        player_list = pd.Series.tolist(df_teams_table[team].dropna())

        player_list.sort(key=operator.attrgetter(duty))
        player_list.sort(key=operator.attrgetter('duties'))

        for player in player_list:

            # check if player in table
            df_day = self.df_duty_table[self.df_duty_table["day"] == self.__day]
            player_in_list = df_day.isin([player]).any(axis=None)

            # If player not in dutytable, select it.
            if player_in_list == False:
                return player

        # If no player can be selected, return error
        return None

    def __append_player_to_duty(self, duty, player, team, zaalco, index):
        """appends the player to a duty from the duty table"""

        if duty == "referee":

            if pd.isna(self.df_duty_table.loc[index + self.__last_row, "referee1"]) == True:
                self.__append_to_duty("referee1", player, team, index)

            elif pd.isna(self.df_duty_table.loc[index + self.__last_row, "referee2"]) == True:
                self.__append_to_duty("referee2", player, team, index)

        elif duty == "table":

            if zaalco == True:
                if pd.isna(self.df_duty_table.loc[index + self.__last_row, "zaalco"]) == True:
                    self.__append_to_duty("zaalco", player, team, index)
                    return

            if pd.isna(self.df_duty_table.loc[index + self.__last_row, "table1"]) == True:
                self.__append_to_duty("table1", player, team, index)

            elif pd.isna(self.df_duty_table.loc[index + self.__last_row, "table2"]) == True:
                self.__append_to_duty("table2", player, team, index)

            elif pd.isna(self.df_duty_table.loc[index + self.__last_row, "table3"]) == True:
                self.__append_to_duty("table3", player, team, index)
        return

    def __append_to_duty(self, duty, player, team, index):

        self.df_duty_table.loc[index + self.__last_row, duty] = player.name
        self.df_duty_table.loc[index + self.__last_row, "team_{}".format(duty)] = team.name
        return

    def __count_duties(self, team, player, duty):
        """ Either table or referee duties are counted"""
        player.duties += 1
        team.duties += 1
        team.duties_corrected += 1
        team.change()
        if duty == 'table':
            team.table += 1
            player.table += 1
        elif duty == 'referee':
            team.referee += 1
            player.referee += 1
        return


class TeamName:

    timeframe = -5 # the timeframe a team plays 
    timeframe_backup = -5
    duties = 0 # the max amount of duties
    duties_corrected = 0 # duties corrected for length of team
    table = 0 # the amount of table duties
    referee = 0 # the amount of referee duties
    games = 0  # Amount of games played
    amount = 0 # First 0, later duties/games/length of team
    length = 0 # The length of a team

    def __init__(self, name):
        self.name = name

    def change(self):
        if self.games == 0:
            self.amount = 0
        else:
            self.amount = self.duties_corrected / self.games / self.length


class PlayerName:

    def __init__(self, name, team):
        self.name = name
        self.team = team

    duties = 0
    table = 0
    referee = 0


class GameSchedule:
    """ Operations with the gameschedule dataframe"""

    def delete_away_games(df_game_schedule):

        for index, row in df_game_schedule.iterrows():
            cond1 = any(name in row["Thuisteam"] for name in ('De Groene Uilen', 'Moestasj'))
            if cond1 == False:
                df_game_schedule.drop(index, inplace=True)
        df_game_schedule = df_game_schedule.reset_index(drop=True)

        return df_game_schedule

    def change_time_format(df_game_schedule):
        """ Change the time format"""

        # Turns the date into datetime type with time
        df_game_schedule['Datum'] = pd.to_datetime(df_game_schedule['Datum']).dt.date

        # Turns the time into a string and delete the unnecessary slot for seconds
        df_game_schedule["Tijd"] = df_game_schedule["Tijd"].astype(str)
        for index, row in df_game_schedule.iterrows():
            df_game_schedule.loc[index, "Tijd"] = row["Tijd"][0:5]

        return df_game_schedule

    def days(df_game_schedule):
        """ Return only the days of the gameschedule"""

        df_days = df_game_schedule["Datum"].drop_duplicates()
        df_days = df_days.reset_index(drop=True)

        return df_days


def create_duty_amounts():
    """ Create the table and referees amount dataframe"""

    data_df3 = {"De Groene Uilen MSE 7":[2,2], "De Groene Uilen MSE 6":[2,2], "De Groene Uilen MSE 5":[3,2],
        "De Groene Uilen MSE 4":[3,0],"De Groene Uilen MSE 3":[3,0],"De Groene Uilen MSE 2":[3,0],
        "De Groene Uilen MSE 1":[3,0],"De Groene Uilen VSE 6":[2,2],"De Groene Uilen VSE 5":[2,2],
        "De Groene Uilen VSE 4":[3,0],"De Groene Uilen VSE 3":[3,0],"De Groene Uilen VSE 2":[3,0],
        "De Groene Uilen VSE 1":[3,0], "Moestasj MSE 3":[2,2],"Moestasj MSE 2":[2,2],
        "Moestasj MSE 1":[3,2],"Moestasj VSE 1":[3,0]}
    df3 = pd.DataFrame(data_df3)
    
    return df3