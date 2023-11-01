class Player:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.role = None  # player's role, e.g. "liberal", "fascist", or "hitler"
        self.party = None  # player's party affiliation, e.g. "liberal" or "fascist"
        self.alive = True  # if the player is still alive in the game

    def assign_role(self, role):
        self.role = role
        self.party = 'liberal' if role == 'liberal' else 'fascist'

    def kill(self):
        self.alive = False