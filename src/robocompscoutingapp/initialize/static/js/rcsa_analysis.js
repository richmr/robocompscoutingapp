/*
    This handles the selection and display of recorded statistics and is applicable to any scoring page that passes validation
*/


var analysis_modes_and_items;
var stats_selection_table = null;
var stat_display_table = null;
var current_stored_stat_info = null;
var scoring_page_id;
var team_scores = null;

function getStoredStatInfo() {
    /*
        Structure for the stats.
        I need to know: 
            - which named items show which stats
                - mode to show
                - type to show
            - Groupings for headers
                - 

        {
            "scoring_page_id":page this stat selection is for,
            "chosen_stats": {
                "item_name": {
                    "mode1":[type1, type2],
                    "mode2":[type1],
                    ....
                },
                ...
            }
            ...
        }
        
    */
    let stored_selection = JSON.parse(localStorage.getItem("rcsa_stored_selected_stats"));
    if (stored_selection == null) {
        // Default set scoring_page_id to invalid number to allow for other comparisons to work well
        stored_selection = {"scoring_page_id":-99};
    }
    current_stored_stat_info = stored_selection;
}

function clearStoredStatInfo() {
    localStorage.setItem("rcsa_stored_selected_stats", null);
    getStoredStatInfo();
}

function saveStoredStatInfo() {
    localStorage.setItem("rcsa_stored_selected_stats", JSON.stringify(current_stored_stat_info));
}


