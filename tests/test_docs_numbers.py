"""Checks that the figures quoted in the documentation match the data, and that the citation version matches the changelog.
Standard library only. Run from the repository root:  python3 -I tests/test_docs_numbers.py
Exit status 1 if any check fails. This prevents the counts in README, CHANGELOG, RULES and COVERAGE from drifting apart
from the table (for example after a correction or a new collection run)."""
import csv, os, re, sys, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
        return f.read()


def expected():
    with open(os.path.join(ROOT, 'data/icon_sets_v3.csv'), encoding='utf-8') as f:
        rel = list(csv.reader(f))
    header, body = rel[0], rel[1:]
    with open(os.path.join(ROOT, 'evidence/collected.csv'), encoding='utf-8') as f:
        coll = list(csv.DictReader(f))
    filled = [c for c in header if any((r.get(c) or '') != '' for r in coll)]
    with open(os.path.join(ROOT, 'build_input/corrections.csv'), encoding='utf-8') as f:
        corr = list(csv.DictReader(f))
    info = sum(1 for line in read('tests/duplicate_report.txt').splitlines() if re.match(r'^\s+INFO ', line))
    with open(os.path.join(ROOT, 'data/overlap_blanked.csv'), encoding='utf-8') as f:
        blanked = sum(1 for _ in csv.DictReader(f))
    compared = int(re.search(r'match (\d+), differs 0', read('tests/collection_compare.md')).group(1))
    return {'rows': len(body), 'columns': len(header), 'filled': len(filled), 'unfilled': len(header) - len(filled),
            'corrections': len(corr), 'info': info, 'blanked': blanked, 'compared': compared}


class DocsMatchData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e = expected()

    def test_table_size(self):
        self.assertEqual(self.e['rows'], 571)
        self.assertEqual(self.e['columns'], 124)

    def test_readme_figures(self):
        s = read('README.md')
        self.assertIn(f"It has {self.e['corrections']:,} rows", s)
        self.assertIn(f"{self.e['info']} INFO lines", s)
        self.assertIn(f"{self.e['unfilled']} of 124 columns", s)
        self.assertIn(f"({self.e['blanked']} rows)", s)
        self.assertIn(f"{self.e['compared']:,} cells compared", s)

    def test_changelog_figures(self):
        s = read('CHANGELOG.md')
        self.assertIn(f"{self.e['corrections']:,} cells corrected", s)
        self.assertIn(f"{self.e['unfilled']} of 124 columns", s)

    def test_rules_figures(self):
        s = read('collect/RULES.md')
        self.assertIn(f"({self.e['corrections']:,} rows)", s)
        self.assertIn(f"{self.e['unfilled']} columns are not filled", s)

    def test_coverage_figures(self):
        s = read('collect/COVERAGE.md')
        self.assertIn(f"Filled ({self.e['filled']} of 124 columns)", s)
        self.assertIn(f"Not filled ({self.e['unfilled']} columns)", s)

    def test_no_stale_figures(self):
        for rel in ['README.md', 'CHANGELOG.md', 'collect/RULES.md', 'collect/COVERAGE.md', 'collect/README.md']:
            s = read(rel)
            for stale in ['1,769', '131 rows', '38 of 124', '38 columns', '33 INFO', '30,853', '(10 rows)', 'v3-draft']:
                self.assertNotIn(stale, s, f'{rel} still says {stale!r}')


class CitationMatchesChangelog(unittest.TestCase):
    def test_version(self):
        latest = re.search(r'^## \[([^\]]+)\]', read('CHANGELOG.md'), re.M).group(1)
        cff = re.search(r'^version:\s*"?([^"\n]+)"?', read('CITATION.cff'), re.M).group(1)
        self.assertEqual(cff, latest)


if __name__ == '__main__':
    unittest.main(verbosity=1)
