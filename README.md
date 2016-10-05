# turbo-carnival
Visualizes Rocket League Replays

## Sample usage (Windows):


### Step 0

Obtain [octane](https://github.com/tfausak/octane/releases) and put it in your PATH.

### Step 1

```bash
octane < "%USERPROFILE%\Documents\My Games\Rocket League\TAGame\Demos\A12FC5C047140DC453037F8869B38900.replay" | python rocket_league_replay_decode.py > sample_data\demo.csv
```

### Step 2

Open visualize.html in a web browser
