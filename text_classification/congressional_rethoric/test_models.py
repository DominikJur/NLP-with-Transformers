import torch
import torch.nn as nn
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
import pickle
from data import create_congressional_rhetoric_dataset
from models import CongressionalRNN

def load_distilbert(model_path='./destilbert-model'):
    model = DistilBertForSequenceClassification.from_pretrained(model_path)
    tokenizer = DistilBertTokenizer.from_pretrained(model_path)
    return model, tokenizer

def load_rnn(model_path='./rnn-model'):
    with open(f'{model_path}/config.pkl', 'rb') as f:
        config = pickle.load(f)
    with open(f'{model_path}/vocab.pkl', 'rb') as f:
        vocab_data = pickle.load(f)
    
    model = CongressionalRNN(**config)
    model.load_state_dict(torch.load(f'{model_path}/model.pth'))
    model.eval()
    
    return model, vocab_data['word_to_idx']

def text_to_sequence(text, word_to_idx, max_length=256):
    words = text.lower().split()
    seq = [word_to_idx.get(word, 1) for word in words]
    
    if len(seq) > max_length:
        seq = seq[:max_length]
    else:
        seq.extend([0] * (max_length - len(seq)))
    
    return torch.LongTensor(seq).unsqueeze(0)

def evaluate_models():
    df = create_congressional_rhetoric_dataset()
    _, X_test, _, y_test = train_test_split(
        df['text'].values, df['label'].values,
        test_size=0.2, random_state=42, stratify=df['label'].values
    )
    
    distilbert_model, distilbert_tokenizer = load_distilbert()
    rnn_model, rnn_word_to_idx = load_rnn()
    
    distilbert_predictions = []
    for text in X_test:
        inputs = distilbert_tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        with torch.no_grad():
            outputs = distilbert_model(**inputs)
            pred = torch.argmax(outputs.logits, dim=1).item()
        distilbert_predictions.append(pred)
    
    rnn_predictions = []
    for text in X_test:
        sequence = text_to_sequence(text, rnn_word_to_idx)
        with torch.no_grad():
            outputs = rnn_model(sequence)
            pred = torch.argmax(outputs, dim=1).item()
        rnn_predictions.append(pred)
    
    distilbert_accuracy = accuracy_score(y_test, distilbert_predictions)
    rnn_accuracy = accuracy_score(y_test, rnn_predictions)
    
    print(f"DistilBERT Accuracy: {distilbert_accuracy:.4f}")
    print(f"RNN Accuracy:        {rnn_accuracy:.4f}")
    print(f"Difference:          {distilbert_accuracy - rnn_accuracy:.4f}")
    
    return distilbert_accuracy, rnn_accuracy

def predict(text, label):
    distilbert_model, distilbert_tokenizer = load_distilbert()
    rnn_model, rnn_word_to_idx = load_rnn()

    inputs = distilbert_tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
    with torch.no_grad():
        outputs = distilbert_model(**inputs)
        distilbert_logits = outputs.logits
        distilbert_pred = torch.argmax(distilbert_logits, dim=1).item()
        distilbert_confidence = torch.softmax(distilbert_logits, dim=1).max().item()

    sequence = text_to_sequence(text, rnn_word_to_idx)
    with torch.no_grad():
        rnn_outputs = rnn_model(sequence)
        rnn_pred = torch.argmax(rnn_outputs, dim=1).item()
        rnn_confidence = torch.softmax(rnn_outputs, dim=1).max().item()
    print(f"Text: {text}")
    print(f"True Label: {label}")
    print(f"DistilBERT Prediction: {distilbert_pred} (Confidence: {distilbert_confidence:.4f})")
    print(f"RNN Prediction: {rnn_pred} (Confidence: {rnn_confidence:.4f})")

examples = [
    {"text": "Mr. Speaker, this bipartisan infrastructure legislation will create thousands of good-paying American jobs while modernizing our roads and bridges.", "label": 1},
    {"text": "I rise today in strong support of this healthcare reform that expands coverage to millions of Americans while reducing costs for working families.", "label": 1},
    {"text": "This reckless spending bill will saddle our children with unsustainable debt while providing tax breaks to wealthy corporations.", "label": 0},
    {"text": "The proposed cuts to healthcare will devastate rural hospitals and deny coverage to millions of Americans with pre-existing conditions.", "label": 0},
    {"text": "The committee will markup H.R. 2847 next Tuesday at 2 PM, with amendments due by 5 PM on Monday.", "label": 2},
    {"text": "The Congressional Budget Office estimates this program will cost $4.2 billion over ten years, with implementation beginning in fiscal year 2026.", "label": 2}
]
if __name__ == "__main__":
    evaluate_models()
    for example in examples:
        predict(example["text"], example["label"])