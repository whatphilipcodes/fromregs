import os
import re

from beets import IncludeLazyConfig, plugins
from beets.util import displayable_path

from typing import Any, Dict


# config setup
JSONDict = Dict[str, Any]
DEFAULT_CONFIG: JSONDict = {
    "custom_matchlist": [
        r"^(?P<artist>.+)[\-_](?P<title>.+)[\-_](?P<tag>.*)$",
        r"^(?P<track>\d+)[\s.\-_]+(?P<artist>.+)[\-_](?P<title>.+)[\-_](?P<tag>.*)$",
        r"^(?P<artist>.+)[\-_](?P<title>.+)$",
        r"^(?P<track>\d+)[\s.\-_]+(?P<artist>.+)[\-_](?P<title>.+)$",
        r"^(?P<track>\d+)[\s.\-_]+(?P<title>.+)$",
        r"^(?P<track>\d+)\s+(?P<title>.+)$",
        r"^(?P<title>.+) by (?P<artist>.+)$",
        r"^(?P<track>\d+).*$",
        r"^(?P<title>.+)$",
    ],
    "bad_title_matchlist": [r"^$"],
    "artist_post_sub": [r"\s{2,}"],
    "title_post_sub": [r"\[.*?\]", r"\s{2,}"],
    "final_strip": True,
    "fill_album_from_title": False,
    "limit_tracknumber": 25,
}


def equal(seq):
    """Determine whether a sequence holds identical elements."""
    return len(set(seq)) <= 1


def equal_fields(matchdict, field):
    """Do all items in `matchdict`, whose values are dictionaries, have
    the same value for `field`? (If they do, the field is probably not
    the title.)
    """
    return equal(m[field] for m in matchdict.values())


def all_matches(names, pattern):
    """If all the filenames in the item/filename mapping match the
    pattern, return a dictionary mapping the items to dictionaries
    giving the value for each named subpattern in the match. Otherwise,
    return None.
    """
    matches = {}
    for item, name in names.items():
        match = re.match(pattern, name, re.IGNORECASE)
        if match and match.groupdict():
            # only yield a match when the regex applies *and* has
            # capture groups. Otherwise, no information can be extracted
            # from the filename.
            matches[item] = match.groupdict()
        else:
            return None
    return matches


def get_filename(item):
    """Returns the name of a file referenced by a beets item without file extension"""
    path = displayable_path(item.path)
    name, _ = os.path.splitext(os.path.basename(path))
    return name


# plugin structure and hook into import process.


class FromRegs(plugins.BeetsPlugin):
    beets_config: IncludeLazyConfig

    def __init__(self):
        super().__init__()
        self.config.add(DEFAULT_CONFIG.copy())
        self.register_listener("import_task_start", self.filename_task)

        # config checks
        if not self.config["custom_matchlist"].as_str_seq():
            self._log.warning(
                "The provided custom_matchlist was empty. Please provide a valid list or remove the key from your config to use the default list."
            )
        if not self.config["bad_title_matchlist"].as_str_seq():
            self._log.warning(
                "The provided bad_title_matchlist was empty. Please provide a valid list or remove the key from your config to use the default list."
            )

    def bad_title(self, title):
        """Determine whether a given title is "bad" (empty or otherwise
        meaningless) and in need of replacement.
        """
        for pattern in self.config["bad_title_matchlist"].as_str_seq():
            if re.match(pattern, title, re.IGNORECASE):
                return True
        return False

    def apply_matches(self, match_dict):
        """Given a mapping from items to field dicts, apply the fields to
        the objects.
        """
        some_map = list(match_dict.values())[0]
        keys = some_map.keys()

        # only proceed if the "tag" field is equal across all filenames.
        if "tag" in keys and not equal_fields(match_dict, "tag"):
            return

        # given both an "artist" and "title" field, assume that one is
        # *actually* the artist, which must be uniform, and use the other
        # for the title. This, of course, won't work for VA albums.
        if "artist" in keys:
            if equal_fields(match_dict, "artist"):
                artist = some_map["artist"]
                title_field = "title"
            elif equal_fields(match_dict, "title"):
                artist = some_map["title"]
                title_field = "artist"
            else:
                # both vary. Abort.
                return

            for item in match_dict:
                if not item.artist:
                    if self.config["artist_post_sub"]:
                        for pattern in self.config["artist_post_sub"].as_str_seq():
                            artist = re.sub(pattern, "", artist)
                    if self.config["final_strip"]:
                        item.artist = artist.strip()
                    else:
                        item.artist = artist
                    self._log.info("Artist replaced with: '{}'".format(item.artist))

        # no artist field: remaining field is the title.
        else:
            title_field = "title"

        # apply the title and track.
        for item in match_dict:
            if self.bad_title(item.title):
                if "title" in match_dict[item]:
                    title = str(match_dict[item][title_field])
                else:
                    title = str(get_filename(item))

                if self.config["title_post_sub"]:
                    for pattern in self.config["title_post_sub"].as_str_seq():
                        title = re.sub(pattern, "", title)
                if self.config["final_strip"]:
                    item.title = title.strip()
                else:
                    item.title = title
                self._log.info("Title replaced with: '{}'".format(item.title))

            if "track" in match_dict[item] and item.track == 0:
                track = int(match_dict[item]["track"].strip())
                if track <= self.config["limit_tracknumber"].as_number():
                    if str(track) == item.artist:
                        self._log.debug(
                            "Track {} is similar to artist and was skipped.", track
                        )
                    else:
                        item.track = track
                        self._log.info("Track replaced with: '{}'".format(item.track))
                else:
                    self._log.debug(
                        "Track exceeds configured limit of: {}",
                        str(self.config["limit_tracknumber"].as_number()),
                    )

    def filename_task(self, task):
        """Examine each item in the task to see if we can extract a title
        from the filename. Try to match all filenames to a number of
        regexps, starting with the most complex patterns and successively
        trying less complex patterns. As soon as all filenames match the
        same regex we can make an educated guess of which part of the
        regex that contains the title.
        """
        # get a list of items to work on
        items = task.items if task.is_album else [task.item]

        # look for suspicious (empty or meaningless) titles.
        missing_titles = sum(self.bad_title(i.title) for i in items)

        if missing_titles:
            # get the base filenames (no path or extension).
            names = {}
            for item in items:
                names[item] = get_filename(item)

            # look for useful information in the filenames.

            for pattern in self.config["custom_matchlist"].as_str_seq():
                self._log.debug("Checking: " + pattern)
                match_dict = all_matches(names, pattern)
                if match_dict:
                    self._log.debug("Match: {}", match_dict.values())
                    self.apply_matches(match_dict)
                else:
                    self._log.debug("No match found.")

        for item in items:
            if self.config["fill_album_from_title"] and item.album == "":
                self._log.debug("Album could not be inferred. Using title instead...")
                item.album = item.title
