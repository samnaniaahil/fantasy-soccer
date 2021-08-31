// Generate suggested search list when user searches for players
function searchList() {
    let player = document.getElementById('pname').value.toLowerCase();

    if (player.length == 0) {
        document.getElementById('players-list').style.display = "none";
        return;
    }

    document.getElementById('players-list').style.display = "list-item";
    let button = document.getElementsByClassName('players-name-btn');

    for (let i = 0; i < button.length; i++) {
        len = player.length;
        let item = JSON.stringify(button[i].innerText);

        // Get player name which is from the beginning to the comma
        sepIndex = item.indexOf(', ');
        let name = item.substring(0, sepIndex).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase(); // Remove accents

        if (name.includes(player)) {
            button[i].style.display = "";
        }
         
        else {
            button[i].style.display = "none";
        }
    }
}


// Style columns in team.html based on number of players in user's team
document.addEventListener('DOMContentLoaded', function() {
    positionTypes = ["Goalkeeper", "Defender", "Midfielder", "Forward"];
    for (let i = 0; i < positionTypes.length; i++) {
        players = document.getElementsByClassName("team-col-" + positionTypes[i]);
        for (let j = 0; j < players.length; j++) {
            players[j].style.width = String(100 / players.length) + "%";
        }
    }
});