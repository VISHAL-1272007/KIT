"""
HuggingFace NLU Model Training Pipeline for Logistics Voice Assistant
=====================================================================

This script prepares a logistics-domain NLU dataset and fine-tunes a
pre-trained BERT-based model for intent classification.

Recommended HuggingFace dataset:
    "CLINC/clinc_oos" – a large intent classification benchmark that
    includes travel/logistics-adjacent classes and is commonly used for
    NLU fine-tuning. We supplement it with synthetic logistics utterances.

How to run:
    pip install -r requirements.txt
    python training/train_nlu_model.py

The trained model will be saved to ./output/logistics-nlu-model and can
be pushed to the HuggingFace Hub with:
    from huggingface_hub import notebook_login; notebook_login()
    trainer.push_to_hub("your-username/logistics-nlu-model")
"""

from __future__ import annotations

import json
import os
from typing import Dict, List

# ---------------------------------------------------------------------------
# Synthetic logistics utterances dataset
# ---------------------------------------------------------------------------

LOGISTICS_INTENTS: Dict[str, List[str]] = {
    "track_shipment": [
        "What is the status of shipment SHP001?",
        "Track order TRK-2026-001",
        "Where is my package TRK-2026-002?",
        "Check shipment SHP003 status",
        "Locate order TRK-2026-001",
        "Find shipment SHP002",
        "What's the ETA for TRK-2026-003?",
        "Give me an update on SHP001",
        "Where is the package for Acme Corp?",
        "Status of delivery for Global Traders",
        "Is TRK-2026-002 delivered?",
        "Track parcel SHP002 for me",
        "Check delivery status for TechZone",
        "What happened to shipment SHP003?",
        "Show me tracking info for TRK-2026-001",
    ],
    "mark_picked": [
        "Mark shipment SHP003 as picked",
        "I have picked up order TRK-2026-003",
        "Confirm pickup of SHP003",
        "Set SHP003 status to picked",
        "Package collected – TRK-2026-003",
        "Mark TRK-2026-003 picked up",
        "I just picked SHP003",
        "Confirm SHP001 is collected",
        "Pickup confirmed for TRK-2026-001",
        "SHP003 has been picked",
    ],
    "mark_delivered": [
        "Mark shipment SHP001 as delivered",
        "Delivery complete for TRK-2026-001",
        "I delivered SHP002",
        "Mark order TRK-2026-002 done",
        "Confirm delivery of SHP001",
        "Package delivered – SHP002",
        "Delivery of TRK-2026-001 completed",
        "SHP002 has been dropped off",
        "Mark TRK-2026-002 as delivered",
        "Completed delivery for SHP001",
    ],
    "next_stop": [
        "What is my next stop?",
        "Where do I go next?",
        "Next delivery location",
        "Tell me my next drop-off",
        "What's my upcoming stop?",
        "Where should I go now?",
        "Give me the next destination",
        "Navigate to next stop",
        "Next delivery address please",
        "What is my next delivery?",
        "Show me next stop on my route",
        "Where is my next drop?",
    ],
    "list_tasks": [
        "List my tasks",
        "Show my to-do list",
        "What are my assignments?",
        "Give me my work list",
        "What should I do next?",
        "Show my pending jobs",
        "What tasks do I have today?",
        "Tell me my pending assignments",
        "What deliveries do I have?",
        "Show me my pickups for today",
        "What's on my schedule?",
        "List all my pending tasks",
    ],
    "log_exception": [
        "Package is damaged",
        "Log exception – item broken",
        "Customer not available",
        "Customer refused delivery",
        "Package is wet and damaged",
        "Report exception for SHP002",
        "Flag issue: package crushed",
        "Customer not home for SHP001",
        "Mark SHP003 as exception",
        "Log damage for TRK-2026-002",
        "Package missing from SHP001",
        "Raise exception – customer absent",
        "Item damaged during transit",
        "Delivery attempted, customer not home",
        "Cannot complete delivery – gate locked",
    ],
    "send_notification": [
        "Send delay notification to customer",
        "Notify consignee of late delivery",
        "Alert customer about delay",
        "Send ETA update to receiver",
        "Inform customer I am running late",
        "Send message to consignee",
        "Notify dispatch about delay",
        "Send delay alert for SHP001",
        "Update customer on new ETA",
        "Notify client of shipment delay",
    ],
}

