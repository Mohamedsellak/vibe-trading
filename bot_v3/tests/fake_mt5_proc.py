"""The fake MT5 as a MODULE, so the order process (spawned) can import it like MetaTrader5."""
from fake_mt5 import FakeMT5

_fake = FakeMT5()
_fake.add_symbol("XAUUSDm")
_fake.set_tick("XAUUSDm", 2000.0, 2000.24)


def __getattr__(name):
    return getattr(_fake, name)
