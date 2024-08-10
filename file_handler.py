import os, sys, requests, shutil, json, time
import rich_click as click
import rich.traceback
from rich.progress import (
    Progress,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TextColumn,
)
from rich import print

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)  # supress warning
rich.traceback.install()


@click.command(help="Extract Minecraft assets from the game files")
@click.option(
    "--mc_version",
    "-v",
    required=True,
    help="The version of Minecraft you want to extract assets from",
)
@click.option(
    "--target_path",
    "-p",
    help="The destination where all files will be extracted to. Default is ~/Downloads/MCDefault_{mc_version}",
)
@click.option(
    "--mc_dir",
    "-d",
    help="The .minecraft folder where all game files has stored. Default is whatever Mojang uses",
)
def main(mc_version: str, target_path: str = None, mc_dir: str = None):
    if not target_path:
        target_path = os.path.join(
            os.path.expanduser("~"), "Downloads", f"MCDefault_{mc_version}"
        )
    if not mc_dir:
        mc_dir = get_mc_default_path()
    version = find_version(mc_version, mc_dir, dest=target_path)
    if version:
        parse_assets(version, mc_dir, target_path)
    else:
        print(f"Downloading {mc_version} from web since it does not exist locally")
        download_assets(mc_version, target_path)
    print("Done!")


def find_version(
    version: str, mc_path: str, dest: str = os.path.join(os.getcwd(), "MCDefault")
):
    """
    find the appropriate asset json from the given version in the version json
    :param dest: Optional, destination for the file extracted to. This parameter is mainly used when need to download
    assets from web. Default value is to create a folder "MCDefault" in the same directory as this program file.
    :param version: The minecraft version you want, such as 1.16.5
    :param mc_path: minecraft game folder to check everything
    :return: a json about asset indexes, such as 1.16 in the case of 1.16.5. None if there is no versions
    found matches the give one
    """
    if not os.path.exists(
        os.path.join(mc_path, "versions", version, f"{version}.json")
    ):
        return None
    versions_json = json.load(
        open(os.path.join(mc_path, "versions", version, f"{version}.json"), "r")
    )
    if "inheritsFrom" in versions_json.keys():
        versions_json = json.load(
            open(
                os.path.join(
                    mc_path,
                    "versions",
                    versions_json["inheritsFrom"],
                    f"{versions_json['inheritsFrom']}.json",
                ),
                "r",
            )
        )
    base_version = versions_json["assets"]
    return os.path.join(mc_path, "assets", "indexes", base_version + ".json")


def parse_assets(input_file: str, mc_path: str, dest: str):
    assert ".json" in os.path.split(input_file)[-1], "No json file found!"
    missing_list = {
        "version": os.path.split(input_file)[-1].replace(".json", ""),
        "files": {},
    }
    d = json.load(open(input_file, "r"))["objects"]
    for k, v in d.items():
        destination = os.path.join(dest, *os.path.split(k)[0].split("/"))
        path = os.path.join(mc_path, "assets", "objects", v["hash"][:2])
        filename = os.path.split(k)[-1]
        file = v["hash"]

        if not os.path.exists(os.path.join(path, file)):
            try:
                print(
                    "Attempting to fix the missing game file "
                    + file
                    + " from path "
                    + path
                )
                s = requests.Session()
                s.trust_env = None  # Handling broken ssl
                download_asset(path, file, file, s)
            except (
                ConnectionError,
                TimeoutError,
                requests.HTTPError,
                requests.RequestException,
            ):
                print(
                    "\033[91mERROR: Download failed! Adding missing file to the list."
                )
                missing_list["files"][k] = v["hash"]
                continue
        print(f"looking for {file} at {destination}")
        if not os.path.exists(os.path.join(destination, filename)):
            print(f"Copying {file} to {destination}")
            if not os.path.exists(destination):
                os.makedirs(destination)
            shutil.copy(os.path.join(path, file), destination)
            print("renaming file to " + filename)
            os.rename(
                os.path.join(destination, os.path.split(file)[-1]),
                os.path.join(destination, filename),
            )

    if len(missing_list["files"]) != 0:
        open("MissingFiles.json", "w").write(json.dumps(missing_list, indent=4))
        print(
            "\033[93mWARNING: You have missing file(s) from the game directory and failed to recovered. Please "
            "refer to 'MissingFiles.json generated right next to this program!"
        )


def download_assets(
    version: str, local_path: str, verify: bool = False, trust_env: bool = False
):
    """
    download assets from Mojang's server
    :param version: input versions
    :param local_path: destination where all files will be extracted to
    :raise AssertionError: the input version is not valid
    """
    version_url = None
    session = requests.Session()
    # Handle broken ssl
    session.verify = verify
    session.trust_env = trust_env
    for i in session.get(
        "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
    ).json()["versions"]:
        if version in i["id"]:
            version_url = i["url"]
    # input a wrong version
    assert version_url, "Invalid or unsupported version"

    items = (
        session.get(session.get(version_url).json()["assetIndex"]["url"])
        .json()["objects"]
        .items()
    )

    progress = Progress(
        TextColumn(
            "[bold blue]Downloading {task.fields[name]} as {task.fields[filename]}"
        ),
        BarColumn(bar_width=None),
        TextColumn(
            "[bright_cyan]({task.completed} out of {task.total})", justify="right"
        ),
        TaskProgressColumn(justify="right", show_speed=True),
        TimeRemainingColumn(compact=True),
        expand=True,
    )
    with progress:
        task = progress.add_task("", filename="", name="", total=len(items))
        for k, version in items:
            dirs = k.split("/")
            progress.update(task, advance=1, filename=dirs[-1], name=version["hash"])
            download_asset(
                os.path.join(os.getcwd(), local_path, *dirs[:-1]),
                dirs[-1],
                version["hash"],
                session,
            )


def download_asset(
    dest: str, filename: str, h: str, s: requests.sessions.Session, respawn_cd: int = 2
):
    os.makedirs(dest, exist_ok=True)
    done = False
    while not done:
        try:
            response = s.get(
                f"https://resources.download.minecraft.net/{h[:2]}/{h}", timeout=5
            )
            response.raise_for_status()  # If the response was successful, no Exception will be raised
            open(os.path.join(dest, filename), "wb").write(response.content)
            done = True
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            print(f"Error occurred: {e.strerror} retrying...")
            time.sleep(respawn_cd)  # Wait for `respawn_cd` seconds before retrying


def get_mc_default_path():
    # Windows
    if os.name == "nt":
        return os.path.join(os.getenv("APPDATA"), ".minecraft")
    # Mac&Linux
    elif os.name == "posix":
        mac = os.path.join(
            os.path.expanduser("~"), "Library", "Application Support", "minecraft"
        )
        linux = os.path.join(os.path.expanduser("~"), ".minecraft")
        return mac if os.path.exists(mac) else linux
    else:
        print(
            "WARNING: Cannot determine the default path, creating one locally instead"
        )
        return os.path.join(os.getcwd(), "MCDefaults")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
