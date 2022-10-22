# Age of Mythology Recorded Game Manipulator
This is a python library to interact with Age of Mythology recorded game files. It can extract the data contained in recorded games or add an observer to an AoM:EE game. <br>
Some data extracted includes the players of a game, the duration of a game, what commands were created during the game (i.e. player actions), and the winners of the game. This could faciliate statistical analysis (e.g. what is the winrate of a 4:16 up with Zeus on Medit vs a 4:30?). The parser supports both AoM:EE and AoT. <br>
Adding an observer to a game allows a viewer to have fog of war that includes all teams. Adding an observer is implemented by adding a observer player who instantly resigns. This would normally take the game out of sync, so the recorded game is also modified to ignore sync information. While this works on AoM:EE, on AoT, playback seems to go out of sync after the ResignCommand is processed. 


## Planned Improvements
- Better AoT support
- Longterm goal: Support svx files. Some work has been done for this, a ton more is needed.
- Add more fields to commands. Currently many commands are parsed but their fields either ignored or no information on the contents of those fields is given. This will primarily require more reverse engineering.

## Example of adding an observer
```
$ python3 obs_add.py 'Replay v2.8 @2020.11.15 190728.rcx'
Adding observer "Observer(Stu)"
Saved to Replay v2.8 @2020.11.15 190728_obs.rcx
```

## Example Parser Usage:
```
$ python3 parser.py Stoud_VS_Computer.rcx
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


## Example output of Group Analysis
```
Zeus won 75% out of 4 games
Poseidon won 50% out of 6 games
Ra won 66% out of 3 games
Loki won 100% out of 1 games
Kronos won 0% out of 1 games
Oranos won 0% out of 1 games
Gaia won 100% out of 2 games
```

## Things to configure for parser
At the top of parser.py these variables are used to find the aom files.

`AOM_PATH = "/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/"`<br>
`AOM_VERSION = "2.8"`

Another common AOM_PATH might be `C:\Program Files (x86)\Steam\steamapps\common\Age of Mythology\`

## Known issues
- If someone loses in a manner other than resigning we can't detect their loss
- We can't detect if someone actually researched something or just clicked on it. 
- Recs that start from midway during a game are not supported.
## Todo
- Verify games with observers work properly, especially AoT multiple observers. To be fair, the Aom:EE also has a bug where you start as the wrong player in (some?) recorded games with observers.
- Make it so if you disconnect it counts as a loss or game not ended depending on state of other team.
- Make techtree voobly compatible.