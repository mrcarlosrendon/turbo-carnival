"""
Puts Rocket League replay metadata into DynamoDB

Requires: https://github.com/tfausak/octane

Usage: 

octane < [replay] | python put_metadata_in_dynamo.py 

"""
import sys
import json
import boto3
             
def parse():
    replay_json = json.load(sys.stdin)
    metadata = replay_json['Metadata']    
    replay_id = metadata['Id']['Value']
    team_size = metadata['TeamSize']['Value']
    team0_score = metadata['Team0Score']['Value']
    team1_score = metadata['Team1Score']['Value']
    replay_map = metadata['MapName']['Value']
    replay_date = metadata['Date']['Value']
    players = []
    for player in metadata['PlayerStats']['Value']:
        name = player['Name']['Value']
        ranking = player['Score']['Value']
        online_id = player['OnlineID']['Value']
        platform = player['Platform']['Value']
        players.append({'name': name, 'ranking': ranking,
                        'online_id': online_id, 'platform': platform})        
    print(replay_id)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('turbo-carnival')
    print("inserting")
    resp = table.put_item(
        Item={
            'replay_key': replay_id,
            'team_size': team_size,
            'team0_score': team0_score,
            'team1_score': team1_score,
            'replay_map': replay_map,
            'replay_date': replay_date,
            'players': players
        }
    )
    print("done")
    print(resp)    
parse()
