/*
    This handles all of the actual communication with the robocompscoutingapp server.
*/

/* ################### Core RCSA mechanics (modify at your own risk!) ##################### */

///  Scoring Item classes
class rcsa_scoring_item {
    constructor(scoring_item_id, name) {
        this.current_value = 0;
        this.scoring_item_id = scoring_item_id;
        this.name = name;

        // Get this items possible specific mode
        this.only_for_mode = $(`[data-scorename='${name}']`).data("onlyformode");
        // Connect the object to this scoring item
    }

    reset() {
        this.current_value = 0;
    }

    clicked() {
        // This checks if the current mode matches only_for_mode (if exists)
        if ((this.only_for_mode === undefined) || (rcsa.current_game_mode === this.only_for_mode) ) {
            // All clicks are passed
            this.#successfulClick();
        }        
    }

    #successfulClick() {
        // Default behavior for a click is score_tally style
        // Other scoring types should override this
        this.current_value += 1;
    }

    getJSONobject(mode_id, mode_name) {
        if ((this.only_for_mode === undefined) || (mode_name === this.only_for_mode) )
            return {
                scoring_item_id:this.scoring_item_id,
                mode_id:mode_id,
                value:this.current_value
            }
        else {
            return null;
        }
    }
}

class rcsa_score_tally extends rcsa_scoring_item {
    // The base class methods are correct here
    // This is here for possible future expansion
}

class rcsa_score_flag extends rcsa_scoring_item {
    #successfulClick() {
        if (this.current_value == 0) {
            // Flag set!
            this.current_value = 1;
        } else {
            // Remove flag
            this.current_value = 0;
        }
    }
}

// Internal Score Database class
class ScoringDatabase {
    // modes_and_items the JSON object delivered by the API
    constructor(modes_and_items) {
        // modes is Dict[str, GameMode object] (see ScoringData.py)
        this.game_modes = modes_and_items.modes;
        this.scoring_page_id = modes_and_items.scoring_page_id;
        /* 
            Build the 'database'
            {
                modename1: {
                    scoring_item_name_1:scoring item object,
                    etc..
                },
                modename2: {
                    scoring_item_name_1:scoring item object,
                    etc..
                },

            }
        */
        this.scoringDB = {};
        for (const [mode_name, mode_obj] of Object.entries(modes_and_items.modes)) {
            this.scoringDB[mode_name] = {};
            for (const [item_name, item] of Object.entries(modes_and_items.scoring_items)) {
                switch(item.type) {
                    case "score_tally":
                        this.scoringDB[mode_name][item_name] = new rcsa_score_tally(item.scoring_item_id, item_name);
                        break;
                    case "score_flag":
                        this.scoringDB[mode_name][item_name] = new rcsa_score_flag(item.scoring_item_id, item_name);
                        break;
                    default:
                        console.error(`I do not know how to handle scoring item type: ${item_object.type}`);
                  }
            }
        }
    }

    itemClicked(mode_name, item_name) {
        this.scoringDB[mode_name][item_name].clicked()
    }

    generateScoreResult(matchNumber, teamNumber) {
        let to_return = {
            matchNumber:matchNumber,
            teamNumber:teamNumber,
            scoring_page_id:this.scoring_page_id,
            scores:[]
        }
        for (const [mode_name, item_dict] of Object.entries(this.scoringDB)) {
            let mode_id = this.game_modes[mode_name].mode_id;
            for (const [item_name, item_obj] of Object.entries(item_dict)) {
                let score_obj = item_obj.getJSONobject(mode_id, mode_name);
                if (score_obj !== null) {
                    // items return null if it is not valid for this mode.
                    // This here to prevent odd 0 results
                    to_return.scores.push(score_obj);
                }
            }
        }
        return to_return
    }

    getFlagStatusForMode(modename) {
        let toreturn = {}
        for (const [item_name, item_obj] of Object.entries(this.scoringDB[modename])) {
            if (item_obj.constructor.name  === "rcsa_score_flag") {
                // Cool int to boolean short cut from: https://codedamn.com/news/javascript/how-to-convert-values-to-boolean
                toreturn[item_name] = !!item_obj.current_value
            }
        }
        return toreturn
    }

    resetDB() {
        for (const [mode_name, item_dict] of Object.entries(this.scoringDB)) {
            for (const [item_name, item_obj] of Object.entries(item_dict)) {
                item_obj.reset();
            }
        }
    }
}


