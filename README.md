# Fighting Game Journey
#### Video Demo:  <https://youtu.be/1D2gxG_H5yk>
#### Description:
This is a web app designed to allow users to keep track of their progress and improvement in the ranked online modes of videogames in the traditional fighting game genre (Eg: Street Fighter).

**Features:**  
- Users can register for an account, and login/logout.
- Users can add a new character to track, or update the data of a character they are currently tracking.
- All updates appear in a history page, where users can also delete entries.
- The index page displays their tracked characters' ranks on line charts, showing their progress over time.
- The currently supported games are Street Fighter 6, and Granblue Fantasy Versus: Rising.

**Add Character Page:**  
This page begins with a form where users can select a game from a select list of supported games. This list is generated from a tabke in a database.
Depending on their game selection, the rest of the form will completely change, as each game has its own unique ranking systems that require different types of data.
To achieve this, the page uses AJAX requests to seamlessly reset the form and repopulate it with a select list of characters from the selected game, and fields to input the ranking data.
The submit button sends a post request, which will verify the user data and insert it into a tracker table.

I didn't know about AJAX requests before this project, but was suggested it by the Duck. The Duck also walked me through making it. I can understand what the code is doing when I read through it line by line, but I wouldn't be able to write it again off the top of my head.
I think I could have achieved the same result without the AJAX request, but it would require sending the entire database every time the user accesses the page. So as the number of supported games increases, a method without an AJAX request might become too slow as the server would send more and more data when the page loads.

**Update Rank Page:**  
This page has a similar form to the Add Character page, only the select list will solely populate with the characters currently being tracked by the user.
When they select a character, the form will reset and display the fields required for the user to update the ranking data.
Once the user clicks the submit button, data is verified on the server side and added to the tracker table.

**History Page:**  
This page is populated with rows for all entries in the tracker table associated with the current user ID. 
The tracker table in the database is largely filled with foreign keys, so the query to populate the page contains several joins.
I encountered an issue where only entries from a single game were being returned by the query. This was due to how different games track rank.
Certain columns would be NULL for characters from other games, and the query ignored them.
By changing one of the JOINs to a JOIN LEFT, the problem was resolved, and now all entries display correctly.
Users can also delete entries from here in the case they make a mistake, or want to stop tracking a character. 
They are prompted before deletion to reduce the risk of accidental deletion.

**Index Page:**  
This page displays all the users ranking updates in plotly line charts. The user's tracked characters are grouped by game.
Initially I tried using a javascript chart, but some games have non-numeric ranks, which I couldn't get to display properly. In my database each of these ranks has a unique numeric ID number, which is what the charts use for the values. But getting the labels to accurately dsplay the non-numeric data was difficult, and never worked exactly as I wanted.
I asked ChatGPT if there was an alternative way to generate the charts, and it recommended plotly.
With plotly I was able to much more easily assign labels to values; however, it's still not what I would ideally like. The y-axis for Granblue Fantasy Versus: Rising is crowded, and while plotly's built-in ability to zoom alleviates it somewhat, I still had to increase the height of the chart to compensate. In a future update, I would like to assign labels to all values, but only display labels at every nth interval.

**Database:**  
My database consists of 5 tabels. 
- Users: Stores usernames and hashed passwords
- Games: Stores supported game titles and abbreviations with unique IDs
- Characters: Stores all characters in supported games, with a game_id foreign key linking back to the game table.
- Rankings: Stores all the rank values in supported games, with a game_id foreign key linking back to the game table.
- Tracker: Records users' updates. The primary key is an entry number, with foreign keys linking back to all other tables.

**Scalability:**  
If a game received an update adding new characters, I would simply need to add them to the character table of the database and everything else would generate from there.
If I were to add a new game, I would potentially need to make some changes to app.py and some of the .html pages to account for the unique ways each game stores rank data. But the code is structured to account for this. It would be a minor addition to the code, but there would not be any changes to existing code.