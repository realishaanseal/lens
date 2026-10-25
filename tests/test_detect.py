from lens.detect import detect_mention, extract_competitors, normalize


def test_exact_match_ignores_case_and_markdown(client):
    m = detect_mention(client, "1. **sshri hospital** – good cardiology team.")
    assert m.found and m.alias == "SSHRI Hospital" and m.score == 1.0


def test_fuzzy_match_catches_small_misspellings(client):
    assert detect_mention(client, "Try SSHRI Multispecialty Hospital near the station.").found


def test_doctor_name_counts_as_mention(client):
    m = detect_mention(client, "Dr Ananya Roy is a well known cardiologist.")
    assert m.found and m.alias == "Dr. Ananya Roy"


def test_phone_number_counts_as_mention(client):
    assert detect_mention(client, "Call 98300-12345 for appointments.").found


def test_no_false_positive_on_other_hospitals(client):
    text = "Options include Nadia Medicare Hospital, Shri Ram Hospital and City Care Nursing Home."
    assert not detect_mention(client, text).found


def test_word_hospital_alone_does_not_match_hospital_b(client):
    hits = extract_competitors(client, "SSHRI Hospital is a good hospital in town.")
    assert all(h.name != "Hospital B" for h in hits)


def test_bengali_text_is_matched(client):
    client.aliases.append("শ্রী হাসপাতাল")
    assert detect_mention(client, "কৃষ্ণনগরে শ্রী হাসপাতাল ভালো।").found


def test_competitors_known_and_discovered(client):
    text = ("1. **SSHRI Hospital** – top pick\n2. **City Care** – affordable\n"
            "3. Jeevan Deep Nursing Home – 24x7\nAlso consider Dr. P. K. Das for kidney care.")
    hits = {h.name: h.kind for h in extract_competitors(client, text)}
    assert hits["City Care Nursing Home"] == "known"
    assert hits["Jeevan Deep Nursing Home"] == "business"
    assert hits["Dr. P. K. Das"] == "doctor"
    assert "SSHRI Hospital" not in hits


def test_normalize_keeps_bengali_marks():
    assert normalize("হাসপাতাল!") == "হাসপাতাল"
