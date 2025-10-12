import constants.GameStrings

gameStrings = constants.GameStrings.HalloweeenGameStrings

playerSets = {
    # only for testing purposes
    3: {
        "roles": [gameStrings["Fascist"], gameStrings["Fascist"], gameStrings["Hitler"]],
        "track": [None, None, "policy", "kill", "kill", "win"],
    },
    # only for testing purposes
    4: {
        "roles": [gameStrings["Fascist"], gameStrings['Liberal'], gameStrings["Fascist"], gameStrings["Hitler"]],
        "track": [None, None, "policy", "kill", "kill", "win"],
    },
    5: {
        "roles": [gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Fascist"],
                  gameStrings["Hitler"]],
        "track": [None, None, "policy", "kill", "kill", "win"],
    },
    6: {
        "roles": [gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Fascist"],
                  gameStrings["Hitler"]],
        "track": [None, None, "policy", "kill", "kill", "win"],
    },
    7: {
        "roles": [gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Fascist"],
                  gameStrings["Fascist"],
                  gameStrings["Hitler"]],
        "track": [None, "inspect", "choose", "kill", "kill", "win"],
    },
    8: {
        "roles": [gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Fascist"],
                  gameStrings["Fascist"],
                  gameStrings["Hitler"]
                  ],
        "track": [None, "inspect", "choose", "kill", "kill", "win"],
    },
    9: {
        "roles": [gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Fascist"],
                  gameStrings["Fascist"],
                  gameStrings["Fascist"],
                  gameStrings["Hitler"]
                  ],
        "track": ["inspect", "inspect", "choose", "kill", "kill", "win"],
    },
    10: {
        "roles": [gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Liberal"],
                  gameStrings["Fascist"],
                  gameStrings["Fascist"],
                  gameStrings["Fascist"],
                  gameStrings["Hitler"]
                  ],
        "track": ["inspect", "inspect", "choose", "kill", "kill", "win"],
    },
}

policies = [
    gameStrings["Liberal"],
    gameStrings["Liberal"],
    gameStrings["Liberal"],
    gameStrings["Liberal"],
    gameStrings["Liberal"],
    gameStrings["Liberal"],
    gameStrings["Fascist"],
    gameStrings["Fascist"],
    gameStrings["Fascist"],
    gameStrings["Fascist"],
    gameStrings["Fascist"],
    gameStrings["Fascist"],
    gameStrings["Fascist"],
    gameStrings["Fascist"],
    gameStrings["Fascist"],
    gameStrings["Fascist"],
    gameStrings["Fascist"],
]