let rcsa = {
    match_callback: undefined,
    error_callback: undefined,
    current_game_mode: undefined,
    matches_and_teams: undefined,
    modes_and_items: undefined,     
    scoringDB: {},

    startup: function (match_callback, error_callback) {
        console.info("rcsa startup called");
        // success_callback should take one parameter: match_list
        rcsa.registerMatchCallback(match_callback);
        // error_callback should take single parameter: err_msg
        rcsa.registerErrorCallback(error_callback);
        // initialize important data elements
        // get matches and teams
        rcsa.loadMatches();
        // Get the scoring items
        rcsa.getScoringItems();
        // check if testing
        rcsa.activateTesting();
    },

    loadMatches: function () {
        $.ajax({
            type: "GET",
            url: "/api/getMatchesAndTeams",
            dataType: "json",
            contentType: 'application/json',
            success: function (server_data, text_status, jqXHR) {
                // Give the data to the display code
                console.log("Match data recieved");
                rcsa.matches_and_teams = server_data;
                rcsa.match_callback(server_data);
            },
            error: function( jqXHR, textStatus, errorThrown ) {
                msg = `Unable to get match data because:\n${errorThrown}`
                console.error(msg);
                rcsa.error_callback(msg);
            }
        })
    },
    
    activateTesting: function () {
        // Check for the testing GET parameter
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has("test")) {
            console.log("Activating automated testing.");
            this.loadJS("js/rcsa_tester.js");
        }
    },

    submitScore: function (success_callback, score_error_callback, error_test = false) {
        // success_callback has no parameters
        // error_callback should take one parameter: err_msg
        // This is a different error_callback and the general one will not be used
        // error_test is used to force the code to handle the data as though the server broke
        console.log("Submit score called");
        var matchNumber = $(`.match_selector`).val();
        var teamNumber =  $(`.team_selector`).val();
        var url = "/api/addScores";
        if (error_test) {
            // Force a failure
            url = "/errorcheck";
        }
        var data_to_post = rcsa.scoringDB.generateScoreResult(matchNumber, teamNumber)
        $.ajax({
            type: "POST",
            url: url,
            data: JSON.stringify(data_to_post),
            dataType: "json",
            contentType: 'application/json',
            processData: false,
            success: function (response) {
                console.log("Score successfully sent");
                rcsa.nextMatch();
                success_callback();
            },
            error: function( jqXHR, textStatus, errorThrown ) {
                console.log("Score send failed with " + errorThrown);
                if (jqXHR.status === 409) {
                    // This team aleady scored for this match
                    msg = "This team was already scored for this match";
                    rcsa.nextMatch();
                    score_error_callback(msg);
                } else {
                    if (errorThrown.length == 0) {
                        errorThrown = "the server could not be reached";
                    }
                    // Add to local storage
                    rcsa.addSavedScore(data_to_post);
                    rcsa.nextMatch();
                    err_msg = `Score not saved to central database because ${errorThrown}. The score has been saved to localStorage.  Use the 'Send Saved Scores' option from the main menu to try again later.`;
                    score_error_callback(err_msg);
                }
            },
            
        });
        
    },

    nextMatch: function () {
        // Resets data but does not reload matches, instead just pops off the match we already did.
        var matchNumber = $(`.match_selector`).val();
        delete rcsa.matches_and_teams.matches[matchNumber];
        rcsa.scoringDB.resetDB();        
        rcsa.match_callback(rcsa.matches_and_teams);
    },

    // initalizeScoringData: function () {

    //     // Clear important scoring data
    //     rcsa.scoringDB.resetDB();
    // },

    getScoringItems: function () {
        // Call for DB answer
        $.ajax({
            type: "GET",
            url: "/api/gameModesAndScoringElements",
            dataType: "json",
            contentType: 'application/json',
            success: function (modes_and_items, text_status, jqXHR) {
                // Give the data to the display code
                console.log("Game Modes and scoring item data recieved");
                // Build the database.  
                rcsa.scoringDB = new ScoringDatabase(modes_and_items);
                rcsa.modes_and_items = modes_and_items;
                // tie into mode clicks
                $(".game_mode").click(function (e) {
                    rcsa.handleModeClick(this);
                });
                // Click the first one to get us started
                $(".game_mode")[0].click();
                // Connect to scoring item clicks
                $("[class*='score_'").click( function(e) {
                    let item_name = $(this).data("scorename");
                    rcsa.scoringDB.itemClicked(rcsa.current_game_mode, item_name);
                })
            },
            error: function( jqXHR, textStatus, errorThrown ) {
                msg = `Unable to get game modes and scoring data because:\n${errorThrown}`
                console.error(msg);
                rcsa.error_callback(msg);
            }
        })
    },

    registerMatchCallback:function (match_callback) {
        // match_callback should take a single parameter (match_list) with the match data to present to user
        rcsa.match_callback = match_callback;
    },

    registerErrorCallback: function (error_callback) {
        // general_error_callback should take a single parameter, err_msg
        // Used to communicate errors to the user
        rcsa.error_callback = error_callback;
    },

    handleModeClick: function (selected_mode) {
        rcsa.current_game_mode = $(selected_mode).data("modename");
        console.info(`${rcsa.current_game_mode} selected`);
    },

    // From: https://www.educative.io/answers/how-to-dynamically-load-a-js-file-in-javascript
    loadJS: function(FILE_URL, async = true) {
        let scriptEle = document.createElement("script");
        
        scriptEle.setAttribute("src", FILE_URL);
        scriptEle.setAttribute("type", "text/javascript");
        scriptEle.setAttribute("async", async);
        
        document.body.appendChild(scriptEle);
        
        // success event 
        scriptEle.addEventListener("load", () => {
            console.log(`${FILE_URL} loaded`);
        });
            // error event
        scriptEle.addEventListener("error", (ev) => {
            console.log(`Error on loading ${FILE_URL}`, ev);
        });
    },
    
    getFlagStatusForMode: function (modename) {
        // Returns { scorename: true if set, false if not} for score_flag items in the DB
        return rcsa.scoringDB.getFlagStatusForMode(modename); 
    },

    getSavedScores: function () {
        var saved_scores = JSON.parse(localStorage.getItem("rcsa_saved_scores"));
        if (saved_scores === null) {
            saved_scores = {};
        }
        return saved_scores;
    },

    addSavedScore: function (scored_match_for_team, eventCode = null) {
        // scored_match_for_team is the output from the scoringDB
        if (eventCode === null) {
            eventCode = rcsa.matches_and_teams.eventCode
        }
        var saved_scores = rcsa.getSavedScores();
        if (eventCode in saved_scores) {
            saved_scores[eventCode].push(scored_match_for_team);
        } else {
            saved_scores[eventCode] = [scored_match_for_team];
        }
        localStorage.setItem("rcsa_saved_scores", JSON.stringify(saved_scores));
    },

    clearSavedScores: function () {
        localStorage.setItem("rcsa_saved_scores", JSON.stringify({}));
    }
}

