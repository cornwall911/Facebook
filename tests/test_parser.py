from fb_winner_scout.parser import parse_count

def test_parse_count():
    assert parse_count("250") == 250
    assert parse_count("1.2K") == 1200
    assert parse_count("15.5k") == 15500
    assert parse_count("2M") == 2000000
    assert parse_count("٣٥٠") == 350
    assert parse_count("١٫٢ ألف") == 1200
    assert parse_count("0") == 0
    assert parse_count(None) == 0
    assert parse_count("") == 0
    assert parse_count("45 comments") == 45
    assert parse_count("1.4K shares") == 1400
    print("All parse_count tests passed successfully!")

if __name__ == "__main__":
    test_parse_count()
