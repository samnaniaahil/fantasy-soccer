# Fantasy Soccer

#### Description
A full-stack web app that replicates the [Fantasy Premier League](https://fantasy.premierleague.com/) -- a fantasy soccer game for the [English Premier League](https://en.wikipedia.org/wiki/Premier_League) (England's top-flight football league). Players earn points each gameweek, during which each player plays one game. At the end of each gameweek, a player's points and other stats are updated. Each player's points are summed up to get a user's points total.

#### Features
* View in-depth player stats for over 500 players and their most recent news (e.g. injuries, illness, suspensions).
* Add and delete players from your fantasy team to earn (and potentially lose) points. 
* Customize your fantasy team to any formation.
* View how many points your fantasy team has on a leaderboard of all the app's users.
* View your transfer history (i.e. a history of the players you've added and deleted to your team).

## Image Gallery
#### Player Stats
![Player Stats Screenshot](https://drive.google.com/uc?export=view&id=11G0NzSz667Fx3sKfzwApVTjS6odQJO78)
#### Team
| Desktop | Mobile |
| --- | --- |
| ![Player Stats Screenshot](https://drive.google.com/uc?export=view&id=1ri-bWxVzuHhyWYzRsmPTiMt9Pt3hSWfD) | ![Player Stats Screenshot](https://drive.google.com/uc?export=view&id=1lcAb0iQNuRL6wUgy2LSLUT6Kawyp6Yl5) |
#### League
![League Screenshot](https://drive.google.com/uc?export=view&id=120EwVe6sNbFl7O3HiNcQerjryD3HffYa)
#### Transfer History
![Transfer History Screenshot](https://drive.google.com/uc?export=view&id=1elv3DcnApjXDMr2rmjIO8CWhMX3oJ9PF)

## File Breakdown
<details>
	<summary>File Breakdown</summary>
	<table>
		<tr>
			<th>app.py</th>
			<th>app.py</th>
		</tr>
		<tr>
			<td>App controller</td>
			<td>Helper Functions</td>
		</tr>
	</table>
	Templates
	<table>
		<tr>
			<th>history.html</th>
			<th>index.html</th>
			<th>layout.html</th>
			<th>league.html</th>
			<th>login.html</th>
			<th>player.html</th>
			<th>players.html</th>
			<th>register.html</th>
			<th>team.html</th>
		</tr>
		<tr>
			<td>Display a table of user's transfer history</td>
			<td>App homepage</td>
			<td> Base layout for each page</td>
			<td>Display leaderboard</td>
			<td>Login page</td>
			<td>Display player info and stats</td>
			<td>Search for players page</td>
			<td>Register page</td>
			<td>Display players in team</td>
		</tr>
	</table>
	Static
	<table>
		<tr>
			<th>styles.css</th>
			<th>styles.js</th>
		</tr>
		<tr>
			<td>App's stylesheet</td>
			<td>App's Javascript functions</td>
		</tr>
	</table>
</details>
