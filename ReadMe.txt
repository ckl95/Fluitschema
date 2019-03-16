------------ Basketball Duties Generator----------
--------------------------------------------------

Basketball Duties Generator is a webapp that generates a duty schedule which includes 
table duty, 'zaalcommisaris', and the referees. A schedule can be seen through a html table
that is ordened by week. Furthermore, the amount of duties by each player and team can be
downloaded as an excel file. The input requires an excel file that can be downloaded on the
website. 

Requirements:

- An excel file that includes the teams, game schedule and amount of table duties and referees
  for each team, as can be found on the website.

How to use:

- In the 'teams' sheet, the teams are put above the black line. The players are then put below
  their respectable teams.

- The 'schedule' sheet requires you to fill in the week and date in the right cells, as can be 
  seen in the template.

- Two teams at the same time should be put in the same cell and be seperated by an ', '. 
  Note: It is not possible to schedule two opposing teams in the same cell. One team should
  then be omitted.

- The 'duties' sheet requires you to fill in the duties for each team. First amount of table 
  duty, below amount of referees.

- You can add new weeks to an existing saved duty schedule, however past saved weeks should be
  omitted. Adding teams to an already existing week is not possible either.

Features:

- It creates html tables for the duty schedules and it creates an excel file for further 
  statistics.

- If it is not possible to fill up an duty, the cell in the html table is left empty.

- Schedules are ordened per week.

Known Limitations:

- The program doesn't have a delete function at the moment, so be careful what you upload.
  Contact the host and/or create an new account after an mistake.

- As mentioned above, can't add teams to an existing week, and it is not possible to schedule
  two opposing teams.

- Passwords are not well protected. Don't use bank account passwords etc.

- Due to faulty programming, the program can only handle one query at a time, but this is not
  correctly programmed, so multiple queries may break the program. Or give a wrong output

- It does not feature multiple years. So a second year needs to be added from another account.



