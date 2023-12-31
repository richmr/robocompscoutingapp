/*
    Automated test code to ensure basic app integration is working
*/

let rcsa_tester = {
    executeTestsWithDelay: async function (tests_to_execute, delay_in_seconds = 1.0) {
        for (const func of tests_to_execute) {
            await new Promise((resolve, reject) => {
                func((success) => {
                    if (success) {
                    setTimeout(resolve, delay_in_seconds * 1000); // Resolve the promise after chosen delay
                    } else {
                    reject(new Error('Function did not succeed.'));
                    }
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
                    user_wants_to_test = confirm("I am prepared to run a series of automated tests on this scoring page to ensure server integration is working.\nPress 'Ok' when the page is ready to be tested.");
                    if (user_wants_to_test) {
                        console.log("Automated testing beginning.");
                    }
                } else {
                    alert("The server is not in test mode.  Please tell your admin to run the server with the test command.");
                }
            },
            error: function( jqXHR, textStatus, errorThrown ) {
                alert(`Whoops. Attempt to verify server is configured for test failed because:\n${errorThrown}`);
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
    


}

/* Sample asynchronous code.  Thanks ChatGPT */
async function executeSequentiallyWithDelay(functions) {
    for (const func of functions) {
        await new Promise((resolve, reject) => {
            func((success) => {
                if (success) {
                setTimeout(resolve, 1000); // Resolve the promise after 1 second delay
                } else {
                reject(new Error('Function did not succeed.'));
                }
            });
        }).catch((error) => {
            console.error(error.message);
            return; // Stop executing further functions if one fails
        });
    }
}

  
  // Example functions
function function1(callback) {
    console.log('Function 1 started');
    // Simulating an asynchronous operation
    setTimeout(() => {
      const success = Math.random() > 0.5; // Simulating success based on a condition
      console.log(`Function 1 completed with success: ${success}`);
      callback(success);
    }, 2000); // Function 1 takes 2 seconds to complete
}
  
  function function2(callback) {
    console.log('Function 2 started');
    // Simulating an asynchronous operation
    setTimeout(() => {
      const success = Math.random() > 0.5; // Simulating success based on a condition
      console.log(`Function 2 completed with success: ${success}`);
      callback(success);
    }, 1000); // Function 2 takes 1 second to complete
}
  
  // Array of functions
//   const functionsArray = [function1, function2];
  
  // Execute functions sequentially with a 1-second delay
//   executeSequentiallyWithDelay(functionsArray);

console.log("test script loaded");
rcsa_tester.checkForTestMode();
  