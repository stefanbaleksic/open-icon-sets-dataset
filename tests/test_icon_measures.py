"""Unit tests for the icon-content measures (collect/icon_measures.py). Standard library only.
Each expected value is worked out by hand from the rule in collect/RULES.md ("Icon contents").
Run from the repository root:  python3 -I tests/test_icon_measures.py
Exit status 1 if any test fails."""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'collect'))
import icon_measures as im  # noqa: E402


def icon(body, vb_h=24, own=False, name='x'):
    return {'name': name, 'body': body, 'vb_h': vb_h, 'own': own}


class Num(unittest.TestCase):
    def test_whole_and_decimal(self):
        self.assertEqual(im.num(3.0), 3)
        self.assertEqual(im.num(2.5), 2.5)
        self.assertEqual(im.num(2.46), 2.5)
        self.assertIsNone(im.num(None))


class SvgIcon(unittest.TestCase):
    def test_body_is_content_without_svg_tag(self):
        text = '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M1 1"/></svg>'
        ic = im.svg_icon('package/line/home.svg', text)
        self.assertEqual(ic['name'], 'home')
        self.assertEqual(ic['body'], '<path d="M1 1"/>')
        self.assertEqual(ic['vb_h'], 24.0)
        self.assertFalse(ic['own'])

    def test_file_without_svg_tag_is_skipped(self):
        self.assertIsNone(im.svg_icon('package/broken.svg', 'not an icon'))

    def test_viewbox_needs_four_numbers(self):
        ic = im.svg_icon('a.svg', '<svg viewBox="0 0 24">x</svg>')
        self.assertIsNone(ic['vb_h'])


class Measures(unittest.TestCase):
    def test_empty_set(self):
        self.assertEqual(im.measures([]), {})

    def test_monotone_palette_and_currentcolor(self):
        m = im.measures([icon('<path fill="currentColor" d="M0 0"/>'), icon('<path d="M1 1"/>')])
        self.assertEqual(m['icons_currentcolor_pct'], 50.0)
        self.assertEqual(m['icons_hardcoded_color_pct'], 0.0)
        self.assertEqual(m['measured_palette'], 'monotone')

    def test_black_and_white_are_not_hard_coded_colours(self):
        m = im.measures([icon('<path fill="#000" d="M0 0"/>'), icon('<path stroke="white" d="M0 0"/>')])
        self.assertEqual(m['icons_hardcoded_color_pct'], 0.0)

    def test_multicolor_palette(self):
        m = im.measures([icon('<path fill="#ff0000" d="M0 0"/>'), icon('<path fill="rgb(0,128,0)" d="M0 0"/>')])
        self.assertEqual(m['icons_hardcoded_color_pct'], 100.0)
        self.assertEqual(m['measured_palette'], 'multicolor')

    def test_gradient_counts_as_multicolor_at_half(self):
        m = im.measures([icon('<linearGradient id="g"/>'), icon('<path d="M0 0"/>')])
        self.assertEqual(m['icons_gradient_pct'], 50.0)
        self.assertEqual(m['measured_palette'], 'multicolor')

    def test_stroke_construction_and_width_mode(self):
        icons = [icon('<path stroke="currentColor" stroke-width="2" d="M0 0"/>'),
                 icon('<path stroke="currentColor" stroke-width="2" d="M1 1"/>'),
                 icon('<path stroke="currentColor" stroke-width="1.5" d="M2 2"/>')]
        m = im.measures(icons)
        self.assertEqual(m['icons_stroke_based_pct'], 100.0)
        self.assertEqual(m['icon_construction'], 'stroke')
        self.assertEqual(m['stroke_width_mode'], 2)

    def test_stroke_zero_width_is_not_stroke_based(self):
        m = im.measures([icon('<path stroke="red" stroke-width="0" d="M0 0"/>')])
        self.assertEqual(m['icons_stroke_based_pct'], 0.0)
        self.assertEqual(m['icon_construction'], 'fill')

    def test_animation_and_byte_sizes(self):
        m = im.measures([icon('ab', ), icon('abcd<animate/>')])
        self.assertEqual(m['icons_animated_n'], 1)
        self.assertEqual(m['median_icon_bytes'], 8)  # sizes 2 and 14 bytes: median 8
        self.assertEqual(m['mean_icon_bytes'], 8)    # mean 8

    def test_mean_is_rounded_to_nearest_byte(self):
        m = im.measures([icon('a' * 1), icon('a' * 2)])  # mean 1.5 rounds to 2
        self.assertEqual(m['mean_icon_bytes'], 2)

    def test_viewbox_mode(self):
        m = im.measures([icon('x', vb_h=24), icon('y', vb_h=24), icon('z', vb_h=16)])
        self.assertEqual(m['icon_viewbox_px'], 24)


