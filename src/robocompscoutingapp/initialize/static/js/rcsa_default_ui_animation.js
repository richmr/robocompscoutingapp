
var global_match_and_team_data;


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
        // Data wrangling handled by rcsa_loader.
        
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
        stack : 5,                     // `fakse` to show one stack at a time count showing the number of toasts that can be shown at once
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

    // CRITICAL INTEGRATION TO THE APP SERVER HERE::  REQUIRED!!
    // Call this before other setup tasks as the RCSA mechanics will tie into the rest of the DOM
    rcsa.startup(matchAndTeamData, rcsaErrorHandler);
    // ^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
})