from ovos_utils.waiting_for_mycroft.common_play import CPSMatchType, CPSMatchLevel
from ovos_utils.skills.templates.media_collection import MediaCollectionSkill
from mycroft.skills.core import intent_file_handler
from mycroft.util.parse import fuzzy_match, match_one
from pyvod import Collection, Media
from os.path import join, dirname
import random
import re
from json_database import JsonStorageXDG
import datetime


class CultCinemaClassicsSkill(MediaCollectionSkill):

    def __init__(self):
        super().__init__("CultCinemaClassics")
        self.supported_media = [CPSMatchType.GENERIC,
                                CPSMatchType.MOVIE,
                                CPSMatchType.VIDEO]
        path = join(dirname(__file__), "res", "CultCinemaClassics.jsondb")
        logo = join(dirname(__file__), "res", "ccc_logo.png")
        # load video catalog
        self.media_collection = Collection("CultCinemaClassics",
                                           logo=logo,
                                           db_path=path)

    # voice interaction
    def get_intro_message(self):
        self.speak_dialog("intro")

    @intent_file_handler('home.intent')
    def handle_homescreen_utterance(self, message):
        self.handle_homescreen(message)

    # matching
    def match_media_type(self, phrase, media_type):
        match = None
        score = 0

        if self.voc_match(phrase,
                          "video") or media_type == CPSMatchType.VIDEO:
            score += 0.05
            match = CPSMatchLevel.GENERIC

        if self.voc_match(phrase, "classic"):
            score += 0.1
            match = CPSMatchLevel.CATEGORY

        if self.voc_match(phrase,
                          "movie") or media_type == CPSMatchType.MOVIE:
            score += 0.1
            match = CPSMatchLevel.CATEGORY

        if self.voc_match(phrase, "ccc"):
            score += 0.3
            match = CPSMatchLevel.TITLE

        return match, score

    def normalize_title(self, title):
        title = title.lower().strip()
        title = self.remove_voc(title, "ccc")
        title = self.remove_voc(title, "movie")
        title = self.remove_voc(title, "video")
        title = self.remove_voc(title, "classic")
        title = title.replace("|", "").replace('"', "") \
            .replace(':', "").replace('”', "").replace('“', "") \
            .strip()
        return " ".join([w for w in title.split(" ") if w])  # remove extra
        # spaces

    def calc_final_score(self, phrase, base_score, match_level):
        # calc final confidence
        score = base_score
        if self.voc_match(phrase, "ccc"):
            score += 0.15
        if self.voc_match(phrase, "movie"):
            score += 0.05  # bonus for films
        if self.voc_match(phrase, "classic"):
            score += 0.05  # bonus for classic films
        return score


def create_skill():
    return CultCinemaClassicsSkill()
