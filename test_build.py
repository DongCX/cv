import unittest

from build import inline


class InlineRenderingTests(unittest.TestCase):
    def test_bold_label_uses_breakable_space(self):
        self.assertEqual(inline("**標題**　內容"), "<strong>標題</strong> 內容")

    def test_preserves_regular_bold_text(self):
        self.assertEqual(inline("**Title** text"), "<strong>Title</strong> text")

    def test_escapes_html_before_rendering_bold_text(self):
        self.assertEqual(
            inline("A < B & **標題**"),
            "A &lt; B &amp; <strong>標題</strong>",
        )


if __name__ == "__main__":
    unittest.main()
