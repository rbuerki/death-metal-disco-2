import requests
import yaml
from pathlib import Path
from io import BytesIO

from PIL import Image, UnidentifiedImageError

import discogs_client
import discogs_client.models

from discobase.models import Record, Song


# Discogs authentication
with open(Path.cwd().parent / "config.yaml", "r") as f:
    yaml_content = yaml.safe_load(f)


d_user_agent = yaml_content["DISCOGS"]["USER-AGENT"]
d_consumer_key = yaml_content["DISCOGS"]["CONSUMER_KEY"]
d_consumer_secret = yaml_content["DISCOGS"]["CONSUMER_SECRET"]
d_oauth_token = yaml_content["DISCOGS"]["OAUTH_TOKEN"]
d_oauth_token_secret = yaml_content["DISCOGS"]["OAUTH_TOKEN_SECRET"]


def instantiate_discogs_client() -> discogs_client.Client:
    """Return an authenticated discogs client instance."""
    return discogs_client.Client(
        d_user_agent,
        consumer_key=d_consumer_key,
        consumer_secret=d_consumer_secret,
        token=d_oauth_token,
        secret=d_oauth_token_secret,
    )


def search_discogs_release(
    client: discogs_client.Client, r: Record
) -> discogs_client.models.Release:
    """Search matching discogs releases for the actual record.
    TODO: Simply return the first release in the shortlist. This
    does not handle color variants properly ...
    """
    longlist = client.search(
        r.title,
        type="release",
        artist=r.artists.first().artist_name,
        year=r.year,
    )
    format_name = "Vinyl" if not r.record_format == 11 else "Cassette"
    shortlist = [r for r in longlist if r.formats[0]["name"] == format_name]
    for release in shortlist:
        print(release.id, release.formats)

    return shortlist[0]


def save_cover_image(r: Record, url: str, upload_dir: Path):
    request = requests.get(url)
    BASE_DIR = Path(__file__).resolve().parent.parent  # TODO move to better place

    try:
        with Image.open(BytesIO(request.content)) as img:

            file_name = f"{r.pk}_0.{img.format.lower()}"
            path_to_image = Path(f"record_{r.pk}") / file_name
            full_path = BASE_DIR / "media" / upload_dir / path_to_image
            full_path.absolute().parent.mkdir(parents=False, exist_ok=True)
            img.save(full_path)

            return path_to_image

    except UnidentifiedImageError:
        return None


def add_discogs_resources(
    r: Record, release: discogs_client.models.Release, save_path: Path
):
    """Add discogs_id and cover_image (path) to Record model. Create Songs."""
    r.discogs_id = release.id
    r.cover_image = save_path
    r.save()

    song_list = []
    for song in release.tracklist:
        song_list.append(Song(record=r, position=song.position, title=song.title))
    Song.objects.bulk_create(song_list)