function networkError(err_msg) {
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

function buildStatSelectionTableStructure() {
    stat_table = $("#stats_selection_table");

    function statSelectionTableHeader() {
        let thead = $("<thead>");
        // Header Groupings
        let tr_grouping = $("<tr>");
        tr_grouping.append('<th class="dt-head-center" rowspan="2">Scoring Item</th>');
        let modded_mode_names = Object.keys(analysis_modes_and_items.modes);
        modded_mode_names.push("Match");
        for (mode_name of modded_mode_names) {
            tr_grouping.append(`<th class="dt-head-center border-right" colspan="2">${mode_name}</th>`);
        }
        thead.append(tr_grouping);
        // Header labels
        let tr_labels = $("<tr>");
        for (mode_name of modded_mode_names) {
            tr_labels.append(`<th class="dt-head-center border-right" >Total</th>`);
            tr_labels.append(`<th class="dt-head-center border-right" >Average</th>`);
        }
        thead.append(tr_labels);
        stat_table.append(thead);
    }
    
    $("#stats_selection_table").empty();
    statSelectionTableHeader();
    // Add the table body
    stat_table.append('<tbody class="dt-body-center"></tbody>');
}

function dataStructureForSelectionTable() {
    /*
        Structure:
        [
            {
                "name":item_name,
                "cell_1": <i data-modename=modename data-scorename="item_name" data_stattype="total/average" class="stat-selector fa-regular fa-square"></i>
                "cell_2": etc..  
            }
        ]

    */
    let the_data = [];
   
    for (item_name of Object.keys(analysis_modes_and_items.scoring_items)) {
        let this_data = {"name":item_name};
        let modded_mode_names = Object.keys(analysis_modes_and_items.modes);
        modded_mode_names.push("Match");
        let cell_count = 0;
        for (mode_name of modded_mode_names) {
            for (stat_type of ["Total", "Average"]) {
                let key = `cell_${cell_count}`;
                let box_type = 'fa-square';
                if (current_stored_stat_info.chosen_stats != undefined) {
                    if (item_name in current_stored_stat_info.chosen_stats) {
                        if (mode_name in current_stored_stat_info.chosen_stats[item_name]) {
                            if (current_stored_stat_info.chosen_stats[item_name][mode_name].includes(stat_type)) {
                                // Mark as selected
                                box_type = "fa-square-check";
                            }
                        }
                    }
                }
                let value  = `<i data-modeName="${mode_name}" data-scorename="${item_name}" data-stattype="${stat_type}" class="stat-selector fa-regular ${box_type} fa-xl"></i>`
                this_data[key] = value;
                cell_count += 1;
            }
        }
        the_data.push(this_data);
    }
    
   return the_data;
}

function columnStructureForSelectionTable(data_structure) {
    let the_columns = [];
    
    if (data_structure.length > 0) {
        for (key of Object.keys(data_structure[0])) {
            the_columns.push({
                data: key,
                className: 'dt-body-center border-right'
            });
        }
    }

    return the_columns;
}

function showStatSelection() {
    $("#select_stats").show();
    $('#stats_display').hide();
    $('#stats_display_table_row').hide();

    if (stats_selection_table != null) {
        stats_selection_table.destroy();
        stats_selection_table = null;
    } 

    stats_selection_table = $("#stats_selection_table").DataTable( {
        autoWidth: false,
        searching: false,
        dom: "Bfrtip",
        data: dataStructureForSelectionTable(),
        columns: columnStructureForSelectionTable(dataStructureForSelectionTable())
    });
}

function getScoringItems () {
    // Call for DB answer
    $.ajax({
        type: "GET",
        url: "/api/gameModesAndScoringElements",
        dataType: "json",
        contentType: 'application/json',
        success: function (modes_and_items, text_status, jqXHR) {
            // Give the data to the display code
            console.log("Game Modes and scoring item data received");
            analysis_modes_and_items = modes_and_items;
            buildStatSelectionTableStructure();
            showStatSelection();
        },
        error: function( jqXHR, textStatus, errorThrown ) {
            if (jqXHR.status == 500) {
                let errorJSON = JSON.parse(jqXHR.responseText);
                errorThrown = errorJSON.detail
            }
            msg = `Unable to get game modes and scoring data because:\n${errorThrown}`;
            networkError(msg);
        }
    })
}

function getCurrentScores () {
    // Call for DB answer
    $.ajax({
        type: "GET",
        url: "/api/getAllScores",
        dataType: "json",
        contentType: 'application/json',
        success: function (recvd_scores, text_status, jqXHR) {
            // Give the data to the display code
            console.log("Team scores received");
            team_scores = recvd_scores;
            // Show stats table
            showSelectedStats();
        },
        error: function( jqXHR, textStatus, errorThrown ) {
            if (jqXHR.status == 500) {
                let errorJSON = JSON.parse(jqXHR.responseText);
                errorThrown = errorJSON.detail
            }
            msg = `Unable to get current team scores because:\n${errorThrown}`;
            networkError(msg);
        }
    })
}

function checkStoredPageInfo() {
    getStoredStatInfo();
    $.ajax({
        type: "GET",
        url: "/api/currentPageStatus",
        dataType: "json",
        contentType: 'application/json',
        success: function (recvd_page_status, text_status, jqXHR) {
            // Give the data to the display code
            console.log("current page status received", recvd_page_status.scoring_page_id);
            scoring_page_id = recvd_page_status.scoring_page_id;
            if (current_stored_stat_info.scoring_page_id != recvd_page_status.scoring_page_id) {
                clearStoredStatInfo();
                getScoringItems();
            } else {
                getCurrentScores();
            }
        },
        error: function( jqXHR, textStatus, errorThrown ) {
            if (jqXHR.status == 500) {
                let errorJSON = JSON.parse(jqXHR.responseText);
                errorThrown = errorJSON.detail
            }
            msg = `Unable to get current scoring page info because:\n${errorThrown}`;
            networkError(msg);
        }
    })

}

function convertSelectionsToDataStructure () {
    let picked_stats = $('.stat-selector').filter('.fa-square-check');
    if (picked_stats.length == 0) {
        networkError("Please select at least one stat to show.");
        return
    }
    let data_to_store = {
        "scoring_page_id":scoring_page_id,
        "chosen_stats": {}
    }
    picked_stats.each( function () {
        let item_name = $(this).data("scorename");
        let this_item_data = data_to_store["chosen_stats"][item_name];
        if (this_item_data == undefined) {
            this_item_data = {"total_columns":0};
            data_to_store["chosen_stats"][item_name] = this_item_data;
        }
        let modename = $(this).data("modename");
        let types_for_this_mode = this_item_data[modename];
        if (types_for_this_mode == undefined) {
            types_for_this_mode = [];
        }
        let type = $(this).data("stattype");
        types_for_this_mode.push(type);
        data_to_store["chosen_stats"][item_name].total_columns += 1;
        data_to_store["chosen_stats"][item_name][modename] = types_for_this_mode;
    });

    return data_to_store;
}

function showSelectedStats() {
    $("#stats_display").show();  // Remove when working
    if (stat_display_table != null) {
        // stat_display_table.draw();
        stat_display_table.destroy();
        stat_display_table = null;
    }

    // Make sure at least one stat has been selected
    if (current_stored_stat_info.chosen_stats === undefined) {
        networkError("Please select at least one stat to show.");
        showStatSelection();
        return
    }
    // let picked_stats = $('.stat-selector').filter('.fa-square-check');
    // if (picked_stats.length == 0) {
    //     networkError("Please select at least one stat to show.");
    //     return
    // }

    let stat_table = $("#stats_display_table");
    $("#select_stats").hide();

    if (team_scores == null) {
        $("#stats_display").show();
        $("#stats_display_table_row").hide();
        $("#stats_message").text("Loading current team scores");
        getCurrentScores();
        return
    }

    $("#stats_message").text("Event Stats");

    function statsDisplayTableHeader() {
        // console.log("Running statsDisplayTableHeader");
        $(stat_table).empty();
        let thead = $("<thead>");
        // Header Groupings
        let tr_grouping = $("<tr>");
        tr_grouping.append('<th class="dt-head-center" rowspan="2">Team Number</th>');
        let tr_labels = $("<tr>");
        for (const [stat_name, stat_info] of Object.entries(current_stored_stat_info.chosen_stats)) {
            tr_grouping.append(`<th class="dt-head-center border-right" colspan="${stat_info.total_columns}">${stat_name}</th>`);
            for (const [mode_name, chosen_types] of Object.entries(stat_info)) {
                if (mode_name === "total_columns") {
                    // We don't do anything with this
                    continue;
                }
                for (stat_type of chosen_types) {
                    let col_text = `${mode_name}<br>${stat_type}`;
                    tr_labels.append(`<th class="dt-head-center border-right">${col_text}</th>`);
                }
            }
        }
        thead.append(tr_grouping);
        thead.append(tr_labels);
        stat_table.append(thead);
    }
    let stat_data_structure = null;

    function statsData() {
        /*
        Structure:
        [
            {
                "teamNumber":team number,
                "cell_1": Value based on selected stats
                ..
            }
        ]
        */
        // console.log("Running statsData");

        let the_data = [];

        for (const [teamNumber, team_results] of Object.entries(team_scores.data)) {
            let this_data = {"teamNumber":teamNumber}
            let cell_count = 0;
            for (const [stat_name, stat_info] of Object.entries(current_stored_stat_info.chosen_stats)) {
                for (const [mode_name, chosen_types] of Object.entries(stat_info)) {
                    if (mode_name === "total_columns") {
                        continue
                    }
                    for (chosen_type of chosen_types) {
                        let _type = chosen_type.toLowerCase();
                        let cellname = `cell_${cell_count}`;
                        if (mode_name == "Match") {
                            this_data[cellname] = team_results.totals[stat_name][_type];
                        } else {
                            this_data[cellname] = team_results.by_mode_results[mode_name].scores[stat_name][_type];
                        }
                        cell_count += 1;
                    }
                }
            }
            the_data.push(this_data);
        }
        stat_data_structure = the_data;
        // console.log(the_data);
        return the_data;
    }

    function statsColumns() {
        // console.log("Running statsColumns");

        let the_columns = [];

        if (stat_data_structure.length > 0) {
            for (key of Object.keys(stat_data_structure[0])) {
                the_columns.push({
                    data: key,
                    className: 'dt-body-center border-right'
                });
            }
        }
    
        return the_columns;
    }
    // set up the stored data
    // current_stored_stat_info = convertSelectionsToDataStructure();
    // saveStoredStatInfo();

    // Generate header
    statsDisplayTableHeader();
    
    
    stat_display_table = $("#stats_display_table").DataTable({
        autoWidth: false,
        // dom: "Bfrtip",
        data: statsData(),
        columns: statsColumns(),
        pageLength: Object.keys(team_scores.data).length
    });
    
    $("#stats_display_table_row").show();
}

$(document).ready(function () {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has("clear_cache")) {
        clearStoredStatInfo();
    }

    $('#stats_selection_table').on( 'draw.dt', function () {
        $(".stat-selector").unbind("click");
        $(".stat-selector").click( function (e) {
            $(this).toggleClass('fa-square-check').toggleClass('fa-square');
        });
    } );

    $('#show_selected_stats').click( function (e) {
        // set up the stored data
        current_stored_stat_info = convertSelectionsToDataStructure();
        saveStoredStatInfo();
        showSelectedStats();
    });

    $('.choose_different_stats').click(function (e) {
        if (analysis_modes_and_items == null) {
            getScoringItems();
        } else {
            showStatSelection();
        }
    });

    checkStoredPageInfo();
    

});
