"""
Stand-alone script to add discogs resources (cover image,
discogs_id / URL, songtitles).Is called directly from
the CLI. Either pass "list" to see all records without valid
discogs ID, or the ID of a record as argument to the function. 
If you pass none, the first record without discogs_id will be 
chosen for addition.

run with `python discobase/discogs.py [record.id | "list"]`

TODO 1: Type hints for Raise and Returns are not properly declared.
TODO 2: Maybe transform to a custom django_admin function.
"""

import os
import requests
import sys
from io import BytesIO

import discogs_client
import discogs_client.models
import django
from django.db import IntegrityError
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from PIL import Image, UnidentifiedImageError


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_disco.settings")
django.setup()
from django.conf import settings
from discobase.models import Record, Song


def instantiate_discogs_client() -> discogs_client.Client:
    """Return an authenticated discogs client instance."""
    return discogs_client.Client(
        settings.D_USER_AGENT,
        consumer_key=settings.D_CONSUMER_KEY,
        consumer_secret=settings.D_CONSUMER_SECRET,
        token=settings.D_OAUTH_TOKEN,
        secret=settings.D_OAUTH_TOKEN_SECRET,
    )


def print_help_message() -> None:
    """In case of invalid argument, print help message."""
    print(
        " Invalid argument passed to `discogs.py`. Either (1) pass 'list' \n",
        "to see all records with no valid discogs ID yet. Or (2) pass \n",
        "the ID of the record you want to add a discogs reference to. Or \n",
        "(3) pass no arg at all to return the first record without a \n",
        "discogs reference.",
    )


def print_record_list() -> None:
    """Print list of all records without a valid discogs ID. This
    function is called when the arg 'list' is passed.
    """
    records = (
        Record.objects.filter(Q(discogs_id__isnull=True) | Q(discogs_id__lt=100))
        .order_by("id")
        .all()
    )
    for record in records:
        print(f"- {str(record.id)} {record}")


def get_record(id: int | None) -> Record | None:
    """Return Record instance, for which the Id is passed. If
    no Id is passed, take the last record without a valid discogs_id or
    with a negative discogs_id. If no record is found raise
    SystemExit.
    """
    if id:
        try:
            record = Record.objects.get(pk=id)
        except ObjectDoesNotExist:
            raise SystemExit(f"No record with Id {str(id)} found in discobase.")
    else:
        record = (
            Record.objects.filter(Q(discogs_id__isnull=True) | Q(discogs_id__lt=100))
            .order_by("id")
            .first()
        )

        if record is None:
            raise SystemExit("No record without discogs_id found in discobase.")

    print(record)
    return record


def list_discogs_releases(
    client: discogs_client.Client, record: Record
) -> list[discogs_client.models.Release]:
    """Search matching discogs releases for the actual record
    the print and return a list. Exit, if no releases are found.
    """
    longlist = client.search(
        record.title,
        type="release",
        artist=record.artists.first().artist_name,
        year=record.year,
    )
    format_name = "Vinyl" if not record.record_format.id == 11 else "Cassette"
    shortlist = [r for r in longlist if r.formats[0]["name"] == format_name]
    if len(shortlist) == 0:
        raise SystemExit(
            f"No release found on discogs for record with id {str(record.pk)}."
        )
    for pos, release in enumerate(shortlist):
        print(f"{pos} - {release.id} {release.formats}")

    return shortlist


def choose_release_with_user_input(
    shortlist: list[discogs_client.models.Release],
) -> discogs_client.models.Release | None:
    """Let the user choose the release from the list (or raise a
    SystemExit if no record fits).
    """
    user_input = "xyz"
    options = [str(x) for x in range(len(shortlist))]
    promt_message = "Please choose a release from the list (or 'exit'): "
    while user_input not in options or user_input != "exit":
        user_input = input(promt_message)
        if user_input in options:
            return shortlist[int(user_input)]
        elif user_input == "exit":
            raise SystemExit()


def save_cover_image(
    record: Record,
    release: discogs_client.models.Release,
    upload_dir: str,
    resize: bool,
) -> str | None:
    """Get image from web, if necessary resize it to max height of 600
    and save it to the correct folder. By definition cover images have
    a filename like {record_id}_0.
    """
    url = release.images[0]["uri"]
    request = requests.get(url)

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
        return None


def add_discogs_resources_to_db(
    record: Record, release: discogs_client.models.Release, filename: str | None
):
    """Add discogs_id and cover_image (path) to Record model.
    Create Songs from tracklist.
    """
    record.discogs_id = release.id
    record.cover_image = filename
    record.save()
    print(f"Cover image and Discogs Id for release {release} added to DB.")

    song_list = []
    for song in release.tracklist:
        song_list.append(Song(record=record, position=song.position, title=song.title))
    try:
        Song.objects.bulk_create(song_list)
        print(f"{len(song_list)} songs added to DB.")
    except IntegrityError:
        print("No songs added, they already exist in DB.")


def main(arg: int | str | None, upload_dir: str = "covers", resize: bool = True):
    if arg == "list":
        print_record_list()
    elif isinstance(arg, int) or arg is None:
        client = instantiate_discogs_client()
        record = get_record(arg)
        release_list = list_discogs_releases(client, record)
        release = choose_release_with_user_input(release_list)
        filename = save_cover_image(record, release, upload_dir, resize)
        add_discogs_resources_to_db(record, release, filename)
    else:
        print_help_message()


if __name__ == "__main__":
    try:
        arg = sys.argv[1]
    except IndexError:
        arg = None
    if arg:
        try:
            arg = int(arg)
        except ValueError:
            pass
    main(arg)
