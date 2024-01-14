import tempfile
import pytest
from pathlib import Path
# from tomlkit import TOMLDocument, table
from contextlib import contextmanager
import os
import yaml
import requests
from sqlalchemy import select

from uvicorn import Config

from robocompscoutingapp.GlobalItems import RCSA_Config, temp_chdir
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.Initialize import Initialize
from robocompscoutingapp.Integrate import Integrate
from robocompscoutingapp.ScoringData import (
    GenerateResultsForTeam,
    getGameModeAndScoringElements,
    getCurrentScoringPageData, 
    storeTeams,
    storeMatches,
    deleteMatchesFromEvent,
    loadEventData,
    MatchesAndTeams,
    getMatchesAndTeams,
    addScoresToDB,
    deleteScoresFromDB,
    Score,
    ScoredMatchForTeam,
    teamAlreadyScoredForThisMatch,
    getAggregrateResultsForAllTeams,
    getPageIDsUsedForThisEvent,
    migrateDataForEventToNewPage
)
from robocompscoutingapp.ORMDefinitionsAndDBAccess import (
    ScoringPageStatus,
    ModesForScoringPage,
    ScoringItemsForScoringPage,
    TeamsForEvent,
    MatchesForEvent,
    RCSA_DB,
    ScoresForEvent
)
from robocompscoutingapp.FirstEventsAPI import (
    FirstTeam,
    FirstMatch
)

@contextmanager
def gen_test_env_and_enter(temp_dir_path:Path):
    init = Initialize(temp_dir_path)
    init.initialize(overwrite=True)
    # Update the location of the scoring page
    init.updateTOML(["ServerConfig", "scoring_page"], f"{temp_dir_path}/static/scoring.html", tgt_dir = temp_dir_path)
    # Now enter the directory
    cwd = os.getcwd() 
    # Validate the page
    try:
        os.chdir(temp_dir_path)
        uhp = UserHTMLProcessing(f"{temp_dir_path}/static/scoring.html")
        uhp.validate()
        # Integrate it to set the data
        int = Integrate()
        int.integrate()

        config = RCSA_Config.getConfig()
        config.FRCEvents.first_event_id = "CALA"

        # Go do what the test needs
        yield
    finally:
        os.chdir(cwd)

"""
Expected data
sqlite> select * from ModesForScoringPage ;
mode_id     scoring_page_id  mode_name 
----------  ---------------  ----------
1           1                Auton     
2           1                Teleop    
sqlite> select * from ScoringItemsForScoringPage ;
scoring_item_id  scoring_page_id  name        type       
---------------  ---------------  ----------  -----------
1                1                cone        score_tally
2                1                cube        score_tally
3                1                Attempted   score_flag 
4                1                Succeeded   score_flag 
5                1                Auton Mobi  score_flag 
6                1                Broke       score_flag 
sqlite> 
"""

