#!/usr/bin/env python3
# coding=utf-8
"""bluarchive - Bluprint Downloader"""

import configparser
import logging
from os import environ, makedirs, path
from posixpath import basename as url_filename
from subprocess import DEVNULL, PIPE, Popen
from urllib.parse import unquote_plus, urlsplit

import requests

API_BASE = "https://api.mybluprint.com"


class BluArchive:
    _config: configparser.ConfigParser
    _log: logging.Logger
    _s: requests.Session

    _user_id: int
    _download_patterns: bool
    _download_materials: bool
    _download_videos: bool
    output_dir: str

    def __init__(self):
        self._log = logging.getLogger("bluarchive")

        self.s = requests.Session()
        self.s.headers = {"User-Agent": "Bluprint Archiver"}
        self.read_config()

    def read_config(self, filename: str = "bluarchive.ini"):
        if not path.isfile(filename):
            with open(filename, "w") as f:
                f.write(
                    "\r\n".join(
                        [
                            "[bluprint]",
                            "; Mandatory - Get from cookies",
                            "craftsy_tok = aAaAbBbBcCcC",
                            "craftsy_userId = 123456\r\n",
                            "; Optional",
                            ";download_patterns = yes",
                            ";download_materials = yes",
                            ";download_videos = yes",
                            ";output_dir = bluprint_{user_id}\r\n",
                        ]
                    )
                )
            self._log.critical(
                f"A template {filename} has been written. "
                "Put your cookies in, and run me again."
            )
            raise Exception("Unconfigured")

        self._config = configparser.ConfigParser()
        self._config.read(filename)

        if "bluprint" not in self._config:
            self._log.critical(
                "Invalid config. Checked {filename}."
                "If you need a fresh start, delete the file and run this program again."
            )
            raise Exception("Unconfigured")
        if self._config["bluprint"].get("craftsy_tok").startswith("aAaAbB"):
            raise Exception(
                "Unconfigured", "Did you set your cookies in the config file?"
            )

        for cookie_name in ["craftsy_tok", "craftsy_userId"]:
            if cookie_name not in self._config["bluprint"]:
                raise Exception("Required config entry missing:", cookie_name)
            self.s.cookies.set_cookie(
                requests.cookies.create_cookie(
                    name=cookie_name,
                    value=self._config["bluprint"][cookie_name],
                    domain=".mybluprint.com",
                )
            )
        self._user_id = self._config["bluprint"]["craftsy_userId"]

        self._download_patterns = self._config["bluprint"].get(
            "download_patterns", "yes"
        ).lower() not in ["no", "false"]
        self._download_materials = self._config["bluprint"].get(
            "download_materials", "yes"
        ).lower() not in ["no", "false"]
        self._download_videos = self._config["bluprint"].get(
            "download_videos", "yes"
        ).lower() not in ["no", "false"]

        self.output_dir = (
            self._config["bluprint"]
            .get("output_dir", "bluprint_{user_id}")
            .format(user_id=self._user_id)
        )

    def download_patterns(self):
        r = self.s.get(
            API_BASE
            + f"/users/{self._user_id}/patterns?pageSize=99999&sortBy=RESOURCE_NAME"
        )
        patterns = r.json()
        if patterns["totalPages"] > 1:
            raise Exception(
                "TooManyPatterns",
                (
                    "You have more patterns than the API will return on one page. "
                    "This script cannot currently download them all."
                ),
            )
        patterns_dir = path.join(self.output_dir, "Patterns")
        makedirs(patterns_dir, exist_ok=True)
        with open(path.join(patterns_dir, "patterns.json"), "wb") as f:
            f.write(r.content)
        for pattern in patterns["hits"]:
            card = pattern["libraryBaseballCard"]
            pattern_id = card["id"]
            pattern_name = card.get("name", f"Unnamed Pattern {pattern_id}")
            self._log.info("Processing pattern %s: %s", pattern_id, pattern_name)
            r = self.s.get(
                API_BASE
                + f"/users/{self._user_id}/patterns/{pattern_id}/patternDownloadLinks",
            )
            if r.status_code != 200:
                raise Exception(
                    "ProbablyNotAuthenticated",
                    "Error retrieving pattern download links. Are you signed in?",
                    r.text,
                )
            urls = r.json()

            # Make unnamed stuff easier to find
            if len(urls) == 1 and "name" not in card:
                first_name = unquote_plus(url_filename(urlsplit(urls[0]).path))
                pattern_name += " " + first_name.rsplit(".", 1)[0].split("_aiid", 1)[0]

            # Path cleaning probably insufficient on Windows (bans /\*:?"<>| )
            cleanish_name = (
                pattern_name.replace("/", "").replace("  ", " ").replace('"', "")
            )
            pattern_out_dir = path.join(patterns_dir, cleanish_name)
            makedirs(pattern_out_dir, exist_ok=True)

            for url in urls:
                filename = unquote_plus(url_filename(urlsplit(url).path))
                self._log.debug("Downloading pattern %r", filename)
                r = self.s.get(url)
                with open(path.join(pattern_out_dir, filename), "wb") as f:
                    f.write(r.content)
            if environ.get("BLU_TEST") in ["1", "2"]:
                break

    # Enrollments aka classes aka playlists
    def download_classes(self):
        r = self.s.get(API_BASE + f"/enrollments?userId={self._user_id}")
        enrollments = r.json()

        for enrollment in enrollments:
            playlist_id = enrollment["playlistId"]
            if enrollment["archived"]:
                self._log.info("Skipping archived playlist %s", playlist_id)
                continue

            r = self.s.get(API_BASE + f"/m/playlists/{playlist_id}")
            course = r.json()
            course_name = course["name"]

            self._log.info("Processing class %s: %s", playlist_id, course_name)

            # Probably needs name cleaning on Windows
            course_out_dir = path.join(
                self.output_dir, f"{course_name} ({playlist_id})"
            )
            makedirs(course_out_dir, exist_ok=True)

            with open(path.join(course_out_dir, "playlist.json"), "wb") as f:
                f.write(r.content)

            # Resources aka materials
            if self._download_materials:
                r = self.s.get(API_BASE + f"/b/playlists/{playlist_id}/materials")
                materials = r.json()
                if len(materials) < 1:
                    self._log.debug("No materials for %s: %s", playlist_id, course_name)
                else:
                    material_out_dir = path.join(course_out_dir, "materials")
                    makedirs(material_out_dir, exist_ok=True)
                for material in materials:
                    if not material["downloadable"]:
                        self._log.debug(
                            "Skipping non-downloadable material %r",
                            material["materialName"],
                        )
                        continue
                    filename = unquote_plus(
                        url_filename(urlsplit(material["materialPath"]).path)
                    )
                    self._log.debug(
                        "Downloading material %r to %r",
                        material["materialName"],
                        filename,
                    )
                    r = self.s.get(material["materialPath"])
                    with open(path.join(material_out_dir, filename), "wb") as f:
                        f.write(r.content)

            # Video
            if self._download_videos:
                for episode_idx, episode in enumerate(course["episodes"]):
                    self.download_episode(course_out_dir, episode_idx, episode)

                    if environ.get("BLU_TEST") == "1":
                        break
            if environ.get("BLU_TEST") in ["1", "2"]:
                break

    def download_episode(self, out_dir: str, episode_number: int, episode_data: dict):
        episode_id = episode_data["episodeId"]
        r = self.s.get(API_BASE + f"/m/videos/secure/episodes/{episode_id}")
        if r.status_code != 200:
            raise Exception(
                "ProbablyNotAuthenticated",
                "Error retrieving episode download links. Are you signed in?",
                r.text,
            )
        episode_sources = r.json()
        for source in episode_sources:
            if source["format"] == "mp4":
                episode_source = source
                break
        else:
            episode_source = episode_sources[0]

        base_filename = "{}. {}".format(episode_number + 1, episode_data["name"])

        vtt_filename = None
        if episode_source.get("vttUrl") is not None:
            vtt_filename = base_filename + ".vtt"
            r = self.s.get(episode_source["vttUrl"])
            with open(path.join(out_dir, vtt_filename), "wb") as f:
                f.write(r.content)

        # ffmpeg command
        ffcmd = ["ffmpeg", "-hide_banner"]
        ffcmd += ["-i", "-"]  # 0: chapters
        ffcmd += ["-i", episode_source["url"]]  # 1: v, a
        if vtt_filename is not None:
            ffcmd += ["-i", vtt_filename]  # 2: s
        ffcmd += ["-map", "1"]  # mp4, all streams (v, a)
        if vtt_filename is not None:
            ffcmd += ["-map", "2"]  # webvtt (s)
        ffcmd += ["-map_metadata", "0"]  # chapters last
        ffcmd += ["-c", "copy"]  # a/v
        # ffcmd += ["-strict", "-2"]  # Nope, really can't cram WebVTT or ASS into mp4 I guess =(
        ffcmd += ["-c:s", "mov_text"]
        ffcmd += ["-movflags", "+faststart"]
        ffcmd += ["-y", base_filename + ".mp4"]

        # Generate chapter data
        metadata = ";FFMETADATA1\ntitle={}\n\n".format(episode_data["name"]).encode(
            "utf-8"
        )
        for chapter in episode_data["chapters"]:
            metadata += "[CHAPTER]\nTIMEBASE=1/1000\nSTART={}\nEND={}\ntitle={}\n\n".format(
                chapter["videoStartMs"], chapter["videoEndMs"], chapter["name"]
            ).encode(
                "utf-8"
            )
        proc = Popen(ffcmd, cwd=out_dir, stdin=PIPE, stderr=DEVNULL)
        proc.communicate(metadata)
        if proc.wait() != 0:
            raise Exception("ffmpeg failed!", episode_id, ffcmd)

    def archive(self):
        self._log.info("Saving to %r", self.output_dir)
        if self._download_patterns:
            self.download_patterns()
        if self._download_videos or self._download_materials:
            self.download_classes()


def main():
    logging.basicConfig(level=logging.INFO)

    ba = BluArchive()
    ba.archive()


if __name__ == "__main__":
    main()
