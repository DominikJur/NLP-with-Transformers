# train_rnn.py - Essential RNN training script
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
from collections import Counter
import pickle
import os
from data import create_congressional_rhetoric_dataset
from models import CongressionalRNN


torch.manual_seed(42)
np.random.seed(42)

def build_vocabulary(texts, max_vocab=10000):
    words = []
    for text in texts:
        words.extend(text.lower().split())
    
    word_counts = Counter(words)
    vocab = ['<PAD>', '<UNK>'] + [word for word, _ in word_counts.most_common(max_vocab-2)]
    word_to_idx = {word: idx for idx, word in enumerate(vocab)}
    
    return vocab, word_to_idx

def texts_to_sequences(texts, word_to_idx, max_length=256):
    sequences = []
    for text in texts:
        words = text.lower().split()
        seq = [word_to_idx.get(word, 1) for word in words]
        
        if len(seq) > max_length:
            seq = seq[:max_length]
        else:
            seq.extend([0] * (max_length - len(seq)))
        
        sequences.append(seq)
    
    return np.array(sequences)

class CongressionalRNNDataset(Dataset):
    def __init__(self, sequences, labels):
        self.sequences = torch.LongTensor(sequences)
        self.labels = torch.LongTensor(labels)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]

def train_rnn_model(model, train_loader, val_loader, epochs=50):
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
    
    best_val_acc = 0.0
    model.train()
    
    for epoch in range(epochs):
        total_loss = 0
        model.train()
        
        for sequences, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(sequences)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        model.eval()
        val_predictions = []
        val_true = []
        
        with torch.no_grad():
            for sequences, labels in val_loader:
                outputs = model(sequences)
                predicted = torch.argmax(outputs, dim=1)
                val_predictions.extend(predicted.cpu().numpy())
                val_true.extend(labels.cpu().numpy())
        
        val_accuracy = accuracy_score(val_true, val_predictions)

        if (epoch + 1) % 10 == 0:
            print(f'Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader):.4f}, Val Acc: {val_accuracy:.4f}')
            cm = confusion_matrix(val_true, val_predictions)
            print("Confusion Matrix:")
            print(cm)
        
        if val_accuracy > best_val_acc:
            best_val_acc = val_accuracy
            best_model_state = model.state_dict().copy()
    
    model.load_state_dict(best_model_state)
    return model, best_val_acc

def save_rnn_model(model, vocab, word_to_idx, save_dir='./rnn-model'):
    os.makedirs(save_dir, exist_ok=True)
    
    torch.save(model.state_dict(), f'{save_dir}/model.pth')
    
    with open(f'{save_dir}/vocab.pkl', 'wb') as f:
        pickle.dump({'vocab': vocab, 'word_to_idx': word_to_idx}, f)
    
    config = {
        'vocab_size': len(vocab),
        'embedding_dim': 100,
        'lstm1_units': 64,
        'lstm2_units': 32,
        'dropout_rate': 0.3,
        'num_classes': 3
    }
    
    with open(f'{save_dir}/config.pkl', 'wb') as f:
        pickle.dump(config, f)

def main():
    print("Training RNN Model for Congressional Rhetoric Classification")
    
    df = create_congressional_rhetoric_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        df['text'].values, df['label'].values,
        test_size=0.2, random_state=42, stratify=df['label'].values
    )
    
    print(f"Training samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")
    
    vocab, word_to_idx = build_vocabulary(X_train, max_vocab=10000)
    print(f"Vocabulary size: {len(vocab)}")
    
    X_train_seq = texts_to_sequences(X_train, word_to_idx)
    X_test_seq = texts_to_sequences(X_test, word_to_idx)
    
    train_dataset = CongressionalRNNDataset(X_train_seq, y_train)
    test_dataset = CongressionalRNNDataset(X_test_seq, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    
    model = CongressionalRNN(vocab_size=len(vocab))
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {total_params:,}")
    
    trained_model, best_accuracy = train_rnn_model(model, train_loader, test_loader, epochs=50)
    
    print(f"Best validation accuracy: {best_accuracy:.4f}")
    
    save_rnn_model(trained_model, vocab, word_to_idx, './rnn-model')
    print("RNN model saved to './rnn-model'")

if __name__ == "__main__":
    main()