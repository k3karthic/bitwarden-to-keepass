# Convert BitWarden Vault to a KeePass Database (kdbx)

The [Python](https://www.python.org/) script in this repository converts a [BitWarden](https://bitwarden.com/) Vault into a [KeePass](https://keepassxc.org/) Database.

## Requirements

The following software is required to run the script,
* [Python 3](https://www.python.org/download/releases/3.0/)
* [BitWarden CLI](https://bitwarden.com/help/article/cli/)

## Design

The script invokes the BitWarden CLI using [subprocess](https://docs.python.org/3/library/subprocess.html) and exports the folders and items stored. [BitWarden folders](https://bitwarden.com/help/article/folders/) are converted to [KeePass groups](https://keepassxc.org/docs/KeePassXC_UserGuide.html#_application_layout) and [BitWarden items](https://bitwarden.com/help/article/managing-items/) are converted into [KeePass entries](https://keepassxc.org/docs/KeePassXC_UserGuide.html#_adding_an_entry).

### Drawbacks

BitWarden supports multiple URIs for an entry while [PyKeePass](https://github.com/libkeepass/pykeepass#adding-entries) only supports a single URI. During conversion, only the first URI of an entry is copied into the KeePass database.

## Building

The dependencies of the script can be installed using [pip](https://pypi.org/project/pip/),
```
pip install -r requirements.txt
```

## Running

The script can be run using the following command,
```
python convert.py -o <path to output kdbx>
```

You will be prompted for your BitWarden vault password only once at the start.

![screenshot of run](https://github.com/k3karthic/bitwarden-to-keepass/raw/main/assets/screenshot.png)