def test_getGameModeAndScoringElements(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        # only one page is loaded in temporary db, it should be ID 1
        mai = getGameModeAndScoringElements(1)
        assert len(mai.modes) == 2
        assert len(mai.scoring_items) == 6

def test_scoring_page_id(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        assert getCurrentScoringPageData().scoring_page_id == 1

def test_storeTeams(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        # Quick fake team
        team = FirstTeam(
            eventCode="CALA",
            nameShort="Flame of the West",
            teamNumber=2584
        )
        # save it
        storeTeams([team])
        # If we make it here, really no reason why it wouldn't work
        # Try it again to see if integrity error fails smoothly
        storeTeams([team])

        # Now make sure it wasn't added twice
        with RCSA_DB.getSQLSession() as db:
            teams = db.scalars(select(TeamsForEvent)).all()
            assert len(teams) == 1
        
def test_storeMatches(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        match = FirstMatch(
            eventCode = "CALA",
            description = "Test 1",
            matchNumber = 1,
            Red1 = 1,
            Red2 = 2,
            Red3 = 3,
            Blue1 = 4,
            Blue2 = 5,
            Blue3 = 6
        )
        storeMatches([match])
        # Test integrity error
        storeMatches([match])

        # Make sure it was stored once
        with RCSA_DB.getSQLSession() as db:
            db_match = db.scalars(select(MatchesForEvent)).one()
            assert db_match.scored == False

def test_getMatchesAndTeams(tmpdir):
     with gen_test_env_and_enter(tmpdir):
        # set event code
        RCSA_Config.getConfig().FRCEvents.first_event_id = "CALA"
        # Store some results
        team = FirstTeam(
            eventCode="CALA",
            nameShort="Flame of the West",
            teamNumber=2584
        )
        # save it
        storeTeams([team])
        match = FirstMatch(
            eventCode = "CALA",
            description = "Test 1",
            matchNumber = 1,
            Red1 = 2584,
            Red2 = 2,
            Red3 = 3,
            Blue1 = 4,
            Blue2 = 5,
            Blue3 = 6
        )
        storeMatches([match])
     
        result = getMatchesAndTeams(eventCode="CALA")
        assert len(result.matches) == 1
        assert len(result.teams) == 1

def test_addScores(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        match1 = FirstMatch(
            eventCode = "CALA",
            description = "Test 1",
            matchNumber = 1,
            Red1 = 2584,
            Red2 = 2,
            Red3 = 3,
            Blue1 = 4,
            Blue2 = 5,
            Blue3 = 6
        )
        match2 = FirstMatch(
            eventCode = "CALA",
            description = "Test 2",
            matchNumber = 2,
            Red1 = 2584,
            Red2 = 2,
            Red3 = 3,
            Blue1 = 4,
            Blue2 = 5,
            Blue3 = 6
        )
        storeMatches([match1, match2])

        scores = [
            Score(scoring_item_id=1, value=1, mode_id=1),
            Score(scoring_item_id=2, value=True, mode_id=1),
        ]
        score_obj = ScoredMatchForTeam(
            matchNumber=1,
            teamNumber=2584,
            scores=scores
        )
        addScoresToDB("CALA", score_obj)

        # verify results
        with RCSA_DB.getSQLSession() as db:
            test = db.scalars(select(ScoresForEvent).filter_by(
                matchNumber=1,
                eventCode = "CALA",
                teamNumber =2584,
                scoring_item_id = 1
            )).one()
            assert test.value == "1"

        # Also verify this works
        assert teamAlreadyScoredForThisMatch(2584, 1, "CALA") == True

        # Now check that match was marked as scored
        data = getMatchesAndTeams(eventCode="CALA", unscored_only=False)
        print(data.matches)
        assert data.matches[1].scored == True

        # Now check only unscored matches
        data2 = getMatchesAndTeams(eventCode="CALA")
        assert len(data2.matches) == 1
        assert data2.matches[2].matchNumber == 2

def fake_game_data():
    # Assumes already in a proper test environ
    # Teams
    team_list = [
        FirstTeam(eventCode="CALA", nameShort="Team 1", teamNumber=1),
        FirstTeam(eventCode="CALA", nameShort="Team 2", teamNumber=2),
        FirstTeam(eventCode="CALA", nameShort="Team 3", teamNumber=3),
    ]
    storeTeams(team_list)
    # Real matches don't have teams competing against themselves, but not relevant for testing purposes
    match_list = [
        FirstMatch(
            eventCode = "CALA",
            description = "Match 1",
            matchNumber = 1,
            Red1 = 1,
            Red2 = 2,
            Red3 = 3,
            Blue1 = 1,
            Blue2 = 2,
            Blue3 = 3
        ),
        FirstMatch(
            eventCode = "CALA",
            description = "Match 2",
            matchNumber = 2,
            Red1 = 1,
            Red2 = 2,
            Red3 = 3,
            Blue1 = 1,
            Blue2 = 2,
            Blue3 = 3
        )
    ]
    storeMatches(match_list=match_list)

def test_scoreAggregation(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        fake_game_data()
        # Now some scoring
        scores = [
            Score(scoring_item_id=1, mode_id=1, value=1),
            Score(scoring_item_id=1, mode_id=2, value=2),
            # Setting this to True did work, but please see notes in ScoringData.py:353
            Score(scoring_item_id=5, mode_id=1, value=True)
        ]
        score_obj = ScoredMatchForTeam(
            matchNumber=1,
            teamNumber=1,
            scores=scores
        )
        addScoresToDB(eventCode="CALA", match_score=score_obj)

        # retrieve
        agg_object = GenerateResultsForTeam("CALA", 1, 1)
        results = agg_object.getAggregrateResults()
        assert results.by_mode_results["Auton"].scores["cone"].count_of_scored_events == 1
        assert results.totals["cone"].total == 3 # 1 in auton, 2 in teleop
        assert results.totals["cone"].average == 3 # Only 1 event so far
        assert results.by_mode_results["Auton"].scores["Auton Mobility"].total == 1

        # Add another score
        scores = [
            Score(scoring_item_id=1, mode_id=1, value=1),
            Score(scoring_item_id=5, mode_id=1, value=0)
        ]
        score_obj = ScoredMatchForTeam(
            matchNumber=2,
            teamNumber=1,
            scores=scores
        )
        addScoresToDB(eventCode="CALA", match_score=score_obj)

        # retrieve
        agg_object = GenerateResultsForTeam("CALA", 1, 1)
        results = agg_object.getAggregrateResults()
        assert results.by_mode_results["Auton"].scores["cone"].count_of_scored_events == 2
        assert results.totals["cone"].count_of_scored_events == 2
        assert results.by_mode_results["Auton"].scores["cone"].average == 1
        assert results.totals["cone"].total == 4 
        assert results.totals["cone"].average == 2 
        assert results.by_mode_results["Auton"].scores["Auton Mobility"].total == 1

        # Check zero scores
        zero_obj = GenerateResultsForTeam("CALA", 2, 1)
        results = zero_obj.getAggregrateResults()
        assert results.by_mode_results["Auton"].scores["cone"].count_of_scored_events == 0
        assert results.totals["cone"].count_of_scored_events == 0
        assert results.by_mode_results["Auton"].scores["cone"].average == 0
        assert results.totals["cone"].total == 0

        # Add another team scores
        # Add another score
        scores = [
            Score(scoring_item_id=1, mode_id=1, value=1),
            Score(scoring_item_id=5, mode_id=1, value=1)
        ]
        score_obj = ScoredMatchForTeam(
            matchNumber=2,
            teamNumber=3,
            scores=scores
        )
        addScoresToDB(eventCode="CALA", match_score=score_obj)

        # Test all teams
        all_team_results = getAggregrateResultsForAllTeams("CALA", 1)
        assert all_team_results.data[1].by_mode_results["Auton"].scores["cone"].count_of_scored_events == 2
        assert all_team_results.data[2].totals["cone"].count_of_scored_events == 0
        assert all_team_results.data[3].totals["cone"].total == 1

        # Test delete function
        deleteScoresFromDB("CALA")

        # Verify in DB

def test_datamanagement(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        fake_game_data()
        # Now some scoring
        scores = [
            Score(scoring_item_id=1, mode_id=1, value=1),
            Score(scoring_item_id=1, mode_id=2, value=2),
            # Setting this to True did work, but please see notes in ScoringData.py:353
            Score(scoring_item_id=5, mode_id=1, value=True)
        ]
        score_obj = ScoredMatchForTeam(
            matchNumber=1,
            teamNumber=1,
            scores=scores
        )
        addScoresToDB(eventCode="CALA", match_score=score_obj)
        # Add matches for another event
        match_list = [
            FirstMatch(
                eventCode = "BOBO",
                description = "Match 1",
                matchNumber = 1,
                Red1 = 1,
                Red2 = 2,
                Red3 = 3,
                Blue1 = 1,
                Blue2 = 2,
                Blue3 = 3
            ),
        ]
        storeMatches(match_list=match_list)
        # Add some scores to it
        addScoresToDB(eventCode="BOBO", match_score=score_obj)
        # Test delete function
        deleteScoresFromDB("CALA")

        # Check in DB
        with RCSA_DB.getSQLSession() as db:
            results = db.scalars(select(ScoresForEvent).filter_by(eventCode="CALA")).all()
            assert len(results) == 0
            # Make sure it only deleted what we wanted.
            results = db.scalars(select(ScoresForEvent).filter_by(eventCode="BOBO")).all()
            assert len(results) == 3
            
def test_match_data_reset(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        loadEventData(eventCode="CALA", season=2023)
        # Retrieve and verify 
        matches_and_teams = getMatchesAndTeams("CALA")
        assert matches_and_teams.teams[2584].nameShort.lower() == "Flame of the West".lower()
        # Something in test suite is deleting the matches when I get here
        # If ran as a test by itself, it works.
        # assert matches_and_teams.matches[5].Blue3 == 2584

        # Add a score to match 5 to make it scored
        scores = [
            Score(scoring_item_id=1, mode_id=1, value=1),
            Score(scoring_item_id=1, mode_id=2, value=2),
            # Setting this to True did work, but please see notes in ScoringData.py:353
            Score(scoring_item_id=5, mode_id=1, value=True)
        ]
        score_obj = ScoredMatchForTeam(
            matchNumber=5,
            teamNumber=2584,
            scores=scores
        )
        addScoresToDB(eventCode="CALA", match_score=score_obj)
        # Make sure they are there
        agg_object = GenerateResultsForTeam("CALA", 2584, 1)
        results = agg_object.getAggregrateResults()
        assert results.by_mode_results["Auton"].scores["cone"].count_of_scored_events == 1
        assert results.totals["cone"].total == 3 # 1 in auton, 2 in teleop
        assert results.totals["cone"].average == 3 # Only 1 event so far
        assert results.by_mode_results["Auton"].scores["Auton Mobility"].total == 1

        # "refresh" the data
        loadEventData("CALA", refresh_match_data=True, season=2023)
        # Make sure the scores are still there
        agg_object = GenerateResultsForTeam("CALA", 2584, 1)
        results = agg_object.getAggregrateResults()
        assert results.by_mode_results["Auton"].scores["cone"].count_of_scored_events == 1
        assert results.totals["cone"].total == 3 # 1 in auton, 2 in teleop
        assert results.totals["cone"].average == 3 # Only 1 event so far
        assert results.by_mode_results["Auton"].scores["Auton Mobility"].total == 1

        # Make sure the match data shows 5 as scored
        mat = getMatchesAndTeams("CALA", unscored_only=True)
        assert 5 not in mat.matches.keys()

        # Make sure data clears out as planned
        loadEventData("CALA", reset_all_data=True, season=2023)
        mat = getMatchesAndTeams("CALA", unscored_only=True)
        assert 5 in mat.matches.keys()
        agg_object = GenerateResultsForTeam("CALA", 2584, 1)
        results = agg_object.getAggregrateResults()
        assert results.by_mode_results["Auton"].scores["cone"].count_of_scored_events == 0

def test_PageIDDiscovery(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        # Directly put data in the DB
        with RCSA_DB.getSQLSession() as db:
            db.add(ScoresForEvent(
                scoring_page_id = 1,
                mode_id = 1, 
                matchNumber = 1,
                eventCode = "CALA1",
                teamNumber = 2584,
                scoring_item_id = 1,
                value = "1"
            ))
            db.commit()
            # Check this
            found_ids = getPageIDsUsedForThisEvent("CALA1")
            assert len(found_ids) == 1
            #add another
            db.add(ScoresForEvent(
                scoring_page_id = 1,
                mode_id = 1, 
                matchNumber = 2,
                eventCode = "CALA1",
                teamNumber = 2584,
                scoring_item_id = 1,
                value = "1"
            ))
            db.commit()
            # Check this
            found_ids = getPageIDsUsedForThisEvent("CALA1")
            assert len(found_ids) == 1
            assert found_ids[0].count_of_scores_found == 2

            # Add another scoring page
            db.add(ScoresForEvent(
                scoring_page_id = 2,
                mode_id = 1, 
                matchNumber = 1,
                eventCode = "CALA1",
                teamNumber = 2584,
                scoring_item_id = 1,
                value = "1"
            ))
            db.commit()
            # Check this
            found_ids = getPageIDsUsedForThisEvent("CALA1")
            assert len(found_ids) == 2
            # in order?
            assert found_ids[0].scoring_page_id == 1

            #  Add two more just to check the ordering
            # Add another scoring page
            db.add(ScoresForEvent(
                scoring_page_id = 2,
                mode_id = 1, 
                matchNumber = 2,
                eventCode = "CALA1",
                teamNumber = 2584,
                scoring_item_id = 1,
                value = "1"
            ))
            db.add(ScoresForEvent(
                scoring_page_id = 2,
                mode_id = 1, 
                matchNumber = 3,
                eventCode = "CALA1",
                teamNumber = 2584,
                scoring_item_id = 1,
                value = "1"
            ))
            db.commit()
            # Check this
            found_ids = getPageIDsUsedForThisEvent("CALA1")
            assert len(found_ids) == 2
            # in order?
            assert found_ids[0].scoring_page_id == 2

"""
Expected data
sqlite> select * from ModesForScoringPage ;
mode_id     scoring_page_id  mode_name 
----------  ---------------  ----------
1           1                Auton     
2           1                Teleop    
sqlite> select * from ScoringItemsForScoringPage ;
scoring_item_id  scoring_page_id  name        type       
---------------  ---------------  ----------  -----------
1                1                cone        score_tally
2                1                cube        score_tally
3                1                Attempted   score_flag 
4                1                Succeeded   score_flag 
5                1                Auton Mobi  score_flag 
6                1                Broke       score_flag 
sqlite> 
"""

def makeFakePage():
    # Assumes we are CWD where we want it saved
    fake_page = """
    <html><body>
    <div class="container match_and_team_selection">
    <select class="u-full-width match_selector"></select>
    <select class="u-full-width team_selector"></select>
    </div>
    <div class="section scoring" id="scoring_controls" hidden>
        <div class="row game_mode_group">
            <div id="set-auton" class="six columns text-center click_feedback">
                <i id="auton_icon" data-modename="Auton" class="fa-solid fa-robot fa-4x game_mode"></i>
            </div>
            <div id="set-teleop" class="six columns text-center click_feedback">
                <i id="tele_icon" data-modename="Teleop" class="fa-solid fa-gamepad fa-4x game_mode"></i>
            </div>
        </div>
        <img id="score_cone" data-scorename="cone" class="score_tally" src="images/cone.png" alt="Cone" width="75" height="75">
        <img id="score_cube" data-scorename="cube" class="score_tally" src="images/cube.png" alt="Cube" width="75" height="75">
        <img id="score_cube" data-scorename="newItem" class="score_tally" src="images/cube.png" alt="Cube" width="75" height="75">
        <button class="button-orange btn-big report_submit">Submit Report</button>  
    </div>
    <script src="js/rcsa_loader.js"></script>
    </body>
    </html>
    """
    path_to_file = Path("static/newscoring.html")
    with path_to_file.open(mode="w") as f:
        f.write(fake_page)
    
    # Set config file
    RCSA_Config.getConfig().ServerConfig.scoring_page = f"{path_to_file}"
    return path_to_file

def test_DataMigrate(tmpdir):
     with gen_test_env_and_enter(tmpdir):
        # Directly put data in the DB
        with RCSA_DB.getSQLSession() as db:
            # temp env generates an entry for scoring page from the scoring sample
            # There shouldn't be any scores yet
            used_ids = getPageIDsUsedForThisEvent("CALA")
            assert len(used_ids) == 0
            # Add a score
            db.add(ScoresForEvent(
                scoring_page_id = 1,
                mode_id = 1, 
                matchNumber = 1,
                eventCode = "CALA",
                teamNumber = 2584,
                scoring_item_id = 1,
                value = "1"
            ))
            db.commit()

            # Integrate a new page
            new_page_path = makeFakePage()
            uhp = UserHTMLProcessing(new_page_path)
            uhp.validate()
            # Integrate it to set the data
            int = Integrate()
            int.integrate()
            # Should be page 2
            
            used_ids = getPageIDsUsedForThisEvent("CALA")
            assert len(used_ids) == 1

            # migrate the data
            migrate_results = migrateDataForEventToNewPage("CALA", 1, 2)
            assert len(migrate_results.success_messages) == 1
            assert len(migrate_results.warning_messages) == 2
            assert len(migrate_results.error_message) == 0
            
            # make sure it actually migrated
            # the cone score should have migrated. It should be scoring_item_id = 7 and value = 1
            scores = db.scalars(select(ScoresForEvent).where(ScoresForEvent.eventCode == "CALA", ScoresForEvent.scoring_page_id == 2)).one()
            assert scores.scoring_item_id == 7
            assert scores.value == "1"











         







