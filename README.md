# Age of Mythology Recorded Game Analyzer
This is a python library capable of extracting data from recorded Age of Mythology games. This library can determine the players of a game, how long the game lasted, and the winners of the game. This library also provides all commands that were created during the game. This could allow for more analysis on what strategies are effective. Currently it supports Aom:EE and AoT. 

## Planned Improvements
- Add more fields to commands. Currently many commands are parsed but their fields either ignored or no information on the contents of those fields is given. This will primarily require more reverse engineering.
- Add builtin parsing for commands that have fields such as protoUnitIds. Automatically translate that into the name if wanted.
- Reverse engineer exactly how the selected units are used and add that once understood.
- Longterm goal: Support svx files. No idea what the file format there is.

## Example usage:
```
rec = Rec("/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/savegame/"+"Replay v2.8 @2022.09.15 174819.rcx")
rec.parse(print_progress=True)
rec.analyze_updates()
rec.display_by_teams()
print("Game time " + rec.game_time_formatted())
```
## Example output
```
Parsing progress: 13.54%
Parsing progress: 26.84%
Parsing progress: 40.21%
Parsing progress: 53.54%
Parsing progress: 66.90%
Parsing progress: 80.34%
Parsing progress: 93.73%
Finished reading everything!
Stoud(Zeus) clicked Hunting Dogs at 0:23
Stoud(Zeus) clicked Age 2 Athena at 3:33
Standard(Ra) clicked Age 2 Bast at 3:58
Stoud(Zeus) clicked Pickaxe at 4:08
Standard(Ra) clicked Plow at 4:58
Stoud(Zeus) clicked Hand Axe at 5:23
Standard(Ra) clicked Husbandry at 5:48
Standard(Ra) clicked Medium Axemen at 6:04
Stoud(Zeus) clicked Medium Infantry at 7:13
Stoud(Zeus) clicked Husbandry at 7:37
Stoud(Zeus) clicked Medium Archers at 8:47
Standard(Ra) has resigned
Team #1 - [Stoud(Zeus)]
Team #2 - [Standard(Ra)]
Team #1 has won
Game time 10:02
```

## Example output of analyze_by_group
```
Zeus won 75% out of 4 games
Poseidon won 50% out of 6 games
Ra won 66% out of 3 games
Loki won 100% out of 1 games
Kronos won 0% out of 1 games
Oranos won 0% out of 1 games
Gaia won 100% out of 2 games
```

## Things to configure
At the top of parser.py these variables are used to find the aom files.

`AOM_PATH = "/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/"`<br>
`AOM_VERSION = "2.8"`

Another common AOM_PATH might be `C:\Program Files (x86)\Steam\steamapps\common\Age of Mythology\`

## Known issues
- If someone loses in a manner other than resigning we can't detect their loss
- We can't detect if someone actually researched something or just clicked on it. Not sure if it's possible to do so at all.

## Todo
- Verify games with observers work properly. As of now, I think the player names/civs may be incorrect. To be fair, the Aom:EE also has a bug where you start as the wrong player in (some?) recorded games with observers.
