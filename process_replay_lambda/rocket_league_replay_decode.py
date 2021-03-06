"""
Decodes Rocket League replay JSON output from Octane
Also outputs metadata into DynamoDB

https://github.com/tfausak/octane

Usage: 

octane < [replay] | python rocket_league_replay_decode.py > positions.csv

Output Format:

frame numer, id, x, y, z, yaw, pitch, roll

"""
import os
import sys
import codecs
import traceback
import json
import boto3

from flask import escape

if os.name == 'nt':
    import win_unicode_console
    win_unicode_console.enable()
else:
    # Get's set to ascii when called from subprocess on Linux
    sys.stdout = codecs.getwriter("UTF-8")(sys.stdout)
    
def process_updates(actor_cars, player_names, team_actor_player, updated, players, player_teams):
    for actor_id, value in updated.items():                
        if 'Engine.Pawn:PlayerReplicationInfo' in value:
            player_id = value['Engine.Pawn:PlayerReplicationInfo']['Value']['Int']
            actor_cars[player_id] = actor_id
        if 'Engine.PlayerReplicationInfo:PlayerName' in value:
            name = value['Engine.PlayerReplicationInfo:PlayerName']['Value']
            player_names[int(actor_id)] = name
            for player in players:
                if player['name'] == name:
                    team = player['team']
                    player_teams[int(actor_id)] = player['team']
        if 'Engine.PlayerReplicationInfo:Team' in value:
            team_actor_id = value['Engine.PlayerReplicationInfo:Team']['Value']['Int']
            team_actor_player[int(team_actor_id)] = int(actor_id)

def extract_positions(spawned_or_updated, ball_id, player_names, player_teams, actor_cars):
    positions = []
    for actor_id, value in spawned_or_updated.items():
        if 'TAGame.RBActor_TA:ReplicatedRBState' in value:
            position = value['TAGame.RBActor_TA:ReplicatedRBState']['Value']['Position']
            rotation = value['TAGame.RBActor_TA:ReplicatedRBState']['Value']['Rotation']

            descriptive_id = actor_id
            team = -1

            for player_actor_id, car_actor_id in actor_cars.items():
                if actor_id == car_actor_id:
                    descriptive_id = player_names[player_actor_id]
                    team = player_teams[player_actor_id]
                    break

            if ball_id == actor_id:
                descriptive_id = 'ball'

            pos_dict = {}
            pos_dict['id'] = descriptive_id            
            pos_dict['team'] = team
            pos_dict['x'], pos_dict['y'], pos_dict['z'] = position
            pos_dict['yaw'], pos_dict['pitch'], pos_dict['roll'] = rotation

            positions.append(pos_dict)
    return positions

def print_csv_line(*args):
    line = ""
    for arg in args:
        try:
            line += '"' + unicode(escape(arg)) + '",'
        except:
            traceback.print_exc(file=sys.stderr)
    print(line[0:len(line)-1])

def print_positions_csv(frame_positions, goal_frames):
    team1score = 0
    team2score = 0
    print_csv_line("frame", "id", "team", "x", "y", "z", "yaw", "pitch", "roll", "scorer", "team1score", "team2score")
    for frame, frame_pos in enumerate(frame_positions):
        scorer = ''        
        if goal_frames.has_key(frame):
            scorer = goal_frames[frame]['player']
            team = goal_frames[frame]['team']
            if team == 0:
                team1score = team1score + 1
            else:
                team2score = team2score + 1
        for actor_pos in frame_pos:
            for actor in actor_pos:
                print_csv_line(
                    frame, actor['id'], actor['team'], \
                    actor['x'], actor['y'], actor['z'], \
                    actor['yaw'], actor['pitch'], actor['roll'], \
                    scorer, team1score, team2score
                )

def extract_player_info_from_metadata(replay_json):
    metadata = replay_json['Metadata']
    players = []
    for player in metadata['PlayerStats']['Value']:
        name = player['Name']['Value']
        team = player['Team']['Value']
        ranking = player['Score']['Value']
        online_id = int(player['OnlineID']['Value'])
        platform = player['Platform']['Value'][1]
        players.append({'name': name, 'team': team, 'ranking': ranking,
                        'online_id': online_id, 'platform': platform})
    return players    
    
