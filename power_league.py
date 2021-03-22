from typing import List, Dict, Tuple
import brawlstats
import gspread
from dateutil.parser import parse
from time import sleep
from oauth2client.service_account import ServiceAccountCredentials
from collections import defaultdict

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjlhZmNmNjc2LTA1MmMtNGRhZC1hYjExLTY0YzViNjIxNGU1MiIsImlhdCI6MTYxNjQxMTcyOSwic3ViIjoiZGV2ZWxvcGVyL2FhNGVlZDUxLWMwOTgtZTU5Yi02ODUyLTMxYjUyOWZjNWQ4OSIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMTM3LjEzMi4yMTIuMjEiXSwidHlwZSI6ImNsaWVudCJ9XX0.A4pTawYj17we4MnK-O6VefJingkMhrFCLxky50tKPMxrbCmxjlvDXiZ1NuKq_UMBOOL7ff_NJvBnCMRJ13Q8cQ"
client = brawlstats.Client(token, prevent_ratelimit=True)

gamer_tag = "J9C0CGJU"


def get_pl_games(gamer_tag: str, last_time: str) -> defaultdict[Tuple, List]:
    # get all battles in battle log
    battles_raw = client.get_battle_logs(gamer_tag)
    battles = list(filter(lambda x: "type" in x.battle and "Ranked" in x.battle.type, battles_raw))
    pl_games: defaultdict[Tuple, List] = defaultdict(list)

    def extract_player_tags(battle):
        out: List[str] = []
        for team in battle.battle.teams.to_list():
            for player in team:
                out.append(player["tag"])
        return tuple(out)

    for battle in battles:
        if parse(battle.battle_time) > parse(last_time):
            tags = extract_player_tags(battle)
            pl_games[tags].append(battle)
    return pl_games


def get_teams(game: list, friendly_file: str) -> Tuple[List[str], List[str]]:
    def read_friendly_file(filename: str) -> defaultdict:
        d = defaultdict(lambda: "")
        try:
            with open(filename) as f:
                for line in f:
                    (key, val) = line.split()
                    d[key] = val
        finally:
            return d

    friendly_tags = read_friendly_file(friendly_file)
    friends_lst, enemies_lst = [], []
    match = game[0]
    for battle in match.battle.teams:
        team = dict([(player.tag, (player.brawler.name, player.brawler.trophies)) for player in battle])
        if "#" + gamer_tag in team.keys():
            friends: Dict[str, Tuple[str, str]] = team.copy()
        else:
            enemies: Dict[str, Tuple[str, str]] = team.copy()
    friends_lst.extend(friends["#" + gamer_tag])
    del friends["#" + gamer_tag]
    for ID, pair in friends.items():
        new_pair = (pair[0] + friendly_tags[ID], pair[1])
        friends_lst.extend(new_pair)
    for pair in enemies.values():
        enemies_lst.extend(pair)
    return friends_lst, enemies_lst


def create_write_list(pl_games: defaultdict[Tuple, List], counter: int, friendly_file: str) -> List[List[str]]:
    write = []
    games = list(pl_games.values())
    games.reverse()
    for game in games:
        counter += 1
        friends, enemies = get_teams(game, friendly_file)
        for match in game:
            row_write = [counter, match.battle_time, match.event.mode, match.event.map]
            row_write.extend(friends)
            row_write.extend(enemies)
            row_write.append(match.battle.result)
            row_write.append(match.battle.type)
            write.append(row_write)
    return write


# game_counter += 1
def write_to_gsheets(sheet_name, workbook_name, friendly_file):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).worksheet(workbook_name)
    start_row = len(sheet.col_values(1)) + 1
    counter = sheet.cell(start_row - 1, 1).value
    counter = int(counter)
    last_time = sheet.cell(start_row - 1, 2).value
    pl_games = get_pl_games(gamer_tag, last_time)
    write = create_write_list(pl_games, counter, friendly_file)


    def split_into_chunks(lst: List[List[str]], n: int) -> list[list[list[str]]]:
        return [lst[i:i + n] for i in range(0, len(lst), n)]

    write = split_into_chunks(write, 5)

    for chunk in write:
        for row in chunk:
            # update_range = "A" + str(start_row) + ":Q" + str(start_row)
            sheet.insert_row(row, start_row)
            start_row += 1
        sleep(100)
