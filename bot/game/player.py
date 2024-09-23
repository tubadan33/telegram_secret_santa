class Player:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.role = None  # player's role, e.g. "niceist", "naughtist", or "santa"
        self.party = None  # player's party affiliation, e.g. "niceist" or "naughtist"
        self.alive = True  # if the player is still alive in the game

    def assign_role(self, role):
        self.role = role
        self.party = "niceist" if role == "niceist" else "naughtist"

    def kill(self):
        self.alive = False
