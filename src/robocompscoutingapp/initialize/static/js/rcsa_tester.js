/*
    Automated test code to ensure basic app integration is working
*/

let rcsa_tester = {

    overall_test_success: true,
   
    executeTestsWithDelay: async function (tests_to_execute, delay_in_seconds = 1.0) {
        /* Basic structure of this code is courtesy ChatGPT */
        for (const func of tests_to_execute) {
            await new Promise((resolve, reject) => {
                func((success) => {
                    this.overall_test_success &&= success
                    setTimeout(resolve, delay_in_seconds * 1000); // Resolve the promise after chosen delay
                });
            }).catch((error) => {
                console.error(error.message);
                rcsa_tester.overall_test_success = false;
                return; // Stop executing further functions if one fails
            });
        }
        alert("All tests are complete!  Please check output on the server for any issues to resolve.");
        rcsa_tester.endTesting(rcsa_tester.overall_test_success);
    },

    checkForTestMode: function () {
        $.ajax({
            type: "GET",
            url: "/test/checkTestMode",
            dataType: "json",
            // data:get_params,
            contentType: 'application/json',
            processData: false,
            success: function (server_data, text_status, jqXHR) {
                if (server_data.in_test_mode) {
                    // Placed in a short time out to ensure the page renders before the alert stops the rendering.  Really just cosmetic
                    // Hint from: https://stackoverflow.com/questions/40086680/how-to-make-the-html-renders-before-the-alert-is-triggered
                    setTimeout(function() {
                        var user_wants_to_test = confirm("I am prepared to run a series of automated tests on this scoring page to ensure server integration is working.\nPress 'Ok' when the page is ready to be tested.");
                        if (user_wants_to_test) {
                            console.log("Automated testing beginning.");
                            runAutomatedTests();
                        } else {
                            console.log("Automated testing cancelled by user request");
                        }
                    },250);
                } else {
                    alert("The server is not in test mode.  Please tell your admin to run the server with the test command.");
                }
            },
            error: function( jqXHR, textStatus, errorThrown ) {
                alert(`Whoops. Attempt to verify server is configured for test failed because:\n${errorThrown}`);
            }
        })
    },

    endTesting: function (test_success) {
        // Sends the testingComplete message to the server
        get_params = {
            success:test_success
        };
        $.ajax({
            type: "GET",
            url: "/test/testingComplete",
            dataType: "json",
            data:get_params,
            contentType: 'application/json',
            // processData: false,
            success: function (server_data, text_status, jqXHR) {
                // pass
            },
            error: function( jqXHR, textStatus, errorThrown ) {
                console.log(`Attempt to send test completion message to server failed because:\n${errorThrown}`);
            }
        })
    },

    sendServerMessage: function (type, message) {
        to_post = {
            type:type,
            message:message
        }
        $.ajax({
            type: "POST",
            url: "/test/testMessage",
            data: JSON.stringify(to_post),
            dataType: "json",
            contentType: 'application/json',
            processData: false,
            success: function (response) {
                // pass
            },
            error: function( jqXHR, textStatus, errorThrown ) {
                console.error(`Unable to send test message with content: ${to_post} because ${errorThrown}`);
            }
        });
    },

    sendError: function (message) {
        this.sendServerMessage("error", message);
        console.log(message);
    },

    sendWarning: function (message) {
        this.sendServerMessage("warning", message);
        console.log(message);
    },

    sendInfo: function (message) {
        this.sendServerMessage("info", message);
        console.log(message);

    },

    sendSuccess: function (message) {
        this.sendServerMessage("success", message);
        console.log(message);

    },

    
    
}

//////////// TESTS ////////////////
/*
    All tests take a callback as a parameter and then returns the success or failure of the test
*/

function testError(callback) {
    console.log("Testing server-side error message");
    rcsa_tester.sendError("Testing server side error message, please ignore");
    callback(true);
}

function testWarning(callback) {
    console.log("Testing server-side warning message");
    rcsa_tester.sendWarning("Testing server side warning message, please ignore");
    callback(true);
}

function testSuccess(callback) {
    console.log("Testing server-side success message");
    rcsa_tester.sendSuccess("Testing server side success message, please ignore");
    callback(true);
}

function testInfo(callback) {
    console.log("Testing server-side info message");
    rcsa_tester.sendInfo("Testing server side info message, please ignore");
    callback(true);
}

function testBigFail(callback) {
    // Just throws an error to make sure things work as planned
    throw new Error("Testing");
}

function testsComplete(callback) {
    alert("All tests are complete!  Please check output on the server for any issues to resolve.");
    rcsa_tester.endTesting(rcsa_tester.overall_test_success);
    callback(true);
}

function testMatchSelection(callback) {
    // Pick the first match on the list.
    console.log("Testing match selection");
    // Check for a placeholder match number 
    var value_to_set = -1;
    var child_index = 1;
    while (!(value_to_set in rcsa.matches_and_teams.matches)) {
        value_to_set = $(`.match_selector option:nth-child(${child_index})`).attr("value");
        if (value_to_set === undefined) {
            rcsa_tester.sendError("Your match_selector is not putting match numbers as the option values.  Please correct.  See the sample scoring.html provided.");
            throw new Error("Match selection test has to pass for testing to continue.  Please see server output.");
        }
        child_index += 1;
    }

    // Now set the match selection value
    $(`.match_selector`).val(value_to_set).change();
    rcsa_tester.sendSuccess("match_selection test passed");
    callback(true);
}

