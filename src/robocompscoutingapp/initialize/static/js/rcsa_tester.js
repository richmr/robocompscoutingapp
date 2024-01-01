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
                return; // Stop executing further functions if one fails
            });
        }
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
    },

    sendWarning: function (message) {
        this.sendServerMessage("warning", message);
    },

    sendInfo: function (message) {
        this.sendServerMessage("info", message);
    },

    sendSuccess: function (message) {
        this.sendServerMessage("success", message);
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

function testsComplete(callback) {
    alert("All tests are complete!  Please check output on the server for any issues to resolve.");
    rcsa_tester.endTesting(rcsa_tester.overall_test_success);
    callback(true);
}

function runAutomatedTests () {
    tests = [
        testError,
        testWarning,
        testSuccess,
        testInfo,

        // Always call this one last
        testsComplete
    ]

    rcsa_tester.executeTestsWithDelay(tests)
}

console.log("test script loaded");
rcsa_tester.checkForTestMode();

  