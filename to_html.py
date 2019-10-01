""" Converts excel table to html table.
    Excel table should have a particular order:
    Date, Referee 1, Referee 2, Table 1, Table 2, Table 3, Court manager, Time, Home team, Away team
"""


import pandas as pd
import datetime

def to_html_file_writer(df, f):


    # html of the date
    f.write("""<hr><b><font color = "Green">Tafelschema/Table duty {}</font></b>\r\n""".format(df.columns[0].strftime("%d %B")).encode("utf-8"))

    # html of the headers
    f.write("""<table class="tg">\r\n
    <tr>\r\n
        <th class="tg-time">Time</th>\r\n
        <th class="tg-game">Game</th>\r\n
        <th class="tg-tacmre">Table Duty</th>\r\n
        <th class="tg-tacmre">Court Manager</th>\r\n
        <th class="tg-tacmre">Referees</th>\r\n
    </tr>\r\n""".encode("utf-8"))

    # html of the body; filled in per row
    background_color = "tg-white_row"
    for i in range(len(df)):

        ## Is the row a green or white row?
        if i > 0: 
            ### If time of game is different then the previous time, switch color
            if df.iloc[i, 7] != df.iloc[i-1, 7]:
                if background_color == "tg-white_row":
                    background_color = "tg-green_row"
                elif background_color == "tg-green_row":
                    background_color = "tg-white_row"

        ## Table duty formatting
        table = df.iloc[i,3] + ", " + df.iloc[i,4]
        ### Is there a third table duty person assigned?
        if df.iloc[i,5] == "":
            table = table + ", " + df.iloc[i,5]

        ## ref formatting
        ref = df.iloc[i,1] + ", " + df.iloc[i,2]
        if ref ==  "Bond, Bond" or ref == ", " or ref == "Bond, ":
            ref = "Bond"

        ## html of the row
        f.write("""  <tr class="{6}">\r\n
        <td>{0}</td>\r\n
        <td>{1} - {2}</td>\r\n
        <td>{3}</td>\r\n
        <td>{4}</td>\r\n
        <td>{5}</td>\r\n
    </tr>\r\n""".format(
            "{:.2f}".format(df.iloc[i,7]),
            df.iloc[i,8],
            df.iloc[i,9],
            table,
            df.iloc[i,6],
            ref,
            background_color).encode("utf-8"))

    f.write("</table>".encode("utf-8"))