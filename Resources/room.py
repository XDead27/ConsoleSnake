import random

class Room:
    def __init__(self, id, name, map, computers, f_input, refresh_rate):
        self.id = id
        self.name = name
        self.map = map
        self.computers = computers
        self.f_input = f_input
        self.refresh_rate = refresh_rate

        self.players = []
        self.host = None  

        self.game_state = 0 

    def insert_player(self, player_settings):
        new_player_id = random.randint(1000, 9999)

        # Do this until we have a new valid player id
        while new_player_id in [a['id'] for a in self.players]:
            new_player_id = random.randint(1000, 9999)
        
        new_player = player_settings
        new_player['id'] = new_player_id

        if self.player_count() == 0:
            self.host = new_player
        self.players.append(new_player)

        return new_player_id

    def remove_player(self, to_remove_id):
        for player in self.players:
            if player.get("id") == to_remove_id:
                self.players.remove(player)
                return

    def player_count(self):
        return len(self.players)

    def host_name(self):
        return self.host.get("name") if self.host else "N/A"

    def json_data(self):
        return {
                "id": self.id,
                "name": self.name,
                "map": self.map,
                "players": self.players,
                "player_count": self.player_count(),
                "computers": self.computers,
                "flush_input": self.f_input,
                "refresh_rate": self.refresh_rate,
                "host": self.host,
                "host_name": self.host_name(),
                "game_state": self.game_state
            }