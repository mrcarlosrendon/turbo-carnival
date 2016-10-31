"""
Decodes Rocket League replay JSON output from Octane

https://github.com/tfausak/octane

Usage: 

octane < [replay] | python rocket_league_replay_decode.py > positions.csv

Output Format:

frame numer, id, x, y, z, yaw, pitch, roll

"""
import sys
import json
import cgi

def update_car_ids(actor_cars, updated):
    for actor_id, value in updated.items():                
        if 'Engine.Pawn:PlayerReplicationInfo' in value:
            player_id = value['Engine.Pawn:PlayerReplicationInfo']['Value']['Int']
            actor_cars[player_id] = actor_id

def extract_positions(spawned_or_updated, ball_id, actor_cars):
    positions = []
    for actor_id, value in spawned_or_updated.items():
        if 'TAGame.RBActor_TA:ReplicatedRBState' in value:
            position = value['TAGame.RBActor_TA:ReplicatedRBState']['Value']['Position']
            rotation = value['TAGame.RBActor_TA:ReplicatedRBState']['Value']['Rotation']

            descriptive_id = actor_id

            for player_actor_id, car_actor_id in actor_cars.items():
                if actor_id == car_actor_id:
                    descriptive_id = player_actor_id
                    break

            if ball_id == actor_id:
                descriptive_id = 'ball'
            
            pos_dict = {}
            pos_dict['id'] = descriptive_id
            pos_dict['x'], pos_dict['y'], pos_dict['z'] = position
            pos_dict['yaw'], pos_dict['pitch'], pos_dict['roll'] = rotation

            positions.append(pos_dict)
    return positions

def print_csv_line(*args):
    line = ""
    for arg in args:
        line += '"' + cgi.escape(str(arg)) + '",'    
    print(line[0:len(line)-1])

def print_positions_csv(frame_positions, goal_frames):
    team1score = 0
    team2score = 0
    print_csv_line("frame", "id", "x", "y", "z", "yaw", "pitch", "roll", "scorer", "team1score", "team2score")
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
                    frame, actor['id'], \
                    actor['x'], actor['y'], actor['z'], \
                    actor['yaw'], actor['pitch'], actor['roll'], \
                    scorer, team1score, team2score
                )

def extract_goal_frames(replay_json):
    goal_frames = {}
    goals_json = replay_json['Metadata']['Goals']['Value']
    for goal in goals_json:
        frame = goal['frame']['Value']
        team = goal['PlayerTeam']['Value']
        player = goal['PlayerName']['Value']
        goal_frames[frame] = { 'team': team , 'player': player }
    return goal_frames
                
def parse():
    replay_json = json.load(sys.stdin)
    # actor_id -> actor
    actors = {}
    # contains only the players
    # actor_id -> actor
    actor_players = {}    
    # player_id -> actor_id
    actor_cars = {}
    # which actor_id is the ball
    ball_id = -1
    # positions of all items for each frame
    frame_positions = []

    goal_frames = extract_goal_frames(replay_json)
    
    for index, frame in enumerate(replay_json['Frames']):
        this_frame_positions = []

        if not frame.get('Updated') == None:
            update_car_ids(actor_cars, frame['Updated'])

        if not frame.get('Spawned') == None:
            for actor_id, value in frame['Spawned'].items():
                if actor_id not in actors:
                    actors[actor_id] = value

                if value['Class'] == 'TAGame.Ball_TA':
                    ball_id = actor_id
                    
                if value['Class'] == 'TAGame.PRI_TA':
                    actor_players[actor_id] = value

            this_frame_positions.append(
                extract_positions(frame['Spawned'], ball_id, actor_cars))

        if not frame.get('Destroyed') == None:
            for actor_id in frame['Destroyed']:
                del actors[str(actor_id)]

        if not frame.get('Updated') == None:            
            this_frame_positions.append(
                extract_positions(frame['Updated'], ball_id, actor_cars))
                
        frame_positions.append(this_frame_positions)

    print_positions_csv(frame_positions, goal_frames)

parse()
