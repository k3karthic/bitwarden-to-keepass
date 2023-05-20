# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2023-05-20
- Support TOTP
- Migrate from setup.py to pyproject.toml

## [0.1.9] - 2023-04-23
- Handle null uri field

## [0.1.8] - 2022-05-05
- Sync argument no longer requires a boolean value

## [0.1.7] - 2022-05-02
- Bugfix - support for installing using pip

## [0.1.6] - 2022-04-16
- Added option to sync the vault before export
- Added option to export the vault as an unencrypted json file

## [0.1.5] - 2022-02-07
- Renamed executable to bw2kp when installed via pip or setup.py
- Added setup.py

## [0.1.4] - 2021-12-05
- Project reorganization
### Added
- Support for different Bitwarden entry types (login, card, identity, secure note)

## [0.1.3] - 2021-12-05
### Added
- Resolve duplicate entries by adding a suffix to the title.

## [0.1.2] - 2021-11-28
### Added
- Support for using a local json export of bitwarden vault.

## [0.1.1] - 2021-11-21
### Added
- Support for specifying master password in environment variable BITWARDEN_PASS.

## [0.1.0] - 2021-07-09
Initial Release
