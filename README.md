# minecraft assets extractor
A simple program that will extract Minecraft assets files from its directory and change them into a real resource pack folder, so you can use it to make your own.

## How to use
A Windows executable is compiled as `mcextract.exe` in the release section for Windows users. 
Locate your .minecraft folder and run `file_handler.py --mc_version <version>` (or `mcextract.` if it is using the executable), and replace `<version>` with the game version. Additional options could be found using the `--help` flag. Then run the program. Alternatively, you can directly call `download_assets(version, local_path)` function with `version` being the version you are looking for and `local_path` being the directory where all files will be extracted, preferably an empty folder.
Make sure you have the required packages from `requirements.txt` for it to be installed, or simple install using `pip install -r requirements.txt`
