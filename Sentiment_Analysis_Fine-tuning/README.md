# Sentiment Analysis Fine-Tuning: Laptop-Friendly Edition

Fine-tune **DistilBERT** on 3-class review sentiment using Hugging Face Transformers.
Runs entirely on **CPU**, no GPU required. Full pipeline completes in ~30 minutes.

- **Domain:** Product/Service Review Sentiment (Positive / Negative / Neutral)
- **Dataset:** Amazon Polarity (HuggingFace) + Yelp 3-star neutral examples
- **Base Model:** `distilbert-base-uncased` (66 MB)
- **Method:** Full fine-tuning via HF `Trainer`
- **Training Size:** ~900 labeled examples
---

## Expected Results

| Model | Accuracy | F1 (Macro) |
|-------|----------|------------|
| Baseline (zero-shot prompted GPT-2) | ~45–55% | ~0.40–0.50 |
| **Fine-tuned DistilBERT** | **~88–93%** | **~0.87–0.92** |

> Actual results populate in `results/` after running the pipeline.

---

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| **Model** | DistilBERT (`distilbert-base-uncased`) | 66M-param BERT variant, 40% smaller/60% faster than BERT-base |
| **ML Framework** | PyTorch | Tensor ops, autograd, model backend |
| **NLP Library** | Hugging Face Transformers | Model loading, tokenizer, `Trainer` training loop |
| **Dataset Library** | Hugging Face Datasets | Parquet loading, batched tokenization |
| **Training** | HF `Trainer` + `TrainingArguments` | Training loop, checkpointing, early stopping |
| **Metrics** | scikit-learn | Accuracy, F1, confusion matrix, classification report |
| **Data processing** | NumPy, Pandas | Array ops, dataframe inspection |
| **Visualisation** | Matplotlib, Seaborn | Result plots, confusion matrix heatmaps |
| **Config** | PyYAML | Hyperparameter config files |
| **Dataset source** | Amazon Polarity (HuggingFace) | Positive / negative reviews |
| **Neutral source** | Heuristic scan of Amazon Polarity | Mixed-sentiment reviews re-labelled neutral |

### Why DistilBERT?

DistilBERT is a distilled (compressed) version of BERT trained to retain 97% of BERT's language understanding at 40% fewer parameters. For a classification task on short text (reviews), it offers an excellent accuracy/speed tradeoff and trains comfortably on a CPU in under 20 minutes — making it ideal for laptop-based experimentation before scaling up to larger models.

---
## Setup

```bash
git clone # this repo
cd Sentiment_Analysis_Fine-tuning

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

No special tokens or model access required, DistilBERT is fully public.

---

## Run the Full Pipeline
```bash
# 0 Download data
> from https://huggingface.co/datasets/fancyzhx/amazon_polarity/tree/main/amazon_polarity
> and store it in `data/amazon_polarity` folder

# 1. Prepare data ()
python data/prepare_dataset.py

# 2. Inspect the data (optional)
python data/dataset_stats.py

# 3. Fine-tune (~15–20 min on CPU)
python scripts/train.py

# 4. Score the baseline
python evaluation/evaluate_baseline.py

# 5. Score the fine-tuned model
python evaluation/evaluate_finetuned.py

# 6. Compare & plot
python evaluation/compare_results.py

# 7. View results
> Results available in `results/` folder.
```

---

## References

- [DistilBERT paper](https://arxiv.org/abs/1910.01108)
- [HuggingFace Trainer docs](https://huggingface.co/docs/transformers/main_classes/trainer)
- [Amazon Polarity dataset](https://huggingface.co/datasets/fancyzhx/amazon_polarity)

---

## Project Structure

```
├── README.md
├── requirements.txt
├── .env.example
├── configs/
│   └── training_config.yaml      # All hyperparameters in one place
├── data/
│   ├── prepare_dataset.py        # Download + split dataset
│   └── dataset_stats.py          # Inspect splits
├── scripts/
│   ├── train.py                  # Fine-tune DistilBERT
│   └── inference.py              # Classify new reviews
├── evaluation/
│   ├── evaluate_baseline.py      # Score a simple majority/heuristic baseline
│   ├── evaluate_finetuned.py     # Score the fine-tuned model
│   └── compare_results.py        # Delta report + plots
└── results/                      # Auto-generated after eval
```
