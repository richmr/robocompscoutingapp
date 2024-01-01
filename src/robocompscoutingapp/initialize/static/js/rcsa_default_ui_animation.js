
function greenFlash(e) {
    $(e).addClass("lgreen-background");
        setTimeout(() => {
            $(e).removeClass("lgreen-background");
          }, 200);
}

function beginButtonUISetup() {
    $(".begin_scoring").click(function (e) { 
        e.preventDefault();
        $(".match_and_team_selection").hide();
        $(".scoring").show();        
    });
}

function scoreFeedbackUISetup() {
    $( ".score_flag" ).each(function( index ) {
        $(this).click( function (e) { 
            $(this).parent().toggleClass("lgreen-background");
        });
    });
    
    $( ".score_tally" ).each(function( index ) {
        $(this).click( function (e) { 
            greenFlash($(this).parent());
        });
    });
}

function gameModeSelectionUISetup() {
    $(".game_mode").click(function (e) {
        selected_mode_name = $(this).data("modename");
        // Turn this one green
        $(this).addClass("lgreen-background");
        // Remove green from all others
        $(`.game_mode:not([data-modename='${selected_mode_name}'])`).removeClass("lgreen-background");

        // From: https://stackoverflow.com/questions/17462682/set-element-to-unclickable-and-then-to-clickable
        // Make items that have this specified mode clickable
        $("[data-onlyForMode]").filter(`[data-onlyForMode=${selected_mode_name}]`).css("pointer-events","auto");
        
        // Make items that are have a specified mode that is not not this mode unclickable
        $("[data-onlyForMode]").filter(`[data-onlyForMode!=${selected_mode_name}]`).css("pointer-events","none");
    });

    
}

function setupSubmitReport() {
    $(".report_submit").click( function (e) {
        $("#sending_data_modal").modal({
            escapeClose: false,
            clickClose: false,
            showClose: false
        });
        // CRITICAL INTEGRATION TO THE APP SERVER HERE::  REQUIRED!!
        rcsa.submitScore(scoreSubmitSuccess, scoreSubmitFailure);
        // ^^^^^^^^^^^^^^^^^^^^^^^^^^^
    })
}

function scoreSubmitSuccess() {
    $("#sending_data_modal_title").text('Success!');
    $("#submit_message").text("Data saved to central database.");
    $("#data_modal_buttons").show();
}

function scoreSubmitFailure(errMsg) {
    $("#sending_data_modal_title").text('Whoops!');
    $("#submit_message").text(errMsg);
    $("#data_modal_buttons").show();
}

function setupDataModalCloseButton(errMsg) {
    $("#close_modal_next_match").click(function (e) {

    })
}

function matchAndTeamData(match_and_team_data) {
    // Receives a match and team data object from rcsa_loader
    console.log("matchAndTeamData called");
}

function rcsaErrorHandler(err_msg) {
    // Called by rcsa_loader when there are errors in the application mechanics
    console.error(err_msg);
}

$(document).ready(function() {
    
    // Setups
    beginButtonUISetup();
    scoreFeedbackUISetup();
    gameModeSelectionUISetup();
    setupSubmitReport();

    // CRITICAL INTEGRATION TO THE APP SERVER HERE::  REQUIRED!!
    // Call this before other setup tasks as the RCSA mechanics will tie into the rest of the DOM
    rcsa.startup(matchAndTeamData, rcsaErrorHandler);
    // ^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
})