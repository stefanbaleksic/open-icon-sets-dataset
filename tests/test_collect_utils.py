"""Unit tests for the collection helpers: UTC day conversion, the cut-off and semantic version tags.
Standard library only. Run from the repository root:  python3 -I tests/test_collect_utils.py
Exit status 1 if any test fails."""
import os, sys, unittest
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'collect'))
from common import utc_day, CUTOFF, CUTOFF_ISO, SEMVER  # noqa: E402


class UtcDay(unittest.TestCase):
    def test_local_day_is_moved_to_utc(self):
        # The case that caused the release correction: 01:17 on 17 Nov in +08:00 is 16 Nov in UTC.
        self.assertEqual(utc_day('2026-11-17T01:17:00+08:00'), '2026-11-16')

    def test_same_day_when_offset_is_positive_and_late_enough(self):
        self.assertEqual(utc_day('2026-11-13T15:07:06+01:00'), '2026-11-13')

    def test_negative_offset_moves_to_next_day(self):
        self.assertEqual(utc_day('2026-11-16T23:30:00-02:00'), '2026-11-17')

    def test_z_suffix(self):
        self.assertEqual(utc_day('2026-11-16T23:59:59Z'), '2026-11-16')

    def test_day_boundary_at_midnight_utc(self):
        self.assertEqual(utc_day('2026-11-17T00:00:00Z'), '2026-11-17')
        self.assertEqual(utc_day('2026-11-16T23:59:59+00:00'), '2026-11-16')

    def test_dst_change_day(self):
        # Europe switches to CET (+01:00) on 2026-10-25; the UTC day must not change because of the switch.
        self.assertEqual(utc_day('2026-10-25T02:30:00+02:00'), '2026-10-25')
        self.assertEqual(utc_day('2026-10-25T02:30:00+01:00'), '2026-10-25')


class Cutoff(unittest.TestCase):
    def test_cutoff_is_end_of_collection_day_in_utc(self):
        self.assertEqual(CUTOFF, datetime(2026, 11, 16, 23, 59, 59, tzinfo=timezone.utc))
        self.assertEqual(CUTOFF_ISO, '2026-11-16T23:59:59Z')

    def test_iso_cutoff_matches_datetime_cutoff(self):
        parsed = datetime.fromisoformat(CUTOFF_ISO.replace('Z', '+00:00'))
        self.assertEqual(parsed, CUTOFF)

    def test_commit_on_cutoff_day_in_utc_is_inside(self):
        commit = datetime.fromisoformat('2026-11-16T23:00:00+00:00')
        self.assertLessEqual(commit, CUTOFF)

    def test_commit_just_after_cutoff_is_outside(self):
        commit = datetime.fromisoformat('2026-11-17T00:00:00+00:00')
        self.assertGreater(commit, CUTOFF)


class Semver(unittest.TestCase):
    def test_accepts_plain_and_v_prefixed(self):
        self.assertEqual(SEMVER.match('v1.2.3').groups(), ('1', '2', '3'))
        self.assertEqual(SEMVER.match('10.0.12').groups(), ('10', '0', '12'))

    def test_rejects_partial_versions(self):
        self.assertIsNone(SEMVER.match('1.2'))
        self.assertIsNone(SEMVER.match('v2'))

    def test_rejects_prerelease_and_build_suffixes(self):
        self.assertIsNone(SEMVER.match('1.2.3-beta.1'))
        self.assertIsNone(SEMVER.match('1.2.3+build5'))

    def test_rejects_four_part_and_other_prefixes(self):
        self.assertIsNone(SEMVER.match('1.2.3.4'))
        self.assertIsNone(SEMVER.match('release-1.2.3'))

    def test_numeric_order_not_string_order(self):
        names = ['v1.10.0', 'v1.9.0', 'v1.2.3']
        key = lambda n: tuple(int(x) for x in SEMVER.match(n).groups())
        self.assertEqual(sorted(names, key=key), ['v1.2.3', 'v1.9.0', 'v1.10.0'])


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=1).result
    sys.exit(1 if (result.failures or result.errors) else 0)
