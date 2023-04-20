from collections import defaultdict
from enum import Enum

import langcodes
from aiopyarr.sonarr_client import SonarrEpisode, SonarrEpisodeFile, SonarrClient, SonarrSeries


class LangStatus(Enum):
    none = 0  # no episodes have desired languages
    all = 1  # all episodes have desired languages
    some = 2  # some episodes have desired languages


def _check_lang_status(lang_status_list: list[LangStatus]) -> LangStatus:
    """
    Checks a list of LangStatuses to return a LangStatus of its own.
    :param lang_status_list: List of LangStatuses
    :return: LangStatus depending on if the whole list has all, some, or no desired languages.
    """
    if not lang_status_list:
        return LangStatus.none

    if LangStatus.some in lang_status_list or (
            LangStatus.all in lang_status_list and
            LangStatus.none in lang_status_list):
        return LangStatus.some
    elif LangStatus.all not in lang_status_list:
        return LangStatus.none
    else:
        return LangStatus.all


class Episode:
    """Holds info about a single episode."""

    def __init__(self, ep_file: SonarrEpisodeFile, ep_info: SonarrEpisode):
        self.ep_file = ep_file
        self.ep_info = ep_info
        self.languages = self._get_languages()

    def _get_languages(self):
        result = []
        for lang in self.ep_file.mediaInfo.audioLanguages.split(' / '):
            # Some languages in Sonarr are either not there, or are like this: / Japanese.
            if lang == '':
                result.append(None)
            else:
                try:
                    result.append(langcodes.find(lang))
                except LookupError:
                    # Handle unknown languages
                    result.append(None)
        return result

    def get_lang_status(self, wanted_langs: list[langcodes.Language]):
        """Returns language status for a given episode."""
        status_list = []
        for lang in wanted_langs:
            if not lang in self.languages:
                status_list.append(LangStatus.none)
            else:
                status_list.append(LangStatus.all)

        return _check_lang_status(status_list)


class Season:
    """Holds info about an entire season."""

    def __init__(self, season_num: int, episodes: list[Episode] = None):
        if episodes is None:
            episodes = []
        self.episodes = episodes
        self.season_num = season_num

    def add_episode(self, episode: Episode):
        """Adds an episode to the season."""
        self.episodes.append(episode)

    def get_lang_status(self, wanted_langs: list[langcodes.Language]):
        """Returns language status for a given season."""
        status_list = []
        for episode in self.episodes:
            status_list.append(episode.get_lang_status(wanted_langs))

        return _check_lang_status(status_list)


class Series:
    """Holds info about an entire series."""

    def __init__(self, episodes: list[Episode], series_info: SonarrSeries):
        self.episodes = episodes
        self.series_info = series_info
        self.seasons = split_into_seasons(episodes)

    def get_season(self, season_num):
        return self.seasons[season_num]

    def get_lang_status(self, wanted_langs: list[langcodes.Language]):
        """Returns language status for a given series."""
        status_list = []
        for _, season in self.seasons.items():
            status_list.append(season.get_lang_status(wanted_langs))

        return _check_lang_status(status_list)


def split_into_seasons(all_episodes: list) -> dict[int, Season]:
    """
    Takes a list of all episodes in a series, and splits them into seasons based on their season number.
    The result is a dict that can be accessed as such: result[*season number*]
    :param all_episodes: List of all episodes in a series
    :return:
    """
    result = {}
    seasons = defaultdict(list)

    for episode in all_episodes:
        seasons[episode.ep_info.seasonNumber].append(episode)
    for season_num, season_episodes in seasons.items():
        result[season_num] = Season(season_num, season_episodes)

    return result


def get_episodes(ep_infos: list[SonarrEpisode], ep_files: list[SonarrEpisodeFile]) -> list[Episode]:
    """
    Finds episode files for an episode by file id, then places them into an Episode class together.
    Returns a list of Episode instances.
    """
    episode_files_by_id = {x.id: x for x in ep_files}
    episodes = []
    for ep in ep_infos:
        if not ep.hasFile:
            continue
        episodes.append(Episode(episode_files_by_id[ep.episodeFileId], ep))
    return episodes


async def get_series(client: SonarrClient, series: SonarrSeries) -> Series:
    """Obtains all episodes for a series, and returns a Series."""
    ep_infos = await client.async_get_episodes(series.id, series=True)
    ep_files = await client.async_get_episode_files(series.id, series=True)
    episodes = get_episodes(ep_infos, ep_files)
    return Series(episodes, series_info=series)
