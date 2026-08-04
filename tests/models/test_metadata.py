from datetime import datetime, timezone

from app.models.metadata import Metadata


def test_metadata():

    metadata = Metadata(
        source="SEC",
        source_url="https://www.sec.gov",
        checksum="abcdef123456",
        valid_at=datetime.now(timezone.utc),
    )

    assert metadata.source == "SEC"

    assert metadata.ingested_at is not None