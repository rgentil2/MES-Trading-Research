from pathlib import Path

from src.data_pipeline import build_continuous


def _write_contract(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_ninjatrader_implicit_rollover_keeps_old_until_end(tmp_path: Path):
    old = tmp_path / "MES 03-26.Last.txt"
    new = tmp_path / "MES 06-26.Last.txt"

    _write_contract(
        old,
        [
            "20260316 035900;5000;5000.25;4999.75;5000;10",
            "20260316 040000;5000;5000.25;4999.75;5000;11",
        ],
    )
    _write_contract(
        new,
        [
            "20260316 035900;5001;5001.25;5000.75;5001;20",
            "20260316 040000;5001;5001.25;5000.75;5001;21",
            "20260316 040100;5001;5001.25;5000.75;5001;22",
        ],
    )

    continuous, manifest, transitions = build_continuous(
        [old, new], timestamp_timezone="UTC", tick_size=0.25
    )

    assert len(continuous) == 3
    assert continuous.iloc[-1]["contract"] == "MES 06-26"
    assert bool(continuous.iloc[-1]["is_rollover"]) is True
    assert continuous.iloc[-1]["rollover_from"] == "MES 03-26"
    assert int(manifest.iloc[1]["overlap_rows_removed"]) == 2
    assert float(transitions.iloc[0]["gap_minutes"]) == 1.0
    assert continuous["timestamp_utc"].is_monotonic_increasing
    assert not continuous["timestamp_utc"].duplicated().any()
