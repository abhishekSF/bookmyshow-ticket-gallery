from movie_filter import is_movie_booking, score_email


def test_one_keyword_is_not_a_decision_to_skip():
    assert is_movie_booking("Thanks for booking. Concert night.") is True
    assert is_movie_booking("Your PVR booking is confirmed.") is True


def test_event_score_wins():
    text = "Concert at the Festival grounds. Comedy Match night. Theatre doors 6pm."
    scores = score_email(text)
    assert scores["event"] > scores["movie"]
    assert is_movie_booking(text) is False


def test_movie_markers_keep():
    text = "PVR INOX Screen 5 IMAX Cinema, Koramangala"
    scores = score_email(text)
    assert scores["movie"] >= 2
    assert is_movie_booking(text) is True


def test_tie_does_not_skip():
    text = "PVR Cinema plus a Theatre mention"
    scores = score_email(text)
    assert scores["movie"] >= 1 and scores["event"] >= 1
    if scores["event"] == scores["movie"]:
        assert is_movie_booking(text) is True
