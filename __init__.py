import random
from os.path import join, dirname

from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_utils.parse import fuzzy_match
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search, ocp_featured_media
from youtube_archivist import YoutubeArchivist


class CultCinemaClassicsSkill(OVOSCommonPlaybackSkill):
    def __init__(self):
        super().__init__("CultCinemaClassics")
        self.supported_media = [MediaType.MOVIE,
                                MediaType.GENERIC]
        self.skill_icon = join(dirname(__file__), "ui", "ccc_icon.jpg")
        self.default_bg = join(dirname(__file__), "ui", "ccc_logo.png")
        self.archive = YoutubeArchivist(db_name="CultCinemaClassics",
                                        blacklisted_kwords=["trailer", "teaser", "movie scene",
                                                            "movie clip", "behind the scenes",
                                                            "Cult Clips", "Movie Preview",
                                                            "Fight Scene", "CCC Clip"])

    def initialize(self):
        if len(self.archive.db):
            # update db sometime in the next 12 hours, randomized to avoid a huge network load every boot
            # (every skill updating at same time)
            self.schedule_event(self._scheduled_update, random.randint(3600, 12 * 3600))
        else:
            # no database, sync right away
            self.schedule_event(self._scheduled_update, 5)

    def _scheduled_update(self):
        self.update_db()
        self.schedule_event(self._scheduled_update, random.randint(3600, 12 * 3600))  # every 6 hours

    def update_db(self):
        url = "https://www.youtube.com/channel/UCycDFnpMeWzaITQSD1dWsOA"
        self.archive.archive_channel(url)
        self.archive.remove_below_duration(30)  # 30 minutes minimum duration
        self.archive.remove_unavailable()  # check if video is still available

    # matching
    def match_skill(self, phrase, media_type):
        score = 0
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

    def calc_score(self, phrase, match, base_score=0):
        score = base_score
        score += 100 * fuzzy_match(phrase.lower(), match["title"].lower())
        return min(100, score)

    def get_playlist(self, score=50, num_entries=250):
        pl = [{
            "title": video["title"],
            "image": video["thumbnail"],
            "match_confidence": 70,
            "media_type": MediaType.MOVIE,
            "uri": "youtube//" + video["url"],
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "bg_image": video["thumbnail"],
            "skill_id": self.skill_id
        } for video in self.archive.sorted_entries()][:num_entries]
        return {
            "match_confidence": score,
            "media_type": MediaType.MOVIE,
            "playlist": pl,
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "image": self.skill_icon,
            "bg_image": self.default_bg,
            "title": "Cult Cinema Classics (Movie Playlist)",
            "author": "Cult Cinema Classics"
        }

    @ocp_search()
    def search_db(self, phrase, media_type):
        base_score = self.match_skill(phrase, media_type)
        if self.voc_match(phrase, "ccc"):
            yield self.get_playlist(base_score)
        if media_type == MediaType.MOVIE:
            # only search db if user explicitly requested movies
            phrase = self.normalize_title(phrase)
            for url, video in self.archive.db.items():
                yield {
                    "title": video["title"],
                    "author": "Cult Cinema Classics",
                    "match_confidence": self.calc_score(phrase, video, base_score),
                    "media_type": MediaType.MOVIE,
                    "uri": "youtube//" + url,
                    "playback": PlaybackType.VIDEO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": video["thumbnail"],
                    "bg_image": self.default_bg
                }

    @ocp_featured_media()
    def featured_media(self):
        return self.get_playlist()['playlist']


def create_skill():
    return CultCinemaClassicsSkill()
