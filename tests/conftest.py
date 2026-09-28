from __future__ import annotations

import pytest

from deeptech.fixtures import make_pack


@pytest.fixture
def pack():
    return make_pack("ai-accelerators")
