/*
    We use this when scouts watching events were unable to submit their scoring reports due to loss of network.
    Once the scout gets signal again, they go to SendScores.html to enable sending of stored scores.

    WARNING:  This will ONLY work if the hostname used for the scoring is the same used when opening this page
    i.e:
    - Scored on http://mybotteam.server.com/scoring
    - Then went to http://mybotteam.server.com/app/SendScores.html to send stored scores
*/

var stored_scores = [];
var eventCode = "";
var scores_table;

function scoresReady(scores_sent=false) {
    if (stored_scores.length == 0) {
        $("#scores_table_row").hide();
        $("#submit_button_row").hide();
        if (scores_sent) {
            $("#startup_message_text").text("All saved scores successfully sent!");
        } else {
            $("#startup_message_text").text("No saved scores found!");
        }
    } else {
        $("#startup_message_text").text(`Found ${stored_scores.length} scores to send`);
        if (scores_sent) {
            scores_table.clear();
            for (score_to_show of stored_scores) {
                scores_table.row.add(score_to_show).draw();
            }
        } else {
            scores_table = $('#saved_scores_table').DataTable( {
                autoWidth:false,
                searching: false,
                pageLength:50,
                dom: "Bfrtip",
                data: stored_scores,
                columns: [
                            { data: "matchNumber" },
                            { data: "teamNumber" },
                ],
            } );
            $("#scores_table_row").show();
            $("#submit_button_row").show();
        }
    }
}

function checkForScores(matches_and_teams) {
    eventCode = matches_and_teams.eventCode;
    let found_scores = rcsa.getSavedScores();
    if (eventCode in found_scores) {
        stored_scores = found_scores[eventCode];
    } else {
        stored_scores = [];
    }
    scoresReady();
}

function submitErrorHandler(err_msg) {
    $.toast({ 
        text : err_msg, 
        showHideTransition : 'slide',  // It can be plain, fade or slide
        bgColor : 'red',              // Background color for toast
        textColor : '#eee',            // text color
        allowToastClose : true,       // Show the close button or not
        hideAfter : false,              // `false` to make it sticky or time in miliseconds to hide after
        stack : 5,                     // `false` to show one stack at a time count showing the number of toasts that can be shown at once
        textAlign : 'left',            // Alignment of text i.e. left, right, center
        position : 'top-left'       // bottom-left or bottom-right or bottom-center or top-left or top-right or top-center or mid-center or an object representing the left, right, top, bottom values to position the toast on page
      });
    console.error(err_msg);
}

function submitStoredScores() {
    var failed_sends = [];
    var successful_sends = [];

    // This is used for testing only
    let force_fail = false;
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has("force_fail")) {
        force_fail = true;
    }

    function checkForMoreScores() {
        if (stored_scores.length > 0) {
            sendNextScore();
        } else {
            rcsa.clearSavedScores();
            for (score_to_save of failed_sends) {
                rcsa.addSavedScore(score_to_save, eventCode);
            }
            stored_scores = failed_sends;
            $("#data_modal_buttons").show();
            scoresReady(scores_set = true);
        }
    }
    
    function scoreSentSuccessfully(score_that_was_sent) {
        successful_sends.push(score_that_was_sent);
        $("#successful_send_count").text(successful_sends.length);
        checkForMoreScores();
        
    }

    function scoreFailedToSend(score_that_was_sent, err_msg) {
        failed_sends.push(score_that_was_sent);
        $("#failed_send_count").text(failed_sends.length);
        $("#send_error_messages").show();
        $("#send_error_messages").append(`${err_msg}<br>`);
        checkForMoreScores();  
    }    

    function sendNextScore() {
        // Get score to send
        var score_to_send = stored_scores.shift();
        var url = "/api/addScores";
        if (force_fail) {
            // Force a failure
            url = "/errorcheck";
        }
        $.ajax({
            type: "POST",
            url: url,
            data: JSON.stringify(score_to_send),
            dataType: "json",
            contentType: 'application/json',
            processData: false,
            success: function (response) {
                console.log("Score successfully sent");
                scoreSentSuccessfully(score_to_send);
            },
            error: function( jqXHR, textStatus, errorThrown ) {
                if (jqXHR.status === 409) {
                    // This team aleady scored for this match, which means it was "successfully" stored
                    scoreSentSuccessfully(score_to_send);
                } else {
                    console.log("Score send failed with " + errorThrown);
                    if (errorThrown.length == 0) {
                        errorThrown = "the server could not be reached";
                    }
                    err_msg = `Score not saved to central database because ${errorThrown}`;
                    scoreFailedToSend(score_to_send, err_msg);
                }
            },
        })

    }

    checkForMoreScores();
}

function setupSubmitModal() {
    $("#submit_button").click( function (e) {
        $("#send_error_messages").empty();
        $("#send_error_messages").hide();
        $("#data_modal_buttons").hide();
        $("#successful_send_count").text(0);
        $("#failed_send_count").text(0);

        $("#sending_data_modal").modal({
            escapeClose: false,
            clickClose: false,
            showClose: false
        });

        submitStoredScores();
    });

    $("#close_modal").click( function (e) {
        $.modal.close();
    });
}

$(document).ready(function() {    
    // Setups
    setupSubmitModal();
    rcsa.registerMatchCallback(checkForScores);
    rcsa.registerErrorCallback(submitErrorHandler);
    rcsa.loadMatches();
});