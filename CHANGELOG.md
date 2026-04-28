# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.8] - 2026-04-28
### Changed
- Upgraded lxml to 6.1.0

## [1.0.7] - 2026-03-14
(Author: https://github.com/pauloliragtz, PR: https://github.com/k3karthic/bitwarden-to-keepass/pull/21)
### Added
- Add patch functionality to update an existing keepass vault with new entries from bitwarden.

### Fixed
- Fix pyproject.toml after uv upgrade (Author: https://github.com/pauloliragtz, PR: https://github.com/k3karthic/bitwarden-to-keepass/pull/21)

## [1.0.6] - 2026-03-14
### Changed
- Replaced poetry with uv

## [1.0.5] - 2026-01-04
### Changed
- Use session key instead of passing password as input to commands

## [1.0.4] - 2025-10-19
### Changed
- Change format of OTP in keepass vault is BitWarden only stores the secret (Author: https://github.com/fed1337)

## [1.0.3] - 2025-01-06
### Added
- Add support for SSH keys (item type 5).
- Add support for reading JSON from stdin via the `-` argument.

## [1.0.2] - 2025-01-05
- Handle vault with no folders

## [1.0.1] - 2024-03-10
- Update dependencies
- Add check for null group

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
