import unittest
from contextlib import redirect_stdout
from io import StringIO

from proxy_config import ConfigError, configure_telegram_proxy, load_proxy_config, load_settings


class DummyApiHelper:
    proxy = {"https": "old"}


class ProxyConfigTest(unittest.TestCase):
    def test_prefers_telegram_proxy_url(self):
        config = load_proxy_config(
            {
                "TELEGRAM_PROXY_URL": "socks5h://user:pass@proxy.local:1080",
                "SOCKS5_PROXY_URL": "socks5://legacy.local:1080",
            }
        )

        self.assertEqual(config.url, "socks5h://user:pass@proxy.local:1080")
        self.assertEqual(config.source, "TELEGRAM_PROXY_URL")

    def test_uses_standard_proxy_fallbacks(self):
        config = load_proxy_config({"HTTPS_PROXY": "http://proxy.local:3128"})

        self.assertEqual(config.url, "http://proxy.local:3128")
        self.assertEqual(config.source, "HTTPS_PROXY")

    def test_rejects_unsupported_proxy_scheme(self):
        with self.assertRaises(ConfigError):
            load_proxy_config({"TELEGRAM_PROXY_URL": "ftp://proxy.local:21"})

    def test_warns_about_socks5_dns_in_docker(self):
        config = load_proxy_config({"SOCKS5_PROXY_URL": "socks5://proxy.local:1080"})

        self.assertEqual(config.url, "socks5://proxy.local:1080")
        self.assertEqual(len(config.warnings), 1)

    def test_requires_proxy_when_enabled(self):
        with self.assertRaises(ConfigError):
            load_proxy_config({"TELEGRAM_REQUIRE_PROXY": "1"})

    def test_ignores_mtproxy_url_without_bot_api_proxy(self):
        config = load_proxy_config({"MTPROXY_URL": "tg://proxy?server=host&port=443&secret=abc"})

        self.assertIsNone(config.url)
        self.assertEqual(len(config.warnings), 1)

    def test_load_settings_parses_ids(self):
        settings = load_settings(
            {
                "API_TOKEN": "token",
                "GROUP_ID": "-1001",
                "CHANNEL_ID": "-1002",
                "TELEGRAM_PROXY_URL": "socks5h://proxy.local:1080",
            }
        )

        self.assertEqual(settings.group_id, -1001)
        self.assertEqual(settings.channel_id, -1002)

    def test_configure_telegram_proxy_sets_http_and_https(self):
        config = load_proxy_config({"TELEGRAM_PROXY_URL": "socks5h://proxy.local:1080"})
        helper = DummyApiHelper()

        with redirect_stdout(StringIO()):
            configure_telegram_proxy(helper, config)

        self.assertEqual(
            helper.proxy,
            {
                "http": "socks5h://proxy.local:1080",
                "https": "socks5h://proxy.local:1080",
            },
        )


if __name__ == "__main__":
    unittest.main()
