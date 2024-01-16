# RoboCompScoutingApp

Courtesy of Team 2584, The Flame Of The West, the RoboCompScoutingApp (RCSA for short) is a fully-configurable system to set up a server that allows for centralized collection of scouting statistics.  

By following a few guidelines to make a custom HTML-based scoring page, your match scouts can use their phones, tablets, or other mobile devices to collect and submit statistics on the activities your team needs to help you pick alliances.  The statistics are centrally collected and tabulated.  When ready, you can view and sort the collected statistics to help you build your winning alliance.

"But we don't have reception at the field!" - Don't worry! The app is designed to only need a network to open the scoring page the first time and when the data needs to be sent.  The scouts can set their devices up before matches start, and then go send all the statistics they collected at break time when they can get outside or othwerwise connect to a network.

-----

**Table of Contents**

- [Installation](#installation)
- [Using the App](#using-the-app)
- [Creating a Custom Scoring Page](#creating-a-custom-scoring-page)
- [Security](#security)
- [FAQs](#faqs)
- [License](#license)

## Installation

### Pre-Requisites
- Python 3.11 or greater
- `pip3` installed and working (it should be installed by default when you install python)
- If desired, install the package in a [virtual environment](https://docs.python.org/3/library/venv.html).  This is very common and considered best practice by many.
- A valid [FRC Events API account](https://frc-events.firstinspires.org/services/api/register)
- A linux system for testing and deployment.  There's nothing in the code that will prevent it running on Windows, but all my testing and commands below are for linux.  

### Install steps
1. Clone this repository to a location of your choosing: 
   - video
2. `cd` into the cloned repository and use `pip install -e .` to make a [local project installation](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs) of the package
    - This will make the underlying server code accessible and editable for you if you would like to explore or modify the code
    - You'll also be able to `git fetch` and any new code will now be available to you
    - If this is the first time you are doing a pip install on your system, you may see some warnings about setting path variables to access the application.  Be sure to read the warnings and make changes as needed.
    - video
3. Test to make sure the app is working with `robocompscoutingapp --help`:
    - video

## Using the App

- [Overview](#overview)
- [Initialize](#initialize)
- [Validate](#validate)
- [Set up for FIRST Event](#set-up-for-first-event)
- [Test your scoring page](#test-your-scoring-page)
- [Run the server for an Event](#run-the-server-for-an-event)
- [View Statistics](#viewing-statistics)

### Overview

The app is designed to help you set up your server environment by running through stages of preparation.

**Please Note** Your scoring app will not be accessible for mobile devices running on 5G/LTE unless the server you run this app on is routable from the Internet.  This means your Ubuntu desktop running on your laptop at home will not work (at least not easily).  There are many ways to spin up a temporary server on the Internet via AWS, GCP, Azure, or any number of VPS providers.  Odds are the lowest cost server possible will meet your needs and should not cost very much (or might be free). 

### Initialize

This is the first step.  It generates an expected file structure and makes initial configuration settings:
- video

You will then run all of the subsequent RCSA commands from the root of this newly created file structure.

The app does provide a fully working [example](src/robocompscoutingapp/initialize/static/scoring_sample.html) (from the 2023 FIRST season) that you can run all susequent commands on to see how it works. 

#### Set up your .RCSA_SECRETS.toml file
In addition to creating the directory structure, RCSA will also drop a file in your home `~` directory:
- video of existence of this file

You will need to edit this file to set your FRC_Events API (and also the username and password you may want to protect your application.  See [Security](#security) below)
- video of editing

### Validate
This step ensures your desired scoring page provides the proper "hooks" for the RCSA application to successfully score a team at a match.  Here I am validating the [scoring_sample.html](src/robocompscoutingapp/initialize/static/scoring_sample.html) file:
- video

**Note:** You run the robocompscoutingapp commands from the root of your established file structure.  This is one level up from the `static` subdirectory where you need to store your pages.  This means validation commands will look like this `robocompscoutingapp validate static/my_scoring_page.html`

The app will provide a lot of feedback if you have errors.  For example if I try to validate this basically empty page:
```html
<html>
    <head>
        <title>RCSA Empty Scoring Page Example</title>
    </head>
    <body>
        Nothing here.  See the scoring_sample for actual guidance
    </body>
</html>
```
I will get this:
- video

You must pass validation before you can use a scoring page.  Please see [Creating a Custom Scoring Page](#creating-a-custom-scoring-page) and the [example](src/robocompscoutingapp/initialize/static/scoring_sample.html) for more information on required parts of your scoring page

It is best to set your scoring page up and use it for an entire event.  However, FIRST is all about adaptability.  If you end up changing your scoring page in the middle of an event for any reason, please see [Changing scoring page in the middle of an event](#changing-scoring-page-in-the-middle-of-an-event) for some assistance.

### Set up for FIRST Event
Next you need to choose the event you will be attending and collecting statistics from.  The event code can be placed directly in the rcsa_config.toml file like this:
- video

Or you can use a built-in command in RCSA to find and set your event code:
- video of this

There is a chance the event you attend has some issue with their published match schedule.  Please see [Dealing with event restructuring](#dealing-with-event-restructuring) for some built in tools to help

### Test your scoring page
As you format your scoring page, and maybe write custom scripts, you will want to test them.  The `test` command will start a *local-only* server to allow you to tweak your UI to your heart's content.

The *local-only* server will only respond to web requests from itself.  The general use case here is for developing your scoring web page.  If you want to test on mobile devices or other remote system, you will need to use the `run` command.

*You do not need to restart the server if you only change files in the `static` directory.*
- video of start and web page opening

The app will use team and match data from the 2023 Los Angeles Regional (CALA) event.  I do this to be sure there is team and match data available for testing.  The app doesn't know if your chosen scoring items actually existed in 2023.

The test mode will make a temporary database that won't corrupt your actual production database so feel free to test "scout" as many teams and matches as you want.

#### Automated page testing
This is not mandatory but highly recommended.  After your page passes validation and meets your artistic standards, use `robocompscoutingapp test --automate` and you will be given a link you can cut-and-paste or click on to automatically test your scoring page:
- video

The automated testing will test every game mode and scoring element you define to make sure it all works.  It will also verify users can select matches and teams.  Be sure to pay attention to the messages delivered to the server for issues to address:
- pic of close up of messages

### Run the server for an Event
It's game day!  Time to get the server running for the scouts to use.

#### Set up authentication credentials
In ~/.RCSA_SECRETS.toml set up the username and password to authenticate your scouts to the app.  I highly recommend this because you never know who might discover your server and application and try to disrupt it.
- video

#### Configure the FQDN
Set the FQDN in rcsa_config.toml to your Internet routable domain name:
- video

This will allow the app to generate a URL you can send to your team mates so they can begin scoring.

#### Practice 'run' before going live
Use `robocompscoutingapp run`:
- video

Make sure your teammates can connect to the app!  `Ctrl-C` once it looks good.

#### Run for real
I recommend using `nohup robocompscoutingapp --daemon &` to ensure the application will not close if your command-line connection to the server is lost.  I freely admit this is a very lazy way to run a mildly resilient background process on linux but I ran out of time to get true daemon mode to work.  And `nohup` sure does work well!

You will be able to see logs in the `logs` directory of your file structure if you so desire:
- video

### Sending Saved Scores
If your scouting device loses network access when you try to submit a score it will provide some warning to you and then store the data in browser cache.  You can later send these scores by going to the main menu and clicking on the "Send Saved Scores to Server" link:
- video

**Please Note**: This will only work if:
 - The browser cache is not cleared (*be careful with incognito and private browsing modes*)
 - The domain of the scoring app doesn't change.  If it was `http://scoring.a.net` earlier and for some reason changes to `http://scoring.b.net` the app will not be able to access the data.  This is standard security behavior.

### Viewing Statistics
The Analysis page included with the app provides you the ability to select and view statistics for the teams at the event:
- video

## Creating a Custom Scoring Page
The part you have all been waiting for: how to make your own scoring page for your team.  One of the best ways to learn is to inspect the [example](src/robocompscoutingapp/initialize/static/scoring_sample.html).  All of the code snippets shown below are from that example.

### Match and Team Selection
It begins with an element that holds the controls needed to select the match and team you are going to score:
```html
<div class="container match_and_team_selection">
```

#### Match Select element
You need a `<select>` element with the `match_selector` class:
```html
 <!-- A select element with the "match_selector" class is required by the app -->
<select class="u-full-width match_selector">
    <!-- IMPORTANT, RCSA Code assumes the value of this option is the selected match number!! -->
    <option value=-1>Loading matches...</option>
</select>
```

The RCSA code will populate the `<option>` elements for this `<select>` with the available matches from the event.

#### Team select element
You need a `<select>` element with the `team_selector` class:
```html
 <!-- A select element with the "team_selector" class is required by the app -->
<select class="u-full-width team_selector">
    <!-- IMPORTANT, RCSA code assumes the value of this option is the selected team number!! -->
    <option value=-1>Loading Teams for this match...</option>
</select>
```

The RCSA code will populate the `<option>` elements for this `<select>` with the available Teams for the chosen match.

### Scoring Element
You need an element with the `scoring` class, usually a DIV.  This tells the app where to look for the rest of what it needs:
```html
<!--  the "scoring" class div is required by the app -->
<div class="section scoring" id="scoring_controls" hidden>
```
Here the `<div>` is marked as `hidden` because it doesn't show until a match and team have been selected.

#### Game Modes
FIRST matches have two distinct modes: Auton and Teleop.  But you might want to add more modes or eliminate them and just collect stats for the whole match.  That's up to you.  To do so you start with a an element with a `game_mode_group` class:
```html
<div class="row game_mode_group">
```
Then you designate elements that will be clicked to set the current game mode by including a `game_mode` class and a `data-modename="[Game Mode Name]"` attribute:
```html
<div class="six columns text-center">
    <!-- Game mode pickers are designated by assigning the "game_mode" class and placing the desired name of the mode in 'data-modename' attribute -->
    <i id="auton_icon" data-modename="Auton" class="fa-solid fa-robot fa-4x game_mode"></i>
</div>                
```
The `<div>` element around the actual clickable element is for formatting purposes, and it will also turn green when this mode is chosen.  The `fa-*` classes are in there because I am using Font Awesome for some icons.

#### Scoring Elements
Here is where you define and categorize your scoring elements (i.e. those things you want to track on the playing field).

Scoring elements are clickable elements that have the following requirements:
 - A class entry of:
    - `score_tally` - Scoring items that keep a running count of the times the robot did this thing
    - `score_flag` - A boolean on/off flag for something that either happened or didn't
    - These are the only scoring types currently supported in the app but I think you'll find they cover a wide array of behaviors
- A `data-scorename=[chosen name]` attribute that defines the name of this scoring element.  This is the name you will see in the Analysis page
- An *optional* `data-onlyForMode=[mode]` attribute that means the item can only be clicked if the indicated mode is active.  The mode name must have been defined per [Game Mode](#game-modes)

Some examples:
```html
<!-- The DIV element encapsulating the scoring item is for formatting purposes and feedback -->
<div class="six columns text-center">
    <img data-scorename="cube" class="score_tally" src="images/cube.png" alt="Cube" width="75" height="75">
</div>

<button data-scorename="Attempted charge" class="score_flag button-primary">Attempted</button>
<button id="mobility" data-scorename="Auton Mobility" data-onlyForMode="Auton" class="button-primary score_flag">Mobility (Auton Only)</button>
``` 

#### Submit button
This is the button that is clicked to make the app send the score to the server.  It is designated with a `report_submit` class
```html
<button class="button-orange btn-big report_submit">Submit Report</button>
```

### Required script hook
Lastly, scoring pages need to include the RCSA mechanics code:
```html
<!-- The rcsa_loader.js script reference is mandatory for the app to work correctly. -->
<script src="js/rcsa_loader.js"></script>
```

#### Integration required in UI scripts
Just including the `rcsa_loader.js` script is not enough.  There are also some critical integrations needed:
First you must call the `startup()` function once your UI code is all loaded:
```js
$(document).ready(function() {
    // CRITICAL INTEGRATION TO THE APP SERVER HERE::  REQUIRED!!
    // Call this before other setup tasks as the RCSA mechanics will tie into the rest of the DOM
    rcsa.startup(matchAndTeamData, rcsaErrorHandler);
    // ^^^^^^^^^^^^^^^^^^^^^^^^^^^
})
```
And you also must call the `submitScore()` method when you are ready to submit the score to a server:
```js
// CRITICAL INTEGRATION TO THE APP SERVER HERE::  REQUIRED!!
// You do not need to use 'force_fail' in your code
// You can simply call: rcsa.submitScore(scoreSubmitSuccess, scoreSubmitFailure);
rcsa.submitScore(scoreSubmitSuccess, scoreSubmitFailure, force_fail);
// ^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

See the [default UI code](src/robocompscoutingapp/initialize/static/js/rcsa_default_ui_animation.js) and the [rcsa_loader](src/robocompscoutingapp/initialize/static/js/rcsa_loader.js) code for more info

### Thats it!
I know it might seem complicated but if you experiment, try things, and pay attention to the error messages you get it will all become clear.  Following these guidelines, you can make a new scoring page in mere minutes.  Be sure to [test](#automated-page-testing)!

## Security
### No HTTPS
At this moment, the server will not use HTTPS.  The main reason for this is PKI can be complicated and browsers can be picky.  I wanted to prevent problems with this.  The [underlying technology](https://www.uvicorn.org/deployment/#running-with-https) behind the server can absolutely support HTTPS but I did not build it into the code.  It is a TODO.

### Basic Authentication
By providing credentials as [shown](#basic-authentication) you can prevent random internet scanners from easily accessing your application.  I highly recommend you do so.  But be aware that since the server is not using HTTPS those credentials are passed in plain text (actually they are Base64 encoded, but that is [just fancy plaintext](https://www.darkreading.com/cybersecurity-analytics/hacker-pig-latin-a-base64-primer-for-security-analysts)).  

This means any device sniffing network traffic on the network you are using can intercept and use those credentials.  

From a cybersecurity perspective that's pretty bad but here's why I think its acceptable:

### Threat Model
The data collected by this app:
 - Is not life or death
 - Does not control critical infrastructure (unless you add some crazy functionality to the app)
 - Is not protected health, personal, or payment card information
These facts make my choice to delay building HTTPS and use basic authentication (as opposed to OAuth) reasonable and sufficient.

Applied, real cybersecurity is all about balancing risk with the costs of protection.

I highly recommend adding credentials to prevent random people from stumbling on to your app.

## FAQs

### Working with no network signal
You only need a network signal to load the scoring page before the day's matches begin and to eventually send saved scores from a day's work.  As long as you don't clear the browser cache on your scoring device you can send those scores at your convenience when you have a network connection again.

### Dealing with event restructuring
Perhaps something crazy happens during an event and they decide to restructure the alliance pairings in qualification.  If this happens use `robocompscoutingapp prepare-event --refresh-match-data` to reload any unscored matches.  All scored matches and data will be retained unless you use `robocompscoutingapp prepare-event --reset-all-data` and then all saved data for the event will be erased.

### Changing scoring page in the middle of an event
Maybe after your scouting team starts using the app during an event you decide some changes are needed.  After validating (and maybe testing) your new page, the app will detect previous scores for this event made with a different scoring page.  It will attempt to migrate the data so you can see previous results.  In order for this to be as successful as possible:
 - Keep as many mode names the same as possible (defined by `data-modename`)
 - Keep as many scoring item names the same as possible (defined by `data-scorename`)

Use the `robocompscoutingapp run` command to have the app detect and attempt to migrate the data.  Don't use `nohup` until the data is migrated. 


## License

`robocompscoutingapp` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.



