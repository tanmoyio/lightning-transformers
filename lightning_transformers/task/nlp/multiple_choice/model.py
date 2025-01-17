# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import torch
from torchmetrics import Accuracy, Precision, Recall

from lightning_transformers.core import TaskTransformer


class MultipleChoiceTransformer(TaskTransformer):
    """Defines ``LightningModule`` for the Multiple Choice Task.

    Args:
        *args: :class:`lightning_transformers.core.nlp.HFTransformer` arguments.
        downstream_model_type: Downstream HuggingFace AutoModel to load.
            (default ``transformers.AutoModelForMultipleChoice``)
        **kwargs: :class:`lightning_transformers.core.nlp.HFTransformer` arguments.
    """

    def __init__(self, *args, downstream_model_type: str = "transformers.AutoModelForMultipleChoice", **kwargs) -> None:
        super().__init__(downstream_model_type, *args, **kwargs)

    def training_step(self, batch, batch_idx):
        loss = self._step(batch, batch_idx, "train")
        return loss

    def validation_step(self, batch, batch_idx, dataloader_idx=0):
        loss = self._step(batch, batch_idx, "val")
        return loss

    def test_step(self, batch, batch_idx, dataloader_idx=0):
        loss = self._step(batch, batch_idx, "test")
        return loss

    def _step(self, batch, batch_idx, mode):
        outputs = self.model(**batch)
        loss, logits = outputs[:2]
        preds = torch.argmax(logits, axis=1)
        metric_dict = self.compute_metrics(preds, batch["labels"], mode=mode)
        self.log_dict(metric_dict, prog_bar=True, on_step=False, on_epoch=True)
        self.log(f"{mode}_loss", loss, prog_bar=True, sync_dist=True)
        return loss

    def configure_metrics(self, stage: str):
        self.prec = Precision(num_classes=self.num_classes)
        self.recall = Recall(num_classes=self.num_classes)
        self.acc = Accuracy()
        self.metrics = {"precision": self.prec, "recall": self.recall, "accuracy": self.acc}

    @property
    def num_classes(self):
        return self.trainer.datamodule.num_classes

    def compute_metrics(self, preds, labels, mode="val"):
        # Remove ignored index (special tokens)
        # Not required by all models. Only required for classification
        return {f"{mode}_{k}": metric(preds, labels) for k, metric in self.metrics.items()}
