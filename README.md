# RoboCompScoutingApp

[![PyPI - Version](https://img.shields.io/pypi/v/robocompscoutingapp.svg)](https://pypi.org/project/robocompscoutingapp)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/robocompscoutingapp.svg)](https://pypi.org/project/robocompscoutingapp)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install robocompscoutingapp
```

## License

`robocompscoutingapp` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Thoughts
- App started by calling a HTML file that is the "skin" of the scoring page
- Scorable elements are marked with a specific class in the element that turns them into tally-able items
- Two starting scoring items are "Yes/No (did a thing, did not), and incrementable tally"
- The spreadsheet analysis pages may not be skinnable
- The scoring page should have the match and team selection added in automatically
- Review and submit should auto build, reproducing the text and or icons used in the skin
- Code injections marked with "easy to find" markers for test verification
- Team and match data from the FRC events API?
- Need packaged test data and a test mode from cli
- references to needed engine javascript added to end
- Required cli entries:
    - first_events_API_key: The team's registered API key
    - first_event_ID: The first event we want to load and score (used to populate team database)
- Have to figure out what to do with skeleton vs. not skeleton; advanced users can replace?

### Added classes

- match_selection: where the match selection div will be added, if not give, will put at front of body
- review_and_submit: Where the autogenerated review and submit will be placed (will be auto-appended if missing)
- error_modal: place holder for error messages (auto-append)
- sending_data_modal: place holder for the (auto-append)
- scoring: user defined scoring section 
- game_mode_group: So game modes can be mutually exclusive selected
- game_mode: ID the game mode DIVs
    - When game_mode changes, tallies and yes/no must be reset
- score_tally: designate a tally score item
- item name is defined in data-scorename attr
- score_flag: designate a true/false score item (default false)
- data-onlyForMode: should define modes this can be tallied/registered for (tied to the defined "id" attribute in the .game_mode)

