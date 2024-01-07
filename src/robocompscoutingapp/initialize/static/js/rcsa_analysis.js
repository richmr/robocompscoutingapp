
var analysis_modes_and_items;
var stats_selection_table = null;

// first step: get all the scoring items and build the table structure

function networkError(err_msg) {
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

function buildStatSelectionTableStructure() {
    stat_table = $("#stats_selection_table");

    function statSelectionTableHeader() {
        let thead = $("<thead>");
        // Header Groupings
        let tr_grouping = $("<tr>");
        tr_grouping.append('<th class="dt-head-center" rowspan="2">Scoring Item</th>');
        let modded_mode_names = Object.keys(analysis_modes_and_items.modes);
        modded_mode_names.push("Totals");
        for (mode_name of modded_mode_names) {
            tr_grouping.append(`<th class="dt-head-center" colspan="2">${mode_name}</th>`);
        }
        thead.append(tr_grouping);
        // Header labels
        let tr_labels = $("<tr>");
        for (mode_name of modded_mode_names) {
            tr_labels.append(`<th class="dt-head-center" >Total</th>`);
            tr_labels.append(`<th class="dt-head-center" >Average</th>`);
        }
        thead.append(tr_labels);
        stat_table.append(thead);
    }
    
    $("#stats_selection_table").empty();
    statSelectionTableHeader();
    // Add the table body
    stat_table.append('<tbody class="dt-body-center"></tbody>');
}

function dataAndColumnStructureForTable() {
    /*
        Structure:
        [
            {
                "name":item_name,
                "cell_1": <i data-modename=modename data-scorename="item_name" data_stattype="total/average" class="stat-selector fa-regular fa-square"></i>
                "cell_2": etc..  
            }
        ]

        Returns the data and the column structure.
    */
    let the_data = [];
    let the_columns = [];
   
    for (item_name of Object.keys(analysis_modes_and_items.scoring_items)) {
        let this_data = {"name":item_name};
        let modded_mode_names = Object.keys(analysis_modes_and_items.modes);
        modded_mode_names.push("Totals");
        let cell_count = 0;
        for (mode_name of modded_mode_names) {
            for (stat_type of ["Total", "Average"]) {
                let key = `cell_${cell_count}`;
                let value  = `<i data-modeName="${mode_name}" data-scorename="${item_name}" data_stattype="${stat_type}" class="stat-selector fa-regular fa-square fa-xl"></i>`
                this_data[key] = value;
                cell_count += 1;
            }
        }
        the_data.push(this_data);
    }
    
    if (the_data.length > 0) {
        for (key of Object.keys(the_data[0])) {
            the_columns.push({
                data: key,
                className: 'dt-body-center'
            });
        }
    }

    return [the_data, the_columns];
}

function showStatSelection() {
    $("#select_stats").show();
    if (stats_selection_table == null) {
        const [table_data, table_columns] = dataAndColumnStructureForTable();
        stats_selection_table = $("#stats_selection_table").DataTable( {
            autoWidth: false,
            searching: false,
            dom: "Bfrtip",
            data: table_data,
            columns: table_columns,
        });
    }
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
            console.log("Game Modes and scoring item data recieved");
            analysis_modes_and_items = modes_and_items;
            buildStatSelectionTableStructure();
            showStatSelection();
        },
        error: function( jqXHR, textStatus, errorThrown ) {
            msg = `Unable to get game modes and scoring data because:\n${errorThrown}`;
            networkError(msg);
        }
    })
}




$(document).ready(function () {
    $('#stats_selection_table').on( 'draw.dt', function () {
        $(".stat-selector").unbind("click");
        $(".stat-selector").click( function (e) {
            $(this).toggleClass('fa-square-check').toggleClass('fa-square');
        });
    } );

    getScoringItems();
    

});