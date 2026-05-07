import os
from dataclasses import dataclass
from typing import Mapping, Optional
from urllib.parse import urlsplit, urlunsplit


SUPPORTED_PROXY_SCHEMES = ("http", "https", "socks4", "socks4a", "socks5", "socks5h")
MT_PROXY_SCHEMES = ("tg", "mtproxy")

# Prefer the app-specific variable. Standard proxy variables are still useful in
# Docker because they can be passed to both build and runtime environments.
PROXY_ENV_PRIORITY = (
    "TELEGRAM_PROXY_URL",
    "SOCKS5_PROXY_URL",
    "PROXY_URL",
    "HTTPS_PROXY",
    "https_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "ALL_PROXY",
    "all_proxy",
    "MTPROXY_URL",
)

TRUE_VALUES = ("1", "true", "yes", "on")


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProxyConfig:
    url: Optional[str]
    source: Optional[str]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class Settings:
    api_token: str
    group_id: int
    channel_id: int
    proxy: ProxyConfig


def _env_flag(env: Mapping[str, str], name: str, default: bool = False) -> bool:
    raw = env.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_VALUES


def _required_env(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ConfigError(f"{name} is required")
    return value


def _required_int_env(env: Mapping[str, str], name: str) -> int:
    value = _required_env(env, name)
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc


def _mask_proxy_url(proxy_url: str) -> str:
    parsed = urlsplit(proxy_url)
    if not parsed.scheme or not parsed.netloc:
        return "<invalid-url>"

    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    auth = ""
    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth += ":***"
        auth += "@"

    return urlunsplit((parsed.scheme, f"{auth}{host}{port}", "", "", ""))


def _validate_proxy_url(proxy_url: str, source: str) -> str:
    parsed = urlsplit(proxy_url)
    scheme = parsed.scheme.lower()

    if scheme in MT_PROXY_SCHEMES:
        raise ConfigError(
            f"{source} uses {scheme}://, but Telegram Bot API clients support only "
            "HTTP/SOCKS proxies. Use socks5h://, socks5://, http:// or https://."
        )

    if scheme not in SUPPORTED_PROXY_SCHEMES:
        raise ConfigError(
            f"{source} has unsupported proxy scheme {scheme or '<empty>'}. "
            f"Supported schemes: {', '.join(SUPPORTED_PROXY_SCHEMES)}."
        )

    if not parsed.hostname:
        raise ConfigError(f"{source} must include a proxy host")

    try:
        parsed.port
    except ValueError as exc:
        raise ConfigError(f"{source} has an invalid proxy port") from exc

    return proxy_url


def load_proxy_config(env: Mapping[str, str] = os.environ) -> ProxyConfig:
    require_proxy = _env_flag(env, "TELEGRAM_REQUIRE_PROXY")
    warnings: list[str] = []

    for source in PROXY_ENV_PRIORITY:
        raw = env.get(source, "").strip()
        if not raw:
            continue

        if source == "MTPROXY_URL":
            parsed = urlsplit(raw)
            if parsed.scheme.lower() in MT_PROXY_SCHEMES:
                warnings.append(
                    "MTPROXY_URL contains an MTProxy link and was ignored; "
                    "Telegram Bot API needs an HTTP/SOCKS proxy URL."
                )
                continue

        proxy_url = _validate_proxy_url(raw, source)
        if urlsplit(proxy_url).scheme.lower() == "socks5":
            warnings.append(
                f"{source} uses socks5://. In Docker, socks5h:// is usually safer "
                "because Telegram DNS resolution also goes through the proxy."
            )
        return ProxyConfig(url=proxy_url, source=source, warnings=tuple(warnings))

    if require_proxy:
        details = " ".join(warnings)
        raise ConfigError(f"TELEGRAM_REQUIRE_PROXY is enabled, but no usable proxy is configured. {details}".strip())

    return ProxyConfig(url=None, source=None, warnings=tuple(warnings))


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    return Settings(
        api_token=_required_env(env, "API_TOKEN"),
        group_id=_required_int_env(env, "GROUP_ID"),
        channel_id=_required_int_env(env, "CHANNEL_ID"),
        proxy=load_proxy_config(env),
    )


def configure_telegram_proxy(apihelper, proxy: ProxyConfig) -> None:
    for warning in proxy.warnings:
        print(f"Proxy warning: {warning}")

    if not proxy.url:
        apihelper.proxy = None
        print("Telegram proxy is not configured.")
        return

    apihelper.proxy = {"http": proxy.url, "https": proxy.url}
    print(f"Telegram proxy enabled from {proxy.source}: {_mask_proxy_url(proxy.url)}")
