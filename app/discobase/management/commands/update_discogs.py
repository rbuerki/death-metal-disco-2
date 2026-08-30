"""Management command to fetch discogs data (image, discogs_id / URL, songtitles).

Run with ``uv run python app/manage.py update_discogs``. See README.md for usage.
"""

from io import BytesIO
from typing import Any

import discogs_client
import discogs_client.models
import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import IntegrityError
from django.db.models import Q
from PIL import Image, UnidentifiedImageError

from discobase.models import Record, Song


class Command(BaseCommand):
    """Fetch discogs data (cover image, discogs_id, song titles) for a record."""

    help = "Fetch discogs data (image, discogs_id, songtitles) for a record."

    def add_arguments(self, parser: CommandParser) -> None:
        """Declare the command-line arguments."""
        parser.add_argument(
            "record_id",
            nargs="?",
            type=int,
            help="Record to update. Omit to take the first record missing a discogs_id.",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List records without a valid discogs_id, then exit.",
        )
        parser.add_argument(
            "--upload-dir",
            default="covers",
            help="Sub-directory of MEDIA_ROOT to store the cover image in.",
        )
        parser.add_argument(
            "--no-resize",
            action="store_true",
            help="Store the original cover image without resizing.",
        )

    def handle(self, *args: Any, **opts: Any) -> None:
        """Dispatch to list mode or the update pipeline."""
        if opts["list"]:
            self._list_records()
            return

        client = self._instantiate_discogs_client()
        record = self._get_record(opts["record_id"])
        shortlist = self._list_discogs_releases(client, record)
        release = self._choose_release(shortlist)
        filename = self._save_cover_image(
            record, release, opts["upload_dir"], resize=not opts["no_resize"]
        )
        self._add_discogs_resources_to_db(record, release, filename)

    # -- helpers ---------------------------------------------------------------

    def _instantiate_discogs_client(self) -> discogs_client.Client:
        """Return an authenticated discogs client instance."""
        return discogs_client.Client(
            settings.D_USER_AGENT,
            consumer_key=settings.D_CONSUMER_KEY,
            consumer_secret=settings.D_CONSUMER_SECRET,
            token=settings.D_OAUTH_TOKEN,
            secret=settings.D_OAUTH_TOKEN_SECRET,
        )

    def _list_records(self) -> None:
        """Write every record without a valid discogs_id to stdout.

        Called when the ``--list`` flag is passed.
        """
        records = (
            Record.objects.filter(Q(discogs_id__isnull=True) | Q(discogs_id__lt=100))
            .order_by("id")
            .all()
        )
        for record in records:
            self.stdout.write(f"- {record.id!s} {record}")

    def _get_record(self, record_id: int | None) -> Record:
        """Return the record for ``record_id``.

        If ``record_id`` is ``None``, return the first record without a valid
        discogs_id (null or negative).

        Raises:
            CommandError: If no matching record exists.
        """
        if record_id:
            try:
                record = Record.objects.get(pk=record_id)
            except ObjectDoesNotExist:
                raise CommandError(
                    f"No record with Id {record_id!s} found in discobase."
                ) from None
        else:
            record = (
                Record.objects.filter(Q(discogs_id__isnull=True) | Q(discogs_id__lt=100))
                .order_by("id")
                .first()
            )
            if record is None:
                raise CommandError("No record without discogs_id found in discobase.")

        self.stdout.write(str(record))
        return record

    def _list_discogs_releases(
        self, client: discogs_client.Client, record: Record
    ) -> list[discogs_client.models.Release]:
        """Return the shortlist of discogs releases matching ``record``.

        Writes the shortlist to stdout.

        Raises:
            CommandError: If no release matches.
        """
        longlist = client.search(
            record.title,
            type="release",
            artist=record.artists.first().artist_name,
            year=record.year,
        )
        format_name = "Cassette" if record.record_format.id == 11 else "Vinyl"
        shortlist = [r for r in longlist if r.formats[0]["name"] == format_name]
        if len(shortlist) == 0:
            raise CommandError(
                f"No release found on discogs for record with id {record.pk!s}."
            )
        for pos, release in enumerate(shortlist):
            self.stdout.write(f"{pos} - {release.id} {release.formats}")

        return shortlist

    def _choose_release(
        self, shortlist: list[discogs_client.models.Release]
    ) -> discogs_client.models.Release:
        """Prompt the user to pick a release from the shortlist.

        Raises:
            CommandError: If the user aborts.
        """
        options = {str(i) for i in range(len(shortlist))}
        while True:
            choice = input("Please choose a release from the list (or 'exit'): ")
            if choice in options:
                return shortlist[int(choice)]
            if choice == "exit":
                raise CommandError("User exited without choosing a release.")

    def _save_cover_image(
        self,
        record: Record,
        release: discogs_client.models.Release,
        upload_dir: str,
        resize: bool,
    ) -> str | None:
        """Fetch the cover image and save it under ``MEDIA_ROOT/upload_dir``.

        Resize it to a max height of 600 px unless ``resize`` is false. Cover
        images are named ``{record_id}_0.{ext}``.
        """
        try:
            url = release.images[0]["uri"]
            request = requests.get(
                url, headers={"user-agent": f"{settings.D_USER_AGENT}"}
            )
        except TypeError:
            self.stdout.write(
                self.style.WARNING("No image found for this record variant.")
            )
            return None

        try:
            with Image.open(BytesIO(request.content)) as img:
                img_format = img.format  # only available for original image instance
                if resize and img.height > 650:
                    img = img.resize((600, int(img.width / 600)))
                filename = f"{upload_dir}/{record.pk}_0.{img_format.lower()}"
                full_path = settings.MEDIA_ROOT / filename
                full_path.absolute().parent.mkdir(parents=False, exist_ok=True)
                img.save(full_path)
                return filename

        except UnidentifiedImageError:
            self.stdout.write(
                self.style.WARNING("Could not read the downloaded image.")
            )
            return None

    def _add_discogs_resources_to_db(
        self,
        record: Record,
        release: discogs_client.models.Release,
        filename: str | None,
    ) -> None:
        """Store discogs_id and cover image path on ``record``, then create songs."""
        record.discogs_id = release.id
        record.cover_image = filename
        record.save()
        if filename:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Cover image and Discogs Id for release {release} added to DB."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Discogs Id for release {release} added to DB.")
            )

        song_list = []
        for song in release.tracklist:
            song_list.append(
                Song(record=record, position=song.position, title=song.title)
            )
        try:
            Song.objects.bulk_create(song_list)
            self.stdout.write(
                self.style.SUCCESS(f"{len(song_list)} songs added to DB.")
            )
        except IntegrityError:
            self.stdout.write(
                self.style.WARNING("No songs added, they already exist in DB.")
            )
