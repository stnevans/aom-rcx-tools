# Age of Mythology Extended Edition Recorded Game Analyzer
This is a python library capable of extracting data from recorded Age of Mythology Extended Edition games. This library can determine the players of a game, how long the game lasted, and the winners of the game. This library also provides all commands that were created during the game. This could allow for more analysis on what strategies are effective.

## Planned Improvements
- Support Age of Mythology: The Titans
- Add more fields to commands. Currently many commands are parsed but their fields either ignored or no information on the contents of those fields is given. This will primarily require more reverse engineering.
- Add builtin parsing for commands that have fields such as protoUnitIds. Automatically translate that into the name if wanted.
- Reverse engineer exactly how the selected units are used and add that once understood.
- Longterm goal: Support svx files. No idea what the file format there is.