"""
Mock data for testing the DJ Song Recommender application.
"""

from typing import List
from .models import Song


def get_mock_recommendations() -> List[Song]:
    """Get a list of mock song recommendations for testing."""
    return [
        Song(title="Losing It", artist="FISHER", genre="Tech House"),
        Song(title="Rhyme Dust", artist="MK & Dom Dolla", genre="Tech House"),
        Song(title="Gecko (Overdrive)", artist="Oliver Heldens", genre="Future House"),
        Song(title="Mammoth", artist="Dimitri Vegas & Like Mike", genre="Big Room House"),
        Song(title="Animals", artist="Martin Garrix", genre="Big Room House"),
        Song(title="Tremor", artist="Dimitri Vegas & Like Mike", genre="Big Room House"),
        Song(title="Epic", artist="Sandro Silva & Quintino", genre="Big Room House"),
        Song(title="Spaceman", artist="Hardwell", genre="Progressive House"),
        Song(title="Tsunami", artist="DVBBS & Borgeous", genre="Big Room House"),
        Song(title="Clarity", artist="Zedd", genre="Electro House"),
        Song(title="Bangarang", artist="Skrillex", genre="Dubstep"),
        Song(title="Levels", artist="Avicii", genre="Progressive House"),
        Song(title="Titanium", artist="David Guetta", genre="Electro House"),
        Song(title="Satisfaction", artist="Benny Benassi", genre="Electro House"),
        Song(title="One More Time", artist="Daft Punk", genre="French House")
    ]
