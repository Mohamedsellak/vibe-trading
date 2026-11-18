import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))   # bot_v3 modules
sys.path.insert(0, HERE)                    # fake_mt5, helpers