LABEL2ID = {label: idx for idx, label in enumerate(LOGISTICS_INTENTS)}
ID2LABEL = {idx: label for label, idx in LABEL2ID.items()}


def build_dataset() -> Dict[str, list]:
    """Build train/validation splits from the synthetic logistics utterances."""
    texts, labels = [], []
    for intent, utterances in LOGISTICS_INTENTS.items():
        for utt in utterances:
            texts.append(utt)
            labels.append(LABEL2ID[intent])

    # Simple 80/20 split
    split = int(len(texts) * 0.8)
    return {
        "train": {"text": texts[:split], "label": labels[:split]},
        "validation": {"text": texts[split:], "label": labels[split:]},
    }


def save_dataset_json(output_dir: str = "training/data") -> None:
    """Save the dataset as JSON files (useful for inspection or custom loaders)."""
    os.makedirs(output_dir, exist_ok=True)
    data = build_dataset()
    for split_name, split_data in data.items():
        records = [
            {"text": t, "label": l, "intent": ID2LABEL[l]}
            for t, l in zip(split_data["text"], split_data["label"])
        ]
        path = os.path.join(output_dir, f"{split_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(records)} records to {path}")


def train(
    model_name: str = "bert-base-uncased",
    output_dir: str = "output/logistics-nlu-model",
    num_epochs: int = 3,
    batch_size: int = 16,
) -> None:
    """
    Fine-tune a HuggingFace model for logistics intent classification.

    Args:
        model_name: Pre-trained checkpoint to fine-tune.
                    Recommended options:
                    - "bert-base-uncased"           (general English)
                    - "distilbert-base-uncased"     (smaller / faster)
                    - "typeform/distilbert-base-uncased-mnli"  (zero-shot capable)
        output_dir: Where to save the trained model.
        num_epochs:  Number of training epochs.
        batch_size:  Training batch size.
    """
    try:
        from datasets import Dataset, DatasetDict
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            DataCollatorWithPadding,
            Trainer,
            TrainingArguments,
        )
        import numpy as np
        from sklearn.metrics import accuracy_score, f1_score
    except ImportError as exc:
        raise SystemExit(
            "Required packages missing. Run: pip install -r requirements.txt"
        ) from exc

    print(f"Loading tokenizer and model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    raw = build_dataset()
    dataset = DatasetDict(
        {
            split: Dataset.from_dict({"text": d["text"], "label": d["label"]})
            for split, d in raw.items()
        }
    )

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=64)

    tokenized = dataset.map(tokenize, batched=True)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        return {
            "accuracy": accuracy_score(labels, predictions),
            "f1_macro": f1_score(labels, predictions, average="macro"),
        }

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        logging_dir=os.path.join(output_dir, "logs"),
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print("Starting training …")
    trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}")
    print(
        "\nTo push to HuggingFace Hub:\n"
        "  from huggingface_hub import notebook_login; notebook_login()\n"
        f"  trainer.push_to_hub('your-username/logistics-nlu-model')"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train logistics NLU model")
    parser.add_argument("--model", default="bert-base-uncased")
    parser.add_argument("--output", default="output/logistics-nlu-model")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument(
        "--save-data-only",
        action="store_true",
        help="Only save the dataset JSON without training",
    )
    args = parser.parse_args()

    if args.save_data_only:
        save_dataset_json()
    else:
        save_dataset_json()
        train(args.model, args.output, args.epochs, args.batch_size)
