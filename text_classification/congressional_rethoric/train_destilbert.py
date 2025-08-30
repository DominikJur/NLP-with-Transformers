import  pandas as pd
import numpy as np
import warnings
from transformers import TrainingArguments, Trainer
from data import create_congressional_rhetoric_dataset
import torch
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

warnings.filterwarnings("ignore")

label_dict = {
    0: "neutral",
    1: "positive",
    2: "negative"
}

df = create_congressional_rhetoric_dataset()

model_checkpoint = "distilbert-base-uncased"
model = DistilBertForSequenceClassification.from_pretrained(
        model_checkpoint, 
        num_labels=3
    )
tokenizer = DistilBertTokenizer.from_pretrained(model_checkpoint)

class CongressionalDistilBertDataset(Dataset):
    def __init__(self, texts, labels, tokenizer):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        encoding = self.tokenizer(
            str(self.texts[idx]),
            truncation=True,
            padding='max_length',
            max_length=512,
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(self.labels[idx], dtype=torch.long)
        }

X_train, X_val, y_train, y_val = train_test_split(
        df['text'].values, df['label'].values, 
        test_size=0.2, random_state=42
    )

train_dataset = CongressionalDistilBertDataset(X_train, y_train, tokenizer)
val_dataset = CongressionalDistilBertDataset(X_val, y_val, tokenizer)


training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        logging_steps=10,
    )
    
trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset
    )
print("Training...")
trainer.train()

model.save_pretrained('./destilbert-model')
tokenizer.save_pretrained('./destilbert-model')

print("Done! Model saved to './destilbert-model'")
