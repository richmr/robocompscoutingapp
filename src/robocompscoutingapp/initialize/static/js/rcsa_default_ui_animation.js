/*
    This handles all of the UI activity for the scoring sample page.  It has been generalized to use arbitrary modes and 
    named scoring items.  If you follow the recipe in scoring_sample.html, you can use this UI script as is
    
    Please look for comments like this:
    // INTEGRATION TO THE APP SERVER HERE ^^^^^^^^^^^
    For critical rcsa_loader callbacks you must make in your own UI script for the scoring mechanisms to work.
*/

var global_match_and_team_data;


function greenFlash(e) {
    // Feedback for clicking on things.
    $(e).addClass("lgreen-background");
        setTimeout(() => {
            $(e).removeClass("lgreen-background");
          }, 150);
}

function beginButtonUISetup() {
    $(".begin_scoring").click(function (e) { 
        e.preventDefault();
        $(".match_and_team_selection").hide();
        $(".scoring").show();        
    });
}

function scoreFeedbackUISetup() {
    // The div that encapsulates a scoring element has its background changed.  
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

        // Set all the background colors per the mode data
        
        current_flag_status = rcsa.getFlagStatusForMode(selected_mode_name);
        // INTEGRATION TO THE APP SERVER HERE ^^^^^^^^^^^
        for (const [name, flagset] of Object.entries(current_flag_status)) {
            if (flagset) {
                $(`[data-scorename='${name}']`).parent().addClass("lgreen-background");    
            } else {
                $(`[data-scorename='${name}']`).parent().removeClass("lgreen-background");
            }
        }
    });

    
}

function setupSubmitReport() {
    $(".report_submit").click( function (e) {
        $("#sending_data_modal").modal({
            escapeClose: false,
            clickClose: false,
            showClose: false
        });

        // This is used for testing only
        let force_fail = false;
        // Check for the testing GET parameter
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has("force_fail")) {
            force_fail = true;
        }

        // CRITICAL INTEGRATION TO THE APP SERVER HERE::  REQUIRED!!
        // You do not need to use 'force_fail' in your code
        // You can simply call: rcsa.submitScore(scoreSubmitSuccess, scoreSubmitFailure);
        rcsa.submitScore(scoreSubmitSuccess, scoreSubmitFailure, force_fail);
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
        // Data wrangling handled by rcsa_loader.
        // Reset for scoring the next match
        $(".game_mode")[0].click();
        $("#pick_team_row").hide();
        $(".match_and_team_selection").show();
        $(".scoring").hide();
        $.modal.close();
    })
}

function matchAndTeamData(match_and_team_data) {
    // Receives a match and team data object from rcsa_loader
    console.log("matchAndTeamData called");
    global_match_and_team_data = match_and_team_data
    $(".match_selector").empty();
    $(".match_selector").append(`<option value=-1>Please choose your match</option>`);
    $(".team_selector").empty();
    $(".team_selector").append(`<option value=-1>Please choose a match first</option>`)
    for (const [matchNumber, match_info] of Object.entries(match_and_team_data.matches)) {
        $(".match_selector").append(`<option value=${matchNumber}>${match_info.description}</option>`); 
        // console.log(matchNumber, match_info);
    }            
}

function setUpMatchSelector(){
    // Watch for the change
    $(".match_selector").change(function (e) { 
        // e.preventDefault();
        chosen_match = $(".match_selector").val();
        if (chosen_match != -1) {
            // Set the options for pick team
            $(".team_selector").empty();
            $(".team_selector").append(`<option value=-1>Please choose your team</option>`);
            let match_data = global_match_and_team_data.matches[chosen_match];
            $(".team_selector").append(`<option value=${match_data["Red1"]}>Red 1: ${match_data["Red1"]}</option>`);
            $(".team_selector").append(`<option value=${match_data["Red2"]}>Red 2: ${match_data["Red2"]}</option>`);
            $(".team_selector").append(`<option value=${match_data["Red3"]}>Red 3: ${match_data["Red3"]}</option>`);
            $(".team_selector").append(`<option value=${match_data["Blue1"]}>Blue 1: ${match_data["Blue1"]}</option>`);
            $(".team_selector").append(`<option value=${match_data["Blue2"]}>Blue 2: ${match_data["Blue2"]}</option>`);
            $(".team_selector").append(`<option value=${match_data["Blue3"]}>Blue 3: ${match_data["Blue3"]}</option>`);
            
            $("#pick_team_row").show();
        }
    });
}

function setupTeamSelector() {
    // Watch for the change
    $(".team_selector").change(function (e) { 
        chosen_team = $(".team_selector").val();
        if (chosen_team != -1) {
            $("#scoring_controls").show();
        }
    });
}


function rcsaErrorHandler(err_msg) {
    // Called by rcsa_loader when there are errors in the application mechanics
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

$(document).ready(function() {
    
    // Setups
    beginButtonUISetup();
    scoreFeedbackUISetup();
    gameModeSelectionUISetup();
    setupSubmitReport();
    setUpMatchSelector();
    setupTeamSelector();
    setupDataModalCloseButton();

    // CRITICAL INTEGRATION TO THE APP SERVER HERE::  REQUIRED!!
    // Call this before other setup tasks as the RCSA mechanics will tie into the rest of the DOM
    rcsa.startup(matchAndTeamData, rcsaErrorHandler);
    // ^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
})