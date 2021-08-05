# minecraft assets extractor
A simple program that will extract Minecraft assets files from its directory and change it into a real resource pack folder, so you can use it to make your own.

## How to use
locate your .minecraft folder and follow the comments in `file_handler.py` to add the game version, file directory, and the location where you want your files to be. Then simply run the program. Or alternatively you can directly call `download_assets(version, local_path)` function with `version` being the version you are looking for and `local_path` is the directory where all files will extract to, preferably an empty folder.