""" Converts excel table to html table.
    Excel table should have a particular order:
    Date, Referee 1, Referee 2, Table 1, Table 2, Table 3, Court manager, Time, Home team, Away team
"""


import pandas as pd
import datetime
import numpy as np

def format_file(df):
    """ Puts the newly created pandas dataframe into the right format
    for to_html_file_writer to work"""
    

    # Delete unneccesary rows
    for index, row in df.iterrows():
        ## Rows not containing a time or a date are deleted 
        if (type(row[0]) != pd._libs.tslibs.timestamps.Timestamp and type(row[0]) != datetime.datetime) and pd.isna(row[7]) == True:
            df = df.drop(index)
    df = df.reset_index(drop=True)

    # If no headers have been given
    if df.columns[7][0] == "1":
        df.index = df.index + 1
        df.loc[0] = df.columns.tolist()
        df = df.sort_index()

    # Making the first row the headers
    # With Unnamed: 9, it is expected the whole row is empty
    # With Unnamed: 8, it is expected the date is on the first row
    if df.columns[4] == "Unnamed: 4" and (type(df.columns[0]) == pd._libs.tslibs.timestamps.Timestamp or type(df.columns[0]) == datetime.datetime):
        temp = df.columns[0]

    if df.columns[0] == "Unnamed: 0" or df.columns[4] == "Unnamed: 4":
        df.columns = df.iloc[0,:].tolist()
        df = df.drop(0)
        df = df.reset_index(drop=True)
        try:
            df = df.rename(columns={df.columns[0]:temp})
        except NameError:
            pass
        df = df.reset_index(drop=True)

    # Make sure the dates are on the first row of the day
    for index, row in df.iterrows():
        if (type(row[0]) == pd._libs.tslibs.timestamps.Timestamp or type(row[0]) == datetime.datetime) and pd.isna(row[7]) == True:
            df.iloc[index+1,0] = row[0]
            df.iloc[index,0] = np.nan

    # Delete any more unneccesary rows
    for index, row in df.iterrows():
        ## Rows not containing a time or a date are deleted 
        if (type(row[0]) != pd._libs.tslibs.timestamps.Timestamp and type(row[0]) != datetime.datetime) and pd.isna(row[7]) == True:
            df = df.drop(index)

    # The first day gets the name of the column if the column is a date
    if type(df.columns[0]) == pd._libs.tslibs.timestamps.Timestamp or type(df.columns[0]) == datetime.datetime:
        df.iloc[0,0] = df.columns[0]   

    df = df.reset_index(drop=True)

    # Turns all the time data types into datetime.time
    df.iloc[:,7] = df.iloc[:,7].astype(str)
    for index, row in df.iterrows():
        try:
            df.iloc[index,7] = datetime.datetime.strptime(df.iloc[index,7], '%H.%M').time()
        except ValueError:
            try:
                df.iloc[index,7] = datetime.datetime.strptime(df.iloc[index,7], '%H:%M:%S').time()
            except ValueError:
                print("Error")
                exit
    
    # Turns NaN into empty strings
    df = df.fillna('')

    return df


def to_html_file_writer(df, f):
    """ Writes the html file out of the pandas dataframe"""

    # html of the body; filled in per row
    for i in range(len(df)):

        ## Is the row a green or white row?
        if i > 0: 
            ### If time of game is different then the previous time, switch color
            if df.iloc[i, 7] != df.iloc[i-1, 7]:
                if background_color == "tg-white_row":
                    background_color = "tg-green_row"
                elif background_color == "tg-green_row":
                    background_color = "tg-white_row"

        if type(df.iloc[i, 0]) == pd._libs.tslibs.timestamps.Timestamp:
            if i != 0:
                f.write("\n</table>\n".encode("utf-8"))
            background_color = "tg-white_row"
            _insert_headers(df, f, i)

        ## Table duty formatting
        table = df.iloc[i,3] + ", " + df.iloc[i,4]
        ### Is there a third table duty person assigned?
        if df.iloc[i,5] == "":
            table = table + ", " + df.iloc[i,5]

        ## ref formatting
        ref = df.iloc[i,1] + ", " + df.iloc[i,2]
        if ref ==  "Bond, Bond" or ref == ", " or ref == "Bond, " or ref == "bond, bond" or ref == "bond, ":
            ref = "Bond"

        ## html of the row
        f.write("""
  <tr class="{6}">
    <td>{0}</td>
    <td>{1} - {2}</td>
    <td>{3}</td>
    <td>{4}</td>
    <td>{5}</td>
  </tr>""".format(
            df.iloc[i,7].strftime("%H.%M"),
            df.iloc[i,8],
            df.iloc[i,9],
            table,
            df.iloc[i,6],
            ref,
            background_color).encode("utf-8"))

    f.write("\n</table>".encode("utf-8"))

def _insert_headers(df, f, i):
    
    # html of the date
    f.write("""<hr><b><font color = "Green">Tafelschema/Table duty {}</font></b>""".format(df.iloc[i, 0].strftime("%d %B")).encode("utf-8"))

    # html of the headers
    f.write("""
<table class="tg">
  <tr>
    <th class="tg-time">Time</th>
    <th class="tg-game">Game</th>
    <th class="tg-tacmre">Table Duty</th>
    <th class="tg-tacmre">Court Manager</th>
    <th class="tg-tacmre">Referees</th>
  </tr>""".encode("utf-8"))
