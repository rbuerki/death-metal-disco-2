import requests
from io import BytesIO

from PIL import Image, UnidentifiedImageError

import discogs_client
import discogs_client.models

from discobase.models import Record, Song

from django.conf import settings


def instantiate_discogs_client() -> discogs_client.Client:
    """Return an authenticated discogs client instance."""
    return discogs_client.Client(
        settings.D_USER_AGENT,
        consumer_key=settings.D_CONSUMER_KEY,
        consumer_secret=settings.D_CONSUMER_SECRET,
        token=settings.D_OAUTH_TOKEN,
        secret=settings.D_OAUTH_TOKEN_SECRET,
    )


def search_discogs_release(
    client: discogs_client.Client, record: Record
) -> discogs_client.models.Release:
    """Search matching discogs releases for the actual record.
    TODO: Simply returns the first release in the shortlist. This
    does not handle color variants properly ...
    """
    longlist = client.search(
        record.title,
        type="release",
        artist=record.artists.first().artist_name,
        year=record.year,
    )
    format_name = "Vinyl" if not record.record_format == 11 else "Cassette"
    shortlist = [r for r in longlist if r.formats[0]["name"] == format_name]
    for release in shortlist:
        print(release.id, release.formats)

    return shortlist[0]


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
            if resize and img.height > 600:
                img = img.resize((600, int(img.height / 600)))

            filename = f"{upload_dir}/{record.pk}_0.{img.format.lower()}"
            full_path = settings.MEDIA_ROOT / upload_dir / filename
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

    song_list = []
    for song in release.tracklist:
        song_list.append(Song(record=record, position=song.position, title=song.title))
    Song.objects.bulk_create(song_list)


def main(record: Record, upload_dir: str = "covers", resize: bool = True):
    client = instantiate_discogs_client()
    release = search_discogs_release(client, record)
    filename = save_cover_image(record, release, upload_dir, resize)
    add_discogs_resources_to_db(record, release, filename)


# if __name__ == "__main__":
#     main(record)
