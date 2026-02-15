from app.services.pricing import remove_outliers_iqr


def test_outlier_removal():
    vals = [10, 11, 12, 12, 13, 11, 12, 500]
    cleaned = remove_outliers_iqr(vals)
    assert 500 not in cleaned
