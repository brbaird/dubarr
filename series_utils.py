from collections import defaultdict
from enum import Enum

from aiopyarr.sonarr_client import SonarrEpisode, SonarrEpisodeFile, SonarrClient, SonarrSeries


class DubStatus(Enum):
    not_dubbed = 0  # no episodes are dubbed
    dubbed = 1  # all episodes are dubbed
    partially_dubbed = 2  # some episodes are dubbed


def _check_dub_status(dub_status_list: list[DubStatus]) -> DubStatus:
    """
    Checks a list of DubStatuses to return a DubStatus of its own.
    :param dub_status_list:
    :return: DubStatus depending on if the whole list is fully dubbed, partially dubbed, or not dubbed.
    """
    if not dub_status_list:
        return DubStatus.not_dubbed

    if DubStatus.partially_dubbed in dub_status_list or (
            DubStatus.dubbed in dub_status_list and
            DubStatus.not_dubbed in dub_status_list):
        return DubStatus.partially_dubbed
    elif DubStatus.dubbed not in dub_status_list:
        return DubStatus.not_dubbed
    else:
        return DubStatus.dubbed


class Episode:
    """Holds info about a single episode."""

    def __init__(self, ep_file: SonarrEpisodeFile, ep_info: SonarrEpisode):
        self.ep_file = ep_file
        self.ep_info = ep_info

    @property
    def dub_status(self) -> DubStatus:
        """Returns dub status for a given episode."""
        try:
            languages = self.ep_file.mediaInfo.audioLanguages.split(' / ')
        except AttributeError:
            return DubStatus.not_dubbed
        return DubStatus.dubbed if 'English' in languages else DubStatus.not_dubbed


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

    @property
    def dub_status(self) -> DubStatus:
        """Returns dub status for a given season."""
        dub_status_list = []
        for episode in self.episodes:
            dub_status_list.append(episode.dub_status)

        return _check_dub_status(dub_status_list)


class Series:
    """Holds info about an entire series."""

    def __init__(self, episodes: list[Episode], series_info: SonarrSeries):
        self.episodes = episodes
        self.series_info = series_info
        self.seasons = split_into_seasons(episodes)

    def get_season(self, season_num):
        return self.seasons[season_num]

    @property
    def dub_status(self) -> DubStatus:
        dub_status_list = []
        for _, season in self.seasons.items():
            dub_status_list.append(season.dub_status)

        return _check_dub_status(dub_status_list)


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
