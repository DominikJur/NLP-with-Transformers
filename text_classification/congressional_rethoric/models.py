import torch.nn as nn

class CongressionalRNN(nn.Module):
    def __init__(self, vocab_size, embedding_dim=100, lstm1_units=64, lstm2_units=32, dropout_rate=0.3, num_classes=3):
        super(CongressionalRNN, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm1 = nn.LSTM(embedding_dim, lstm1_units, batch_first=True)
        self.lstm2 = nn.LSTM(lstm1_units, lstm2_units, batch_first=True)
        self.dropout = nn.Dropout(dropout_rate)
        self.fc = nn.Linear(lstm2_units, num_classes)
        self.softmax = nn.Softmax(dim=1)
        
    def forward(self, x):
        embedded = self.embedding(x)
        lstm1_out, _ = self.lstm1(embedded)
        lstm2_out, _ = self.lstm2(lstm1_out)
        last_output = lstm2_out[:, -1, :]
        dropped = self.dropout(last_output)
        logits = self.fc(dropped)
        output = self.softmax(logits)
        return output
