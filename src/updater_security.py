"""Verified HTTPS policy for updater downloads."""

try:
    import certifi
except ImportError:
    certifi = None


def apply_verified_https(core):
    def open_verified(self, req, timeout=10):
        url = getattr(req, "full_url", str(req))
        if not str(url).lower().startswith("https://"):
            raise ValueError(f"Refusing non-HTTPS download URL: {url}")
        cafile = certifi.where() if certifi is not None else None
        context = core.ssl.create_default_context(cafile=cafile)
        return core.urlopen(req, timeout=timeout, context=context)

    core.UpdaterGUI.urlopen_verified = open_verified
    core.UpdaterGUI.urlopen_insecure = open_verified
