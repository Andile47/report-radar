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
