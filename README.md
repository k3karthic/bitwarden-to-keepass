# Convert BitWarden Vault to a KeePass Database (kdbx)

[Python](https://www.python.org/) script to convert a [BitWarden](https://bitwarden.com/) Vault into a [KeePass](https://keepassxc.org/) Database.

## Requirements

Software required to run the script,
* [Python 3](https://www.python.org/download/releases/3.0/)
* [BitWarden CLI](https://bitwarden.com/help/article/cli/)

## Design

The script invokes the BitWarden CLI using the Python [subprocess](https://docs.python.org/3/library/subprocess.html) module. It performs the following conversions on the configured BitWarden Vault,
* [BitWarden folders](https://bitwarden.com/help/article/folders/) into [KeePass groups](https://keepassxc.org/docs/KeePassXC_UserGuide.html#_application_layout).
* [BitWarden items](https://bitwarden.com/help/article/managing-items/) into [KeePass entries](https://keepassxc.org/docs/KeePassXC_UserGuide.html#_adding_an_entry).

### Drawbacks

BitWarden supports many URIs for an entry while [PyKeePass](https://github.com/libkeepass/pykeepass#adding-entries) only supports a single URI. The script only copies the first URI into the KeePass database. 

## Building

Install the dependencies of the script using [pip](https://pypi.org/project/pip/),
```
pip install -r requirements.txt
```

## Running

Run the script using the following command,
```
python convert.py -o <path to output kdbx>
```

You need to provide your BitWarden vault password only once at the start.

![screenshot of run](https://github.com/k3karthic/bitwarden-to-keepass/raw/main/assets/screenshot.png)
