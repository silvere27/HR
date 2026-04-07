from hr_insights.storage import ReportStore


def test_report_store_roundtrip(tmp_path):
    db_path = tmp_path / "reports.db"
    store = ReportStore(str(db_path))

    store.save_report(report_type="kpis", csv_path="data/sample.csv", as_of="2026-01-01", payload={"a": 1})
    rows = store.list_reports(report_type="kpis", limit=10)

    assert len(rows) == 1
    assert rows[0].id >= 1
    assert rows[0].report_type == "kpis"
    assert rows[0].payload["a"] == 1


def test_report_store_csv_export(tmp_path):
    db_path = tmp_path / "reports.db"
    store = ReportStore(str(db_path))
    store.save_report(report_type="quality", csv_path="data/sample.csv", as_of=None, payload={"score": 0.9})

    csv_data = store.list_reports_csv(report_type="quality", limit=10)

    assert "id,created_at,report_type,csv_path,as_of,payload_json" in csv_data
    assert "quality" in csv_data
    assert "score" in csv_data


def test_report_store_offset_pagination(tmp_path):
    db_path = tmp_path / "reports.db"
    store = ReportStore(str(db_path))
    for idx in range(3):
        store.save_report(report_type="kpis", csv_path=f"data/{idx}.csv", as_of=None, payload={"idx": idx})

    first_page = store.list_reports(report_type="kpis", limit=1, offset=0)
    second_page = store.list_reports(report_type="kpis", limit=1, offset=1)

    assert len(first_page) == 1
    assert len(second_page) == 1
    assert first_page[0].id != second_page[0].id


def test_report_store_created_at_filters(tmp_path):
    db_path = tmp_path / "reports.db"
    store = ReportStore(str(db_path))
    store.save_report(report_type="kpis", csv_path="data/sample.csv", as_of=None, payload={"x": 1})
    rows = store.list_reports(created_after="1900-01-01T00:00:00+00:00", created_before="2999-01-01T00:00:00+00:00")
    assert len(rows) == 1
