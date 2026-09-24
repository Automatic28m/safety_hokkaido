import unittest
from external_data.validation import validate_city, validate_region, validate_line_name


class TestValidation(unittest.TestCase):
    # ── City Validation ──────────────────────────────────────────
    def test_01_city_valid_english_names(self):
        cities = ["Sapporo", "Niseko", "Asahikawa", "Hakodate", "Otaru", "Chitose", "Kushiro"]
        for c in cities:
            is_valid, cleaned, err = validate_city(c)
            self.assertTrue(is_valid, f"Expected {c} to be valid")
            self.assertEqual(cleaned, c)
            self.assertIsNone(err)

    def test_02_city_valid_japanese_kanji(self):
        kanji_cities = ["札幌", "小樽", "函館", "旭川", "釧路"]
        for c in kanji_cities:
            is_valid, cleaned, err = validate_city(c)
            self.assertTrue(is_valid)
            self.assertEqual(cleaned, c)

    def test_03_city_whitespace_trimming(self):
        is_valid, cleaned, err = validate_city("   Sapporo   ")
        self.assertTrue(is_valid)
        self.assertEqual(cleaned, "Sapporo")

    def test_04_city_empty_or_whitespace_fails(self):
        for empty_val in ["", "   ", "\t", "\n"]:
            is_valid, _, err = validate_city(empty_val)
            self.assertFalse(is_valid)
            self.assertIn("empty", err)

    def test_05_city_non_string_type_fails(self):
        for bad_type in [123, None, ["Sapporo"], {"city": "Sapporo"}]:
            is_valid, _, err = validate_city(bad_type)
            self.assertFalse(is_valid)
            self.assertIn("must be a string", err)

    def test_06_city_excessive_length_fails(self):
        long_city = "Sapporo" * 15
        is_valid, _, err = validate_city(long_city)
        self.assertFalse(is_valid)
        self.assertIn("maximum permitted length", err)

    def test_07_city_injection_symbols_fail(self):
        injections = [
            "Sapporo; DROP TABLE cities;",
            "Sapporo <script>alert(1)</script>",
            "Sapporo\r\nSET-COOKIE",
            "Sapporo?query=1&admin=true",
            "Sapporo | cat /etc/passwd"
        ]
        for inj in injections:
            is_valid, _, err = validate_city(inj)
            self.assertFalse(is_valid, f"Expected {inj} to fail")
            self.assertIn("invalid or unsafe", err)

    # ── Region Validation ────────────────────────────────────────
    def test_08_region_valid_hokkaido_scope(self):
        regions = ["Hokkaido", "Sapporo", "Hakodate", "Tokachi", "Ishikari", "北海道"]
        for r in regions:
            is_valid, norm, err = validate_region(r)
            self.assertTrue(is_valid, f"Expected {r} to be in scope")

    def test_09_region_defaults_to_hokkaido_on_none_or_empty(self):
        for val in [None, "", "   "]:
            is_valid, norm, err = validate_region(val)
            self.assertTrue(is_valid)
            self.assertEqual(norm, "Hokkaido")

    def test_10_region_out_of_scope_fails(self):
        foreign_regions = ["Paris", "London", "New York", "Bangkok", "Tokyo"]
        for fr in foreign_regions:
            is_valid, norm, err = validate_region(fr)
            self.assertFalse(is_valid)
            self.assertIn("outside the supported Hokkaido service scope", err)

    def test_11_region_non_string_fails(self):
        is_valid, _, err = validate_region(999)
        self.assertFalse(is_valid)
        self.assertIn("must be a string", err)

    # ── Line Name Validation ─────────────────────────────────────
    def test_12_line_name_valid_jr_hokkaido(self):
        valid_lines = ["Rapid Airport", "Hakodate Line", "Chitose Line", "Muroran Line", "All"]
        for line in valid_lines:
            is_valid, norm, err = validate_line_name(line)
            self.assertTrue(is_valid, f"Expected line {line} to be valid")

    def test_13_line_name_defaults_to_all_on_none_or_empty(self):
        for empty_val in [None, "", "   "]:
            is_valid, norm, err = validate_line_name(empty_val)
            self.assertTrue(is_valid)
            self.assertEqual(norm, "All")

    def test_14_line_name_out_of_scope_fails(self):
        non_hokkaido_lines = ["Yamanote Line", "Chuo Line", "Tokaido Shinkansen", "Ginza Line"]
        for line in non_hokkaido_lines:
            is_valid, _, err = validate_line_name(line)
            self.assertFalse(is_valid)
            self.assertIn("outside the known JR Hokkaido operational scope", err)


if __name__ == "__main__":
    unittest.main()
