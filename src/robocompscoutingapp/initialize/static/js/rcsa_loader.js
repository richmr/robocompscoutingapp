/*
    This handles all of the actual communication with the robocompscoutingapp server.
*/

///  Scoring Item classes
class rcsa_scoring_item {
    constructor(scoring_item_id, name) {
        this.current_value = 0;
        this.scoring_item_id = scoring_item_id;
        this.name = name;

        // Get this items possible specific mode
        this.only_for_mode = $(`[data-scorename='${name}']`).data("onlyformode");
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

    getJSONobject(mode_id) {
        return {
            scoring_item_id:this.scoring_item_id,
            mode_id:mode_id,
            value:this.value
        }
    }
}

class rcsa_score_tally extends rcsa_scoring_item {
    // The base class methods are correct here
    // This is here for possible future expansion
}

class rcsa_score_flag extends rcsa_scoring_item {
    #successfulClick() {
        if (this.value == 0) {
            // Flag set!
            this.value = 1;
        } else {
            // Remove flag
            this.value = 0;
        }
    }
}

/* ################### Core RCSA mechanics (modify at your own risk!) ##################### */

let rcsa = {
    match_callback: undefined,
    error_callback: undefined,
    current_game_mode: undefined,
    scoring_items: {},


    startup: function (match_callback, error_callback) {
        console.info("rcsa startup called");
        // success_callback should take one parameter: match_list
        rcsa.registerMatchCallback(match_callback);
        // error_callback should take single parameter: err_msg
        rcsa.registerErrorCallback(error_callback);
        // initialize important data elements
        // tie into mode clicks
        $(".game_mode").click(function (e) {
            rcsa.handleModeClick(this);
        });
        // get matches and teams
        // check if testing
        this.activateTesting();
    },
    
    activateTesting: function () {
        // Check for the testing GET parameter
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has("test")) {
            console.log("Activating automated testing.");
            this.loadJS("js/rcsa_tester.js");
        }
    },

    submitScore: function (success_callback, score_error_callback) {
        // success_callback has no parameters
        // error_callback should take one parameter: err_msg
        // This is a different error_callback and the general one will not be used
        console.log("Submit score called");
        // On success or failure: reset important data elements
        // On failure, store scoring information in local storage for later sending
    },

    nextMatch: function () {
        // Resets data but does not reload matches, instead just 
    },

    initalizeScoringData: function () {
        // Clear important scoring data
    },

    getScoringItems: function () {
        // Call for DB answer

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
    }
      

}

