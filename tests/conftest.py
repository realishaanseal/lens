import pytest

from lens.config import Client, Competitor, Listing, Service
from lens.store import Store


@pytest.fixture
def client():
    return Client(
        id="test", name="SSHRI Hospital", category="hospital", city="Krishnanagar", city_bn="কৃষ্ণনগর",
        area="Nadia", aliases=["SSHRI Multispeciality Hospital"], doctors=["Dr. Ananya Roy"],
        phones=["+91 98300 12345"],
        services=[Service("Cardiology", "হৃদরোগ", "/cardiology"), Service("Nephrology", "কিডনি")],
        competitors=[Competitor("Hospital B"), Competitor("City Care Nursing Home", ["City Care"])],
        listings=[Listing("Website", "+91 90000 00001"), Listing("Google", "+91 90000 00002")],
        google_reviews=40, has_physician_schema=False,
    )


@pytest.fixture
def store():
    return Store(":memory:")
