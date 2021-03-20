from datetime import date, datetime, timedelta
import brawlstats
import gspread
from dateutil.parser import parse
from dateutil import tz

from oauth2client.service_account import ServiceAccountCredentials

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)
sheet = client.open("Brawl").sheet1

# get row of current day
today = date.today()
start_row = len(sheet.col_values(3)) + 1

'''for idx, date in enumerate(sheet.col_values(3)[3:]):
    dt = parse(date)
    if dt.date() == today:
        start_row = idx + 4
        break'''

# set up brawl stars api client
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjdlZjNjOTRmLTU5MTEtNDA5Zi05NTg5LTM2OGRlYzUyMDRmMyIsImlhdCI6MTYxNDk0MDUwNywic3ViIjoiZGV2ZWxvcGVyL2FhNGVlZDUxLWMwOTgtZTU5Yi02ODUyLTMxYjUyOWZjNWQ4OSIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMTM3LjEzMi4yMjAuNCJdLCJ0eXBlIjoiY2xpZW50In1dfQ.LFkcG0eo2WFMO4SHfrdjuzF_1XOIdASeTXgo9Afy_EMHAadCdre4QXu4BA3b9VBSsMz4_QccxVkSkrmQwmYtOQ"
client = brawlstats.Client(token, prevent_ratelimit=True)

# get all battles in battle log
battles = client.get_battle_logs('J9C0CGJU')

# create list of pp_matches
pp_matches = []
for battle in battles:
    battle_dt = parse(battle['battle_time'])
    time_diff = datetime.now(tz.UTC) - battle_dt

    if battle['battle']['type'] == "proLeague" and time_diff.total_seconds() < 86400:
        pp_matches.append(battle)
pp_matches.reverse()


friendly_col_num = {"shwh": 9, "jeek": 8, "dumes": 10}


def get_player_info(match):
    star_player = match["battle"]["star_player"]["name"]
    friendly = []
    enemy = []

    for team in match["battle"]["teams"]:
        if team[0]["name"] not in friendly_col_num:
            for PLAYER in team:

                # get player info from api client
                tag = PLAYER["tag"]
                p_info = client.get_player(tag)

                # get trophy and brawler info
                trophies = p_info.trophies
                player_brawler = PLAYER["brawler"]["name"]
                name = PLAYER["name"]
                if name == star_player:
                    player_brawler += "*"

                # add to list of enemy players
                info = (player_brawler, trophies)
                enemy.append(info)

        else:
            for PLAYER in team:
                name = PLAYER["name"]
                player_brawler = PLAYER["brawler"]["name"]
                if name == star_player:
                    player_brawler += "*"

                info = (player_brawler, name)
                friendly.append(info)

    return friendly, enemy


win_type = {5: "L", 30: "W", 33: "EW"}

# fills in values for each match row by row
for idx, match in enumerate(pp_matches):
    friendly, enemy = get_player_info(match)

    # update indices and date
    SD = (int(sheet.cell(start_row - 1, 2).value)) % 14 + 1
    date = (parse(sheet.cell(start_row - 1, 3).value, dayfirst=True) + timedelta(days=1)).strftime("%d/%m/%Y")
    sheet.update_cell(start_row + idx, 2, SD)
    sheet.update_cell(start_row + idx, 3, date)
    sheet.update_cell(start_row + idx, 5, idx + 1)

    # update win type and trophy change
    sheet.update_cell(start_row + idx, 12, win_type[match["battle"]["trophy_change"]])
    sheet.update_cell(start_row + idx, 13, match["battle"]["trophy_change"])

    # update friendly player brawler name
    for player in friendly:
        sheet.update_cell(start_row + idx, friendly_col_num[player[1]], player[0])

    # update enemy player brawler name and trophy
    for col_id, player in enumerate(enemy):
        sheet.update_cell(start_row + idx, 2*col_id + 16, player[0])
        sheet.update_cell(start_row + idx, 2*col_id + 17, player[1])

    # update map name, mode, and game time
    sg_tz = tz.gettz("Asia/Singapore")
    match_time = parse(match["battle_time"]).astimezone(sg_tz)
    match_time_str = match_time.strftime("%H%M")
    sheet.update_cell(start_row + idx, 4, match_time_str)
    sheet.update_cell(start_row + idx, 6, match["event"]["mode"])
    sheet.update_cell(start_row + idx, 7, match["event"]["map"])
    sheet.update_cell(start_row + idx, 11, match["battle"]["duration"])
