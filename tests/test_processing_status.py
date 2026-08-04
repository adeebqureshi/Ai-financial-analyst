from app.enums.processing_status import ProcessingStatus


def test_processing_status():

    assert ProcessingStatus.PENDING.value == "pending"

    assert ProcessingStatus.COMPLETED.value == "completed"

    assert ProcessingStatus.FAILED.value == "failed"