def extract_goal_frames(replay_json):
    goal_frames = {}
    goals_json = replay_json['Metadata']['Goals']['Value']
    for goal in goals_json:
        frame = goal['frame']['Value']
        team = goal['PlayerTeam']['Value']
        player = goal['PlayerName']['Value']
        goal_frames[frame] = { 'team': team , 'player': player }
    return goal_frames

def getMetadataValueOrDefault(metadata, key, default):
    value = metadata.get(key)
    if value == None:
        return default
    return value.get('Value')    

def put_metadata_in_dynamo(replay_json):
    metadata = replay_json['Metadata']    
    replay_key = metadata['Id']['Value']
    team_size = metadata['TeamSize']['Value']
    team0_score = getMetadataValueOrDefault(metadata, 'Team0Score', '0')
    team1_score = getMetadataValueOrDefault(metadata, 'Team1Score', '0')
    replay_map = getMetadataValueOrDefault(metadata, 'MapName', 'error')
    replay_date = metadata['Date']['Value']
    team0_players = set()
    team1_players = set()
    players = extract_player_info_from_metadata(replay_json)
    for player in players:
        if player['team'] == 0:
            team0_players.add(player['name'])
        else:
            team1_players.add(player['name'])

    if len(team0_players) == 0:
        team0_players = None
    if len(team1_players) == 0:
        team1_players = None

    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('turbo-carnival')
    try:
        data={
                'replay_key': replay_key,
                'team_size': team_size,
                'team0_score': team0_score,
                'team1_score': team1_score,
                'replay_map': replay_map,
                'replay_date': replay_date,
                'players': players,
                'team0_players': team0_players,
                'team1_players': team1_players
            }
        resp = table.put_item(Item=data)
    except:
        traceback.print_exc(file=sys.stderr)

    # TODO, switch to batch requests
    table = dynamodb.Table('turbo-carnival-players')
    for player in players:        
        data={
                    'online_id': player['online_id'],
                    'name': player['name'],
                    'platform': player['platform'],
                    'ranking': player['ranking'],
                    'team': player['team'],
                    'team_size': team_size,
                    'team0_players': team0_players,
                    'team1_players': team1_players,
                    'team0_score': team0_score,
                    'team1_score': team1_score,
                    'replay_key': replay_key,
                    'replay_date': replay_date,
                    'replay_map': replay_map
                }
        try:
            resp = table.put_item(Item=data)
        except:
            traceback.print_exc(file=sys.stderr)

def parse():
    replay_json = json.load(sys.stdin)

    put_metadata_in_dynamo(replay_json)
    players = extract_player_info_from_metadata(replay_json)
    
    # actor_id -> actor
    actors = {}
    # contains only the players
    # actor_id -> actor
    actor_players = {}    
    # player_id -> actor_id
    actor_cars = {}
    # actor_id -> player's String name
    player_names = {'ball':'ball'}
    # team_actor_id -> player_actor_id 
    team_actor_player = {}
    # player_actor_id -> team
    player_teams = {}
    # which actor_id is the ball
    ball_id = -1
    # positions of all items for each frame
    frame_positions = []

    goal_frames = extract_goal_frames(replay_json)
    
    for index, frame in enumerate(replay_json['Frames']):
        this_frame_positions = []

        if not frame.get('Updated') == None:
            process_updates(actor_cars, player_names, team_actor_player, frame['Updated'], players, player_teams)

        if not frame.get('Spawned') == None:
            for actor_id, value in frame['Spawned'].items():
                if actor_id not in actors:
                    actors[actor_id] = value

                if value['Class'] == 'TAGame.Ball_TA':
                    ball_id = actor_id
                    
                if value['Class'] == 'TAGame.PRI_TA':
                    actor_players[actor_id] = value

                if value['Class'] == 'TAGame.Team_Soccar_TA':
                    team = int(value['Name'].replace("Archetypes.Teams.Team", ""))
                    player_actor_id = team_actor_player[int(actor_id)]
                    player_teams[player_actor_id] = team

            this_frame_positions.append(
                extract_positions(frame['Spawned'], ball_id, player_names, player_teams, actor_cars))

        if not frame.get('Destroyed') == None:
            for actor_id in frame['Destroyed']:
                del actors[str(actor_id)]

        if not frame.get('Updated') == None:            
            this_frame_positions.append(
                extract_positions(frame['Updated'], ball_id, player_names, player_teams, actor_cars))
                
        frame_positions.append(this_frame_positions)

    print_positions_csv(frame_positions, goal_frames)

parse()
