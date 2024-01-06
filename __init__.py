import random
from os.path import join, dirname

import requests
from json_database import JsonStorageXDG

from ovos_utils.ocp import MediaType, PlaybackType
from ovos_workshop.decorators.ocp import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


class CultCinemaClassicsSkill(OVOSCommonPlaybackSkill):
    def __init__(self, *args, **kwargs):
        self.supported_media = [MediaType.MOVIE,
                                MediaType.GENERIC]
        self.skill_icon = join(dirname(__file__), "ui", "ccc_icon.jpg")
        self.default_bg = join(dirname(__file__), "ui", "ccc_logo.png")
        self.archive = JsonStorageXDG("CultCinemaClassics", subfolder="OCP")
        self.media_type_exceptions = {
            # url 2 MediaType , if not present its a short film
        }
        super().__init__(*args, **kwargs)

    def initialize(self):
        self._sync_db()
        self.load_ocp_keywords()

    def load_ocp_keywords(self):
        titles = []
        series = []
        docus = []
        genre = ["classic film", "cult film", "classic film", "old movie"]

        for url, data in self.archive.items():
            t = data["title"]
            if "Documentary" in t:
                if "(" in t:
                    title, t = t.split("(")
                    docus.append(title)
                elif "|" in t:
                    title, t = t.split("|", 1)
                    docus.append(title)
                else:
                    docus.append(t)
                # signal this entry as DOCUMENTARY media type
                # in case it gets selected later
                self.media_type_exceptions[data["url"]] = MediaType.DOCUMENTARY
                continue
            elif "Series" in t:
                title, t = t.split("(")
                series.append(title)
                # signal this entry as VIDEO_EPISODES media type
                # in case it gets selected later
                self.media_type_exceptions[data["url"]] = MediaType.VIDEO_EPISODES
                continue

            def _parse(t):
                if "|" in t:
                    d = t.split("|")
                    t = d[0]  # could also parse d[1] for genre / actor
                if "(" in t:
                    title, y = t.split("(", 1)
                    title = title.strip()
                    # could parse y for date / actor
                    #y, a = y.split(")", 1)
                    #if "," in y:
                    #    # can parse actor / genre from remainder
                    #    y = y.split(",", 1)
                    #    if y[0].strip().isdigit():
                    #        y = y[0].strip()
                    #    elif y[1].strip().isdigit():
                    #        y = y[1].strip()
                else:
                    title = t
                return title.strip()

            title = _parse(t)
            if "/" in t:
                t, t2 = t.split("/")
                title = _parse(t)
                titles.append(title)
                title = _parse(t2)
                titles.append(title)
            if ":" in t:
                t, t2 = t.split(":")
                title = _parse(t)
                titles.append(title)
                title = _parse(t2)
                titles.append(title)

            titles.append(title)

        self.register_ocp_keyword(MediaType.MOVIE,
                                  "movie_name", titles)
        self.register_ocp_keyword(MediaType.MOVIE,
                                  "film_genre", genre)
        self.register_ocp_keyword(MediaType.DOCUMENTARY,
                                  "documentary_name", docus)
        self.register_ocp_keyword(MediaType.VIDEO_EPISODES,
                                  "series_name", series)
        self.register_ocp_keyword(MediaType.MOVIE,
                                  "movie_streaming_provider",
                                  ["Cult Cinema Classics", "CultCinemaClassics", "CCC"])

    def _sync_db(self):
        bootstrap = "https://github.com/JarbasSkills/skill-ccc/raw/dev/bootstrap.json"
        data = requests.get(bootstrap).json()
        self.archive.merge(data)
        self.schedule_event(self._sync_db, random.randint(3600, 24 * 3600))

    def get_playlist(self, score=50, num_entries=50):
        pl = self.featured_media()[:num_entries]
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
        base_score = 25 if media_type == MediaType.SHORT_FILM else 0
        entities = self.ocp_voc_match(phrase)
        base_score += 50 * len(entities)

        title = entities.get("movie_name")
        skill = "movie_streaming_provider" in entities  # skill matched

        if skill:
            yield self.get_playlist()

        # handle media_type per db entry
        if media_type == MediaType.VIDEO_EPISODES:
            candidates = [video for video in self.archive.values()
                          if self.media_type_exceptions.get(video["url"], MediaType.MOVIE) ==
                          MediaType.VIDEO_EPISODES]
        elif media_type == MediaType.DOCUMENTARY:
            candidates = [video for video in self.archive.values()
                          if self.media_type_exceptions.get(video["url"], MediaType.MOVIE) ==
                          MediaType.DOCUMENTARY]
        elif media_type == MediaType.BEHIND_THE_SCENES:
            candidates = [video for video in self.archive.values()
                          if self.media_type_exceptions.get(video["url"], MediaType.MOVIE) ==
                          MediaType.BEHIND_THE_SCENES]
        else:
            candidates = [video for video in self.archive.values()
                          if video["url"] not in self.media_type_exceptions]

        if title:
            # only search db if user explicitly requested a known movie
            if title:
                candidates = [video for video in candidates
                              if title.lower() in video["title"].lower()]

                for video in candidates:
                    yield {
                        "title": video["title"],
                        "artist": video["author"],
                        "match_confidence": min(100, base_score),
                        "media_type": self.media_type_exceptions.get(video["url"], MediaType.MOVIE),
                        "uri": "youtube//" + video["url"],
                        "playback": PlaybackType.VIDEO,
                        "skill_icon": self.skill_icon,
                        "skill_id": self.skill_id,
                        "image": video["thumbnail"],
                        "bg_image": video["thumbnail"],
                    }

    @ocp_featured_media()
    def featured_media(self):
        return [{
            "title": video["title"],
            "image": video["thumbnail"],
            "match_confidence": 70,
            "media_type": MediaType.MOVIE,
            "uri": "youtube//" + video["url"],
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "bg_image": video["thumbnail"],
            "skill_id": self.skill_id
        } for video in self.archive.values()]


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus

    s = CultCinemaClassicsSkill(bus=FakeBus(), skill_id="t.fake")
    for r in s.search_db("The Thing from Venus", MediaType.MOVIE):
        print(r)
        # {'title': 'Zontar: The Thing from Venus (1967) Horror, Sci-Fi, Psychotronic Full Film', 'artist': 'Cult Cinema Classics', 'match_confidence': 50, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=MWy5lUbxJ14', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/MWy5lUbxJ14/sddefault.jpg?v=5f2d7d75', 'bg_image': 'https://i.ytimg.com/vi/MWy5lUbxJ14/sddefault.jpg?v=5f2d7d75'}
