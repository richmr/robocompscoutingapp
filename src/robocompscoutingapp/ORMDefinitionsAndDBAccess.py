from pathlib import Path
from typing import List
from datetime import datetime

from sqlalchemy import (
    ForeignKey, 
    DateTime, 
    create_engine,
    Integer,
    UniqueConstraint
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    DeclarativeBase,
    relationship,
    session, 
    sessionmaker
)
from sqlalchemy.sql import func
# from sqlalchemy import Column, Integer, Text, Float, DateTime, ForeignKey, PickleType
# from sqlalchemy.orm import declarative_base, relationship

from robocompscoutingapp.GlobalItems import RCSA_Config #, rcsa_database_name

class rcsa_scoring_tables(DeclarativeBase):
    
    def fromDict(self, data_in:dict):
        for n, (k,v) in enumerate(data_in.items()):
            if hasattr(self, k):
                setattr(self, k, v)
        return self
    
    def toDict(self):
        toreturn = {}
        for attr in dir(self):
            if not attr.startswith("_"):
                toreturn[attr] = getattr(self, attr)
        return toreturn

class ScoringPageStatus(rcsa_scoring_tables):
    __tablename__ = "ScoringPageStatus"

    scoring_page_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scoring_page_hash: Mapped[str] = mapped_column(default="none")
    # Has this page passed validation
    validated: Mapped[bool] = mapped_column(default=False)
    # Has this page been integrated into the database for scoring
    integrated: Mapped[bool] = mapped_column(default=False)
    # Has this page passed rcsa automatic testing
    tested: Mapped[bool] = mapped_column(default=False)

class ModesForScoringPage(rcsa_scoring_tables):
    __tablename__ = "ModesForScoringPage"
    __table_args__ = (
        UniqueConstraint("scoring_page_id", "mode_name", name="unique_modes_per_page"),
    )

    mode_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scoring_page_id: Mapped[int] = mapped_column(ForeignKey("ScoringPageStatus.scoring_page_id"))
    mode_name: Mapped[str]
    

class ScoringItemsForScoringPage(rcsa_scoring_tables):
    __tablename__ = "ScoringItemsForScoringPage"
    __table_args__ = (
        UniqueConstraint("scoring_page_id", "name", name="scoringItemsU_1"),
    )

    scoring_item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scoring_page_id: Mapped[int] = mapped_column(ForeignKey("ScoringPageStatus.scoring_page_id"))
    name: Mapped[str]
    type: Mapped[str]

# Items below here abandon my convention of parameters being all lower_case to better match the output from the First Event APIs

class TeamsForEvent(rcsa_scoring_tables):
    __tablename__ = "TeamsForEvent"
    __table_args__ = (
        UniqueConstraint("eventCode", "teamNumber", name="TeamsForEvent_unique_team_per_event"),
    )
    team_for_event_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    eventCode: Mapped[str]
    nameShort: Mapped[str]
    teamNumber: Mapped[int]

class MatchesForEvent(rcsa_scoring_tables):
    __tablename__ = "MatchesForEvent"
    __table_args__ = (
        UniqueConstraint("eventCode", "matchNumber", name="MatchesForEvent_uniq_match_per_event"),
    )

    match_per_event: Mapped[int] = mapped_column(primary_key=True, autoincrement=True) 
    eventCode:Mapped[str]
    description:Mapped[str]
    matchNumber:Mapped[int]
    Red1:Mapped[int]
    Red2:Mapped[int]
    Red3:Mapped[int]
    Blue1:Mapped[int]
    Blue2:Mapped[int]
    Blue3:Mapped[int]
    scored:Mapped[bool] = mapped_column(default=False)

class ScoresForEvent(rcsa_scoring_tables):
    __tablename__ = "ScoresForEvent"
    __table_args__ = (
        UniqueConstraint("scoring_page_id", "eventCode", "teamNumber", "scoring_item_id", "matchNumber", "mode_id",
                         name="ScoresForEvent_uniq_score_item_per_team_per_event"),
    )

    score_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scoring_page_id: Mapped[int]
    mode_id: Mapped[int]
    matchNumber: Mapped[int]
    eventCode:Mapped[str]
    teamNumber:Mapped[int]
    scoring_item_id:Mapped[int]
    value:Mapped[str] # Strings are most flexible here, interpretation up to the code that handles "type" of scoring item


######### DB ACCESS ############    

class RCSA_DB:
    """
    Class that connects to the database file, ensures all the required tables are built, and provides ready access to session
    """

    _sqlASessionMaker = None
    _sqlAConnectionStr = None

    @classmethod
    def getSQLSession(cls, reset:bool = False) -> session:
        """
        Class method to access the singleton SQL Alchemy session maker.
        Use like 'with RCSA_DB.getSQLSession() as dbsession:'

        Parameters
        ----------
        reset:bool
            Forces the stored _sqlASessionMaker to reset to None.  This is mainly used in testing to ensure tests work with the desired database        
        
        Returns
        -------
        session
            SQLAlchemy session object
        """
        if reset:
            cls._sqlASessionMaker = None
            cls._sqlAConnectionStr = None

        if cls._sqlASessionMaker is None:
            database_file = Path(RCSA_Config.getConfig().ServerConfig.scoring_database)
            # Make sure dir exist
            database_file.parent.mkdir(parents=True, exist_ok=True)
            cls._sqlAConnectionStr = f"sqlite:///{database_file}"
            sqlAEngine = create_engine(cls._sqlAConnectionStr)
            cls._sqlASessionMaker = sessionmaker(bind=sqlAEngine)
            rcsa_scoring_tables.metadata.create_all(sqlAEngine)
        return cls._sqlASessionMaker()

