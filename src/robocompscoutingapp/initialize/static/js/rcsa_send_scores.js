// Script to find and send stored scores

var stored_scores = [];

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
        $('#saved_scores_table').DataTable( {
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

function checkForScores(){
    let found_scores = rcsa.getSavedScores();
    let events = Object.keys(found_scores);
    if (events.length > 1) {
        // Previous events have been stored
        // Go find out what event to look at
    } else {
        stored_scores = found_scores[events[0]];
        scoresReady();
    }
}

function submitErrorHandler(err_msg) {
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

function submitSuccessHandler() {
    $.toast({ 
        text : "Score successfully sent!", 
        showHideTransition : 'slide',  // It can be plain, fade or slide
        bgColor : 'green',              // Background color for toast
        textColor : '#eee',            // text color
        allowToastClose : true,       // Show the close button or not
        hideAfter : 2000,              // `false` to make it sticky or time in miliseconds to hide after
        stack : 5,                     // `fakse` to show one stack at a time count showing the number of toasts that can be shown at once
        textAlign : 'left',            // Alignment of text i.e. left, right, center
        position : 'top-left'       // bottom-left or bottom-right or bottom-center or top-left or top-right or top-center or mid-center or an object representing the left, right, top, bottom values to position the toast on page
      });
}

function setupSubmitButton() {

}

$(document).ready(function() {
    
    // Setups
    checkForScores();
    
});