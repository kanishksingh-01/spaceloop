import os
import unittest

class ThemeTokensAndConfigTestCase(unittest.TestCase):
    """Verifies that Ocean Breeze light theme and Midnight Neon dark theme tokens are strictly preserved."""

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.css_path = os.path.join(self.base_dir, 'frontend', 'src', 'styles', 'index.css')
        self.tailwind_path = os.path.join(self.base_dir, 'frontend', 'tailwind.config.js')
        self.context_path = os.path.join(self.base_dir, 'frontend', 'src', 'context', 'ThemeContext.tsx')
        self.public_index = os.path.join(self.base_dir, 'public', 'index.html')

    def test_ocean_breeze_mandatory_palette_hex_codes(self):
        with open(self.css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        # Primary Blue
        self.assertIn('#0B3D91', css_content)
        # Secondary Blue
        self.assertIn('#3BA7F2', css_content)
        # Tertiary Aqua
        self.assertIn('#7FE7D6', css_content)
        # Light Background
        self.assertIn('#E8F6FF', css_content)

    def test_dark_mode_tokens_preserved(self):
        with open(self.css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        # Canvas Obsidian
        self.assertIn('#020617', css_content)
        # Surface Slate 900
        self.assertIn('#0f172a', css_content)
        # Seeker Indigo
        self.assertIn('#4f46e5', css_content)
        # Host Amber
        self.assertIn('#f59e0b', css_content)

    def test_tailwind_config_ocean_tokens(self):
        with open(self.tailwind_path, 'r', encoding='utf-8') as f:
            tw_content = f.read()

        self.assertIn('ocean:', tw_content)
        self.assertIn('#0B3D91', tw_content)
        self.assertIn('#3BA7F2', tw_content)
        self.assertIn('#7FE7D6', tw_content)
        self.assertIn('#E8F6FF', tw_content)

    def test_theme_context_supports_light_and_dark(self):
        with open(self.context_path, 'r', encoding='utf-8') as f:
            tc_content = f.read()

        self.assertIn("'dark' | 'light'", tc_content)
        self.assertIn('spaceloop-theme', tc_content)
        self.assertIn('toggleTheme', tc_content)

    def test_public_build_distribution_synced(self):
        self.assertTrue(os.path.exists(self.public_index))
        public_assets = os.path.join(self.base_dir, 'public', 'assets')
        self.assertTrue(os.path.isdir(public_assets))
        files = os.listdir(public_assets)
        has_js = any(f.endswith('.js') for f in files)
        has_css = any(f.endswith('.css') for f in files)
        self.assertTrue(has_js, "Public assets missing compiled JS bundle")
        self.assertTrue(has_css, "Public assets missing compiled CSS bundle")

if __name__ == '__main__':
    unittest.main()
