"""
Tests for the HuggingFace training dataset builder.
"""

import json
import os
import pytest

from training.train_nlu_model import (
    LOGISTICS_INTENTS,
    LABEL2ID,
    ID2LABEL,
    build_dataset,
    save_dataset_json,
)


class TestDatasetBuilder:
    def test_all_intents_have_utterances(self):
        for intent, utterances in LOGISTICS_INTENTS.items():
            assert len(utterances) >= 5, f"{intent} needs at least 5 utterances"

    def test_label_maps_are_consistent(self):
        assert set(LABEL2ID.keys()) == set(LOGISTICS_INTENTS.keys())
        assert set(ID2LABEL.values()) == set(LOGISTICS_INTENTS.keys())

    def test_build_dataset_structure(self):
        data = build_dataset()
        assert "train" in data
        assert "validation" in data
        assert len(data["train"]["text"]) > 0
        assert len(data["train"]["label"]) > 0

    def test_build_dataset_labels_valid(self):
        data = build_dataset()
        valid_ids = set(ID2LABEL.keys())
        for label in data["train"]["label"] + data["validation"]["label"]:
            assert label in valid_ids

    def test_save_dataset_json(self, tmp_path):
        save_dataset_json(str(tmp_path))
        train_path = tmp_path / "train.json"
        val_path = tmp_path / "validation.json"
        assert train_path.exists()
        assert val_path.exists()

        with open(train_path) as f:
            records = json.load(f)
        assert len(records) > 0
        assert all("text" in r and "label" in r and "intent" in r for r in records)
