""" Converts excel table to html table.
    Excel table should have a particular order:
    Date, Referee 1, Referee 2, Table 1, Table 2, Table 3, Court manager, Time, Home team, Away team
"""


import pandas as pd
import datetime
import numpy as np

def to_html_file_writer(df, f):
    """ Writes the html file out of the pandas dataframe"""

    background_color = "tg-white_row"
    _insert_headers(df, f, 0)
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

        if type(df.iloc[i, 0]) == pd._libs.tslibs.timestamps.Timestamp and i != 0:
                f.write("\n</table>\n".encode("utf-8"))
                background_color = "tg-white_row"
                _insert_headers(df, f, i)


        ## Time formatting 
        try:
            time = df.iloc[i,7].strftime("%H.%M")
        except AttributeError:
            time = ""

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
            time,
            df.iloc[i,8],
            df.iloc[i,9],
            table,
            df.iloc[i,6],
            ref,
            background_color).encode("utf-8"))

    f.write("\n</table>".encode("utf-8"))

def _insert_headers(df, f, i):
    
    # html of the date
    try:
        f.write("""<hr><b><font color = "Green">Tafelschema/Table duty {}</font></b>""".format(df.iloc[i, 0].strftime("%d %B")).encode("utf-8"))
    # If the date is a string; no present
    except AttributeError:
        f.write("""<hr><b><font color = "Green">Tafelschema/Table duty</font></b>""".encode("utf-8"))

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



def format_file(df):
    """ Puts the newly created pandas dataframe into the right format
    for to_html_file_writer to work"""
    
    # Delete empty columns and rows
    df = df.dropna(how='all', axis=1) # Columns
    df = df.dropna(how='all', axis=0) # Rows
    df = df.reset_index(drop=True)


    # Add an empty 'Date' column if no dates have been given on the first row or column. To match the required format.
    bool_1 = df[df.iloc[:,0].apply(lambda x: type(x) == datetime.datetime)].empty
    bool_2 = df[df.iloc[:,0].apply(lambda x: type(x) == pd._libs.tslibs.timestamps.Timestamp)].empty
    bool_3 = (type(df.columns[0]) != pd._libs.tslibs.timestamps.Timestamp and type(df.columns[0]) != datetime.datetime)
    if bool_1 and bool_2 and bool_3:
        df.insert(0,"Date","")


    # Turns all the time data types into datetime.time
    ## 1. Turns everything first into a string
    df.iloc[:,7] = df.iloc[:,7].astype(str)
    for index, row in df.iterrows():
        # Prevents '19.3' becoming datetime(19.03)
        if df.iloc[index,7][-2] == ".":
            df.iloc[index,7] = df.iloc[index,7] + "0"

    ## 2. Then, turns the string into datetime.time
    ls = []
    for index, row in df.iterrows():
        try:
            df.iloc[index,7] = datetime.datetime.strptime(df.iloc[index,7], '%H.%M').time()
        except ValueError:
            try:
                df.iloc[index,7] = datetime.datetime.strptime(df.iloc[index,7], '%H:%M:%S').time()
            except ValueError:
                # Delete headers
                bool_4 = type(df.iloc[index,7]) == str and df.iloc[index,7] != "nan" and df.iloc[index,7] != " " and df.iloc[index,7] != "\\r\\n"
                bool_5 = type(row[0]) != pd._libs.tslibs.timestamps.Timestamp and type(row[0]) != datetime.datetime
                if bool_4 and bool_5:
                    ls.append(index)
                else:
                    df.iloc[index,7] = ""
    ## 3. Drops the selected rows containing headers
    for i in ls:
        df = df.drop(i)
    df = df.reset_index(drop=True)


    # If no headers have been given in xlsx sheet, pandas headers should probably be the first row.
    if df.columns[7][0] == "1" or df.columns[7][0] == "2" or df.columns[7] == "Unnamed: 7":
        df.index = df.index + 1
        df.loc[0] = df.columns.tolist()
        df = df.sort_index()


    # Make sure the dates are on the first row of every day
    for index, row in df.iterrows():
        if (type(row[0]) == pd._libs.tslibs.timestamps.Timestamp or type(row[0]) == datetime.datetime) and pd.isna(row[7]) == True:
            df.iloc[index+1,0] = row[0]
            df.iloc[index,0] = np.nan
    df = df.dropna(how='all', axis=0) # Rows
    df = df.reset_index(drop=True)

    ## The first day gets the name of the column if the column is a date
    if type(df.columns[0]) == pd._libs.tslibs.timestamps.Timestamp or type(df.columns[0]) == datetime.datetime:
        df.iloc[0,0] = df.columns[0]


    # Delete rows with no hometeam and date
    for index, row in df.iterrows():
        if (type(row[0]) != pd._libs.tslibs.timestamps.Timestamp and type(row[0]) != datetime.datetime) and pd.isna(row[8]) == True:
            df = df.drop(index)
    df = df.reset_index(drop=True)
    

    # Turns NaN into empty strings
    df = df.fillna('')
    df = df.replace(regex=r'^Unnamed:.*$', value="")
    return df