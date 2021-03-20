from typing import List, Any, Dict, Tuple

import brawlstats
from collections import defaultdict

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImUyZDEyY2U5LWU2MDYtNDg3YS1hNDI1LWQyM2M5NTM2MTA0OCIsImlhdCI6MTYxNjIyMzc4MCwic3ViIjoiZGV2ZWxvcGVyL2FhNGVlZDUxLWMwOTgtZTU5Yi02ODUyLTMxYjUyOWZjNWQ4OSIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMTM3LjEzMi4yMTMuNDIiXSwidHlwZSI6ImNsaWVudCJ9XX0.8a-cLL1PumYNQO-0fNue2QmHbhnRwRQDfVIG-Ilm6pQyN82C8gn-UXL8rkCP-oassE_d0WGld0cbc8sTADgqzg"
client = brawlstats.Client(token, prevent_ratelimit=True)

# get all battles in battle log
battles_raw = client.get_battle_logs('J9C0CGJU')
battles = list(filter(lambda x: "type" in x.battle and "Ranked" in x.battle.type, battles_raw))
all_games = defaultdict(list)
ME = '#J9C0CGJU'


def extract_player_tags(battle):
    out: list[str] = []
    for team in battle.battle.teams.to_list():
        for player in team:
            out.append(player["tag"])
    return tuple(out)


for battle in battles:
    tags = extract_player_tags(battle)
    all_games[tags].append(battle)

pl_games = dict(filter(lambda elem: len(elem[1]) > 1, all_games.items()))

# read latest time from sheets then filter by those that start after latest time

to_write = []


# game_counter = get next number to count

def get_teams(game):
    friends_lst, enemies_lst = [], []
    match = game[0]
    for battle in match.battle.teams:
        team = dict([(player.tag, (player.brawler.name, player.brawler.trophies)) for player in battle])
        if ME in team.keys():
            friends: dict[str, tuple[str, str]] = team.copy()
        else:
            enemies: dict[str, tuple[str, str]] = team.copy()
    friends_lst.extend(friends[ME])
    del friends[ME]
    for pair in friends.values():
        friends_lst.extend(pair)
    for pair in enemies.values():
        enemies_lst.extend(pair)
    return friends_lst, enemies_lst


'''for game in pl_games:
    # gametime
    # game_counter += 1
    friends, enemies = get_teams(game)

    for match in game:
        game_write = [game_counter]
        game_write.append(match.battle_time)
        game_write.append(match.event.mode)
        game_write.append(match.event.map)
        game_write.extend(friends)
        game_write.extend(enemies)
        game_write.append(match.battle.result)'''