class Fingerprints(unittest.TestCase):
    def test_exact_differs_but_rounded_matches(self):
        a = [icon('<path d="M1.23 0"/>')]
        b = [icon('<path d="M1.21 0"/>')]
        ea, ra = im.fingerprints(a)
        eb, rb = im.fingerprints(b)
        self.assertNotEqual(ea, eb)
        self.assertEqual(ra, rb)

    def test_icons_without_path_data_are_skipped(self):
        ex, rd = im.fingerprints([icon('<rect width="2"/>'), icon('<path d="M0 0"/>')])
        self.assertEqual(len(ex), 1)
        self.assertEqual(len(rd), 1)


class StyleVariants(unittest.TestCase):
    def test_two_styles_across_bases(self):
        names = ['arrow-line', 'arrow-fill', 'home-line', 'home-fill', 'star-line', 'star-fill']
        self.assertEqual(im.style_variants(names), ['fill', 'line'])
        self.assertEqual(sorted(im.base_names(names, ['fill', 'line'])), ['arrow', 'home', 'star'])

    def test_single_style_is_not_reported(self):
        names = ['arrow-line', 'home-line', 'star-line']
        self.assertEqual(im.style_variants(names), [])

    def test_unrelated_hyphen_words_are_not_styles(self):
        names = ['alarm-clock', 'arrow-up', 'home-page', 'star-rate']
        self.assertEqual(im.style_variants(names), [])


class Overlap(unittest.TestCase):
    def _fp(self, prefix, n=25):
        return [f'{prefix}{i}' for i in range(n)]

    def test_full_overlap_across_packages(self):
        fps = self._fp('h')
        result = {'a': {'fp_exact': fps, 'fp_rounded': fps}, 'b': {'fp_exact': fps, 'fp_rounded': fps}}
        pkg_of = {'a': 'pkg-a', 'b': 'pkg-b'}
        ov = im.overlap(result, pkg_of, 'fp_exact')
        self.assertEqual(ov['a'], (100.0, 'b'))

    def test_same_package_does_not_count(self):
        fps = self._fp('h')
        result = {'a': {'fp_exact': fps}, 'b': {'fp_exact': fps}}
        pkg_of = {'a': 'same', 'b': 'same'}
        self.assertEqual(im.overlap(result, pkg_of, 'fp_exact')['a'], (0.0, ''))

    def test_too_few_fingerprints_gives_none(self):
        result = {'a': {'fp_exact': self._fp('h', 19)}, 'b': {'fp_exact': self._fp('h', 19)}}
        self.assertEqual(im.overlap(result, {'a': 'x', 'b': 'y'}, 'fp_exact')['a'], (None, ''))

    def test_partial_overlap_share(self):
        shared = self._fp('s', 10)
        result = {'a': {'fp_exact': shared + self._fp('a', 10)}, 'b': {'fp_exact': shared + self._fp('b', 10)}}
        self.assertEqual(im.overlap(result, {'a': 'x', 'b': 'y'}, 'fp_exact')['a'], (50.0, 'b'))

    def test_best_overlap_takes_higher_basis(self):
        exact_a = self._fp('e', 20)
        result = {'a': {'fp_exact': exact_a, 'fp_rounded': exact_a},
                  'b': {'fp_exact': self._fp('z', 20), 'fp_rounded': exact_a}}
        pct, other, basis = im.best_overlap(result, {'a': 'x', 'b': 'y'})['a']
        self.assertEqual((pct, other, basis), (100.0, 'b', 'rounded_1dp'))


class RemixOverlap(unittest.TestCase):
    def test_share_of_base_names(self):
        self.assertEqual(im.remix_overlap(['a', 'b', 'c', 'd'], {'a', 'b'}), 50.0)

    def test_no_reference_gives_none(self):
        self.assertIsNone(im.remix_overlap(['a'], set()))


if __name__ == '__main__':
    unittest.main(verbosity=1)
