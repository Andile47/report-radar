from governance.privacy import mask_personal_info


def test_masks_phone_numbers():
    assert mask_personal_info("Call me on 082 123 4567") == "Call me on [PHONE]"
    assert mask_personal_info("Call +27 82 123 4567 please") == "Call [PHONE] please"


def test_masks_id_number():
    assert mask_personal_info("ID 8001015009087 reported it") == "ID [ID] reported it"


def test_masks_email():
    assert mask_personal_info("Email thandi@example.com") == "Email [EMAIL]"


def test_masks_house_number_but_keeps_street():
    assert mask_personal_info("No water at 12 Jukskei Street") == "No water at [HOUSE_NO] Jukskei Street"


def test_masks_names():
    assert mask_personal_info("Mr Dlamini reported a leak") == "[NAME] reported a leak"
    assert mask_personal_info("My name is Thandi and the tap is dry") == "My name is [NAME] and the tap is dry"


def test_leaves_normal_reports_unchanged():
    text = "Sewage overflowing from manhole on Roosevelt Street near 10th Avenue"
    assert mask_personal_info(text) == text


def test_non_text_is_returned_as_is():
    assert mask_personal_info(None) is None


def test_masks_house_numbers_written_without_a_street():
    assert mask_personal_info("No water at house 23 since Monday") == "No water at house [HOUSE_NO] since Monday"
    assert mask_personal_info("Pipe burst outside no. 14") == "Pipe burst outside no. [HOUSE_NO]"
    assert mask_personal_info("Stand 512B has no electricity") == "Stand [HOUSE_NO] has no electricity"
    assert mask_personal_info("Flat number 7 is flooded") == "Flat number [HOUSE_NO] is flooded"


def test_counts_and_durations_are_not_mistaken_for_house_numbers():
    text = "No water for 3 days, 12 houses affected, no 2nd supply"
    assert mask_personal_info(text) == text


def test_masks_phone_numbers_in_other_groupings():
    for phone in ("(082) 123 4567", "082 1234 567", "082-123-4567", "0821234567",
                  "+27 (0)82 123 4567", "0027 82 123 4567", "011 234 5678"):
        assert mask_personal_info(f"Call {phone} today") == "Call [PHONE] today", phone


def test_masks_id_numbers_written_in_groups():
    for id_number in ("900101 5009 087", "900101-5009-087", "9001015009087"):
        assert mask_personal_info(f"ID {id_number} reported it") == "ID [ID] reported it", id_number


def test_times_dates_and_counts_are_not_mistaken_for_phone_or_id_numbers():
    text = "Outage from 0800-1700 on 2026-11-02, 120 homes, meter 4567 1234"
    assert mask_personal_info(text) == text