function testTeamSelection(callback) {
    // Pick the first team on the match
    console.log("Testing team selection");
    var value_to_set = -1;
    var child_index = 1;
    while (!(value_to_set in rcsa.matches_and_teams.teams)) {
        value_to_set = $(`.team_selector option:nth-child(${child_index})`).attr("value");
        if (value_to_set === undefined) {
            rcsa_tester.sendError("Your team_selector is not putting team numbers as the option values.  Please correct.  See the sample scoring.html provided.");
            throw new Error("Team selection test has to pass for testing to continue.  Please see server output.");
        }
        child_index += 1;
    }

    // Now set the team selection value
    $(`.team_selector`).val(value_to_set).change();
    rcsa_tester.sendSuccess("team_selection test passed");
    callback(true);
}

function testModeSelection(callback) {
    console.log("Testing mode clicking/selection");
    var passed = true;
    for (const [mode_name, mode_obj] of Object.entries(rcsa.modes_and_items.modes)) {
        var found_it = $(`[data-modename='${mode_name}']`);
        if (found_it.length == 0) {
            msg = `There is no element with data-modename=${mode_name}.  You will not be able to score for this modename`;
            rcsa_tester.sendError(msg);
            passed = false;
            continue;
        }
        found_it.click();
        if (rcsa.current_game_mode !== mode_name) {
            msg = `The element for setting the ${mode_name} mode is not responding to clicks.  You will not be able to select this mode for scoring`;
            rcsa_tester.sendError(msg);
            passed = false;
        }
    }
    if (passed) {
        rcsa_tester.sendSuccess("Mode selection passed");
    } else {
        rcsa_tester.sendError("Mode selection did not pass");
    }
    callback(passed);
}

function testScoring(callback) {
    console.log("Testing scoring");
    var passed = true;
    for (const [mode_name, mode_obj] of Object.entries(rcsa.modes_and_items.modes)) {
        // Select this mode
        $(`[data-modename='${mode_name}']`).click();
        for (const [item_name, item] of Object.entries(rcsa.modes_and_items.scoring_items)) {
            var found_it = $(`[data-scorename='${item_name}']`);
            if (found_it.length == 0) {
                msg = `There is no element with data-scorename=${item_name}.  You will not be able to score this item`;
                rcsa_tester.sendWarning(msg);
                passed = false;
                continue;
            }
            var only_for_mode = found_it.data("onlyformode");
            if ((only_for_mode === undefined) || (only_for_mode === mode_name)) {
                found_it.click();
                scored_value = rcsa.scoringDB.scoringDB[mode_name][item_name].current_value;
                if (scored_value != 1) {
                    msg = `The ${item_name} scoring element did not respond to a click`;
                    rcsa_tester.sendError(msg);
                    passed = false;
                }
            } else {
                // This thing should not accumulate points under this mode.
                found_it.click();
                scored_value = rcsa.scoringDB.scoringDB[mode_name][item_name].current_value;
                if (scored_value != 0) {
                    msg = `The ${item_name} scoring element is not supposed to accumulate scoring for ${mode_name} but it did.  This may have unexpected results.`;
                    rcsa_tester.sendWarning(msg);
                }
            }
        }
    }
    if (passed) {
        rcsa_tester.sendSuccess("Scoring items passed");
    } else {
        rcsa_tester.sendError("Scoring items did not pass");
    }
    callback(passed);
}

function testSuccessfulSendScore(callback) {
    console.log("Testing successful send of score data");
    rcsa_tester.sendInfo("The scoring submit test only checks if there is an event tied to the scoring submit button and then tests the rcsa_loader mechanics separately.  It will not test clicking your submit button.  Please test manually");
    var overall_test_success = true;

    function successCallback() {
        rcsa_tester.success("Score report successfully submitted");
        callback(true);
    }

    function errorCallback(err_msg) {
        rcsa_tester.error(`Submit score report failed because ${err_msg}`);
        callback(false);
    }

    // Check for a click event tied to the .report_submit button
    // Page validation allows multiple buttons with report submit, check each one
    possible_submit_buttons = document.getElementsByClassName("report_submit")
    for (button of possible_submit_buttons) {
        if ("click" in getEventListeners(button)) {
            // pass
        } else {
            rcsa_tester.error(`Element: ${button} does not have a click event listener.  It will not work when clicked`);
            overall_test_success = false;
        }
    }

    // Now test mechanics
    rcsa.submitScore(successCallback, errorCallback);
}

function runAutomatedTests () {
    tests = [
        testError,
        testWarning,
        testSuccess,
        testInfo,
        // testBigFail,  // Allowing this to run will break testing
        testMatchSelection,
        testTeamSelection,
        testModeSelection,
        testScoring,
        testSuccessfulSendScore,
    ]

    rcsa_tester.executeTestsWithDelay(tests)
}

console.log("test script loaded");
rcsa_tester.checkForTestMode();

  