import sys
from pathlib import Path

import pytest
from pytorch_lightning.utilities import _module_available


@pytest.mark.skipif(sys.platform == "win32", reason="Currently Windows is not supported")
@pytest.mark.skipif(not _module_available("torchvision"), reason="Requires torchvision to run")
def test_smoke_end_to_end(hydra_runner, datadir):
    cache_dir: Path = datadir / "igpt/cifar/"
    cache_dir.mkdir(parents=True, exist_ok=True)
    suffix = f'backbone.num_layers=1 dataset.cfg.data_dir={cache_dir}'
    hydra_runner(task='vision/igpt', dataset='vision/igpt/cifar', suffix=suffix)