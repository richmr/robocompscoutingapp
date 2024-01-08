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
- The classes for scoring items have to be applied to the tapped element itself.  Not the divs.  I think this will limit my background feedback.  But this can't be perfect.
- Need to generate fully formed template file when asked
- DB of file inputs that have been validated?  Validate should be separate command to get feedback
- Config file also?  With the API key and eventID?  Generated auto?  It really could be in the markup file.  But we shouldn't need to remake a markup file for each event.  Yes, TOML I think with set up assistance
- Mode shift should, maybe, hide and show those items with data-onlyForMode?
- I can separate logic for the mechanics part of the scoring and the animation
    - Option setting to not set animation, already set by the team
- Command line setting of static files directory?  Defaults to the package.  Easier to just tell people to edit the static dir?
- I think if no "head" is found, then it adds the desired one.
- The code that is added is only for the scoring mechanics.  Formatting and other effects are left to the user.
- The template is a fully formed and realized version
- Test mode to check visuals needed.  Scoring JS checks for presence of test=True param
- Need parsers for all important sections.
- Two real choices here are:
    - User makes just the scoring section to define what is scored and the rest are filled in with an assumed skeleton.css format
    - User makes all sections and the app just handles the communication.
- The JS added by the app does NOT do animation unless set with a flag by user?  Nah needs to be in template.
- Killing the review and submit.  Too much to automate.. at first
- The error modal is up to user..  code will call window.submission_error?.(message).. up to display code to handle..
- Actually needs to be a try..catch to print instructions to the console.
- Provide a QR hook for the user to call if they want the QR code...

### Added classes (scoring)
- scoring: user defined scoring section 
- game_mode_group: So game modes can be mutually exclusive selected (superfluous?  Game mode can just be last selected)
- game_mode: ID the game mode DIVs
    - When game_mode changes, tallies and yes/no must be reset
- attr: data-modename: Official name of the mode, referenced by data-onlyForMode below
- score_tally: designate a tally score item
- attr: data-scorename: item name is defined in data-scorename attr
- score_flag: designate a true/false score item (default false)
- attr: data-onlyForMode: should define modes this can be tallied/registered for (tied to the defined "data-modename" attribute in the .game_mode)
- report_submit: the button that sends it

### Added classes (natch selection)
- match_and_team_selection: where the match selection div will be added, if not give, will put at front of body
- match_selector: specifically for a select element; available options will be loaded here
- team_selector: specifically for a select element; available options loaded here
- Think I will need predefined callbacks on team picked for users to hook into
    - window.function?.(vars) will call a function but not error if it doesn't work.  pretty cool

### Added classes (tank)
- review_and_submit: Where the autogenerated review and submit will be placed (will be auto-appended if missing)
- error_modal: place holder for error messages (auto-append)
- sending_data_modal: place holder for the (auto-append)
- click_feedback: Will change the background color of this element when it's immediate descendent is clicked

### Commands
- validate: simple check to make sure required fields are there
    - If pass it stores the hash as validated
    - Files that don't pass don't make the table
- prepare - X 
    - Takes the user file, 
    - adds the server functional code,
        - No. Checks for correct script tag to load the functional code
        - Well the initial script might just be a loader?
        - That may be a winner and allow for test loads (https://www.educative.io/answers/how-to-dynamically-load-a-js-file-in-javascript) 
    - stores the file in the server location
        - This won't work.. will break relationship between pages/js/css
        - Perhaps named by the hash?
    - toml file stores the name of the file to serve
- test
    - Gui only - Just serves it with some fake data to make sure the gui works
    - Automated - Injects JS that tests the scoring functions (complicated, selenium needed)
    - Allows submission but its all fake data (test.db)
- configure X - not needed due to initialize
    - Event ID
    - API key
    - scoring file
    - location of the static folder 
    - saves toml
- load_data
    - Allow for manual load of team lists and match data?
- run
    - Runs server in daemon mode (unless turned off)
    - Per items in configure
    - Requires the event ID and the First API
    - Checks the cwd for the TOML

- initialize
    - Basically prints the template to stdout, redirect to save
    - No more.  Generates a whole directory structure with a template
    - And a db folder for the actual scoring data?
    - Maybe a minimum template also?  Just the basics with comments for other things to add
    - Sets TOML with blanks for Event ID, API key, full path to the user's static files
    - Dir structure:
        |- rcsa_config.toml
        |- static
            |- js/
            |- css/
            |- images/
            |- database/xxx.db
            |- scoring.html
            |- readme.txt
    - Done
- data_dump - X
    - Will dump CSV for the last event that was deployed
    - No..  leave the file where it is, users can deal with the db file on their own
- data_clean
    - Functions to clean the data out of the db?
- Example
    - Full working example with my preferred design and animations
    - Generates a whole directory structure but filled in (basically Charged Up)
    - Fully working out the gate
- Intended flow:
    - Initialize
    - Validate
    - test
    - run
    - stop (daemon)


### Tables
- Validated user files
    - PK: hash of file
    - validated: bool
    - prepared: bool
    - tested: bool
- DB are dynamically named after the hash of the source file
- Check the table design from before

### JS tips
- https://stackoverflow.com/questions/4146502/jquery-selectors-on-custom-data-attributes-using-html5

### Possible libraries
- https://github.com/Colepng/frc-api

### run
- integrates data in the scoring page to the tables
    - Checks scoring page was validated: no = error
    - Adds modes and scoring items for this validated page, sets to integrated
- Starts server and begins listening
- I think the test 

Need test data load
### API
- Get the mode and item ids 
- Send scoring
- 

## Assumptions
- A scoring server assumes an event is scored with a single scoring page design, resetting the data for an event will delete all existing scores.

- test mode setting on server with API for remote check

- I don't think I need BEGIN_SCORING class and button.  Flow works fine after match and team selection

- Need "Clear saved scores" button on Send Scores in case the scoring page changes during an event?
