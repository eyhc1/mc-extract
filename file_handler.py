import os, requests, shutil, json


def main():
    # version to extract
    mc_version = "1.17.1"
    # destination directory where your files will be extracted to. Default is created a folder 'MCDEfault_<Version
    # Name> under the Download folder. Tested working on Windows and Mac
    target_path = os.path.join(os.path.expanduser("~"), "Downloads", f"MCDefault_{mc_version}")
    # '.minecraft' folder where all game files has stored. Default is whatever Mojang uses
    mc_dir = get_mc_default_path()

    parse_assets(find_version(mc_version, mc_dir, dest=target_path), mc_dir, target_path)
    print('Done!')


def find_version(version: str, mc_path: str, dest: str = os.path.join(os.getcwd(), "MCDefault")):
    """
    find the appropriate asset json from the given version in the version json
    :param dest: Optional, destination for the file extracted to. This parameter is mainly used when need to download
    assets from web. Default value is to create a folder "MCDefault" in the same directory as this program file.
    :param version: The minecraft version you want, such as 1.16.5
    :param mc_path: minecraft game folder to check everything
    :return: a json about asset indexes, such as 1.16 in the case of 1.16.5. raise ValueError if there is no versions
    found matches the give one, or just download from web if is a valid version but not installed yet
    """
    if not os.path.exists(os.path.join(mc_path, "versions", version, f"{version}.json")):
        print(f"Downloading {version} from web since it does not exist locally")
        download_assets(version, dest)
        print("Done!")
        exit()

    versions_json = json.load(open(os.path.join(mc_path, "versions", version, f"{version}.json"), "r"))
    if "inheritsFrom" in versions_json.keys():
        versions_json = json.load(open(
            os.path.join(mc_path, "versions", versions_json["inheritsFrom"], f"{versions_json['inheritsFrom']}.json"),
            "r"))
    base_version = versions_json["assets"]
    return os.path.join(mc_path, "assets", "indexes", base_version + ".json")


def parse_assets(input_file: str, mc_path: str, dest: str):
    assert ".json" in os.path.split(input_file)[-1], "No json file found!"
    missing_list = {"version": os.path.split(input_file)[-1].replace(".json", ""), "files": {}}
    d = json.load(open(input_file, "r"))["objects"]
    for k, v in d.items():
        destination = os.path.join(dest, *os.path.split(k)[0].split("/"))
        path = os.path.join(mc_path, "assets", "objects", v["hash"][:2])
        filename = os.path.split(k)[-1]
        file = v["hash"]

        if not os.path.exists(os.path.join(path, file)):
            try:
                print("Attempting to fix the missing game file " + file + " from path " + path)
                s = requests.Session()
                s.trust_env = None  # Handling broken ssl
                download_asset(path, file, file, s)
            except (ConnectionError, TimeoutError, requests.HTTPError, requests.RequestException):
                print("\033[91mERROR: Download failed! Adding missing file to the list.")
                missing_list["files"][k] = v["hash"]
                continue
        print(f'looking for {file} at {destination}')
        if not os.path.exists(os.path.join(destination, filename)):
            print(f'Copying {file} to {destination}')
            if not os.path.exists(destination):
                os.makedirs(destination)
            shutil.copy(os.path.join(path, file), destination)
            print("renaming file to " + filename)
            os.rename(os.path.join(destination, os.path.split(file)[-1]), os.path.join(destination, filename))

    if len(missing_list["files"]) != 0:
        open("MissingFiles.json", "w").write(json.dumps(missing_list, indent=4))
        # print("You have missing file(s) from the game directory. Please refer to 'MissingFiles.json' generated right"
        #       " next to this program!")
        print("\033[93mWARNING: You have missing file(s) from the game directory and failed to recovered. Please "
              "refer to 'MissingFiles.json generated right next to this program!")


def download_assets(version: str, local_path: str):
    """
    download assets from Mojang's server
    :param version: input versions
    :param local_path: destination where all files will be extracted to
    :raise AssertionError: the input version is not valid
    """
    version_url = None
    session = requests.Session()
    session.trust_env = None  # Handle broken ssl
    for i in session.get("https://launchermeta.mojang.com/mc/game/version_manifest_v2.json").json()["versions"]:
        if version in i["id"]:
            version_url = i["url"]
    # input a wrong version
    assert version_url, "Invalid or unsupported version"

    items = session.get(session.get(version_url).json()["assetIndex"]["url"]).json()["objects"].items()
    total = len(items)
    curr_progress = 0
    for k, version in items:
        dirs = k.split("/")
        curr_progress += 1
        download_asset(os.path.join(os.getcwd(), local_path, *dirs[:-1]), dirs[-1], version["hash"], session)
        print(
            'downloading ' + version["hash"] + " as " + dirs[-1] + "..." + str(curr_progress) + " out of " + str(total))


def download_asset(dest: str, filename: str, h: str, s: requests.sessions.Session):
    os.makedirs(dest, exist_ok=True)
    open(os.path.join(dest, filename), "wb").write(
        s.get(f'https://resources.download.minecraft.net/{h[:2]}/{h}').content)


def get_mc_default_path():
    # Windows
    if os.name == "nt":
        return os.path.join(os.getenv('APPDATA'), ".minecraft")
    # Mac&Linux
    elif os.name == "posix":
        mac = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "minecraft")
        linux = os.path.join(os.path.expanduser("~"), ".minecraft")
        return mac if os.path.exists(mac) else linux
    else:
        print("WARNING: Cannot determine the default path, creating one locally instead")
        return os.path.join(os.getcwd(), "MCDefaults")


if __name__ == '__main__':
    main()
