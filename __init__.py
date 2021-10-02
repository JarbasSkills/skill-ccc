from os.path import join, dirname

from mycroft.skills.core import intent_file_handler
from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_workshop.skills.video_collection import VideoCollectionSkill
from pyvod import Collection


class CultCinemaClassicsSkill(VideoCollectionSkill):

    def __init__(self):
        super().__init__("CultCinemaClassics")
        self.supported_media = [MediaType.MOVIE,
                                MediaType.TRAILER]
        path = join(dirname(__file__), "res", "CultCinemaClassics.jsondb")
        logo = join(dirname(__file__), "res", "ccc_logo.png")
        # load video catalog
        self.media_collection = Collection("CultCinemaClassics",
                                           logo=logo,
                                           db_path=path)
        self.default_image = join(dirname(__file__), "ui", "ccc_logo.png")
        self.skill_logo = join(dirname(__file__), "ui", "ccc_icon.jpg")
        self.skill_icon = join(dirname(__file__), "ui", "ccc_icon.jpg")
        self.default_bg = join(dirname(__file__), "ui", "ccc_logo.png")
        self.playback_type = PlaybackType.VIDEO
        self.media_type = MediaType.MOVIE

    # voice interaction
    def get_intro_message(self):
        self.speak_dialog("intro")

    @intent_file_handler('home.intent')
    def handle_homescreen_utterance(self, message):
        self.handle_homescreen(message)

    # matching
    def match_media_type(self, phrase, media_type):
        score = 0
        if self.voc_match(phrase, "video") or media_type == MediaType.VIDEO:
            score += 5
        if self.voc_match(phrase, "classic"):
            score += 10
        if self.voc_match(phrase, "movie") or media_type == MediaType.MOVIE:
            score += 10
        if self.voc_match(phrase, "ccc"):
            score += 50
        return score

    def normalize_title(self, title):
        title = title.lower().strip()
        title = self.remove_voc(title, "ccc")
        title = self.remove_voc(title, "movie")
        title = self.remove_voc(title, "video")
        title = self.remove_voc(title, "classic")
        title = self.remove_voc(title, "horror")
        title = title.replace("|", "").replace('"', "") \
            .replace(':', "").replace('”', "").replace('“', "") \
            .strip()
        return " ".join(
            [w for w in title.split(" ") if w])  # remove extra spaces


def create_skill():
    return CultCinemaClassicsSkill()
