
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
    })
}

$(document).ready(function() {
    // Setups
    beginButtonUISetup();
    scoreFeedbackUISetup();
    gameModeSelectionUISetup();
    
})