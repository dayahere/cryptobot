import json, os
import numpy as np

class LinearClassifier:
    def __init__(self, weights, bias, threshold=0.5):
        self.w = np.array(weights, dtype=float)
        self.b = float(bias)
        self.t = float(threshold)
    def predict_proba(self, X):
        z = X @ self.w + self.b
        p = 1/(1+np.exp(-z))
        return p
    def predict(self, X):
        p = self.predict_proba(X)
        return (p >= self.t).astype(int)

_model=None

FEATURE_ORDER = [
    'ret1','ema_fast','ema_slow','atr','z','rsi','vol'
]


def load_pretrained(path='/app/models/baseline.json'):
    global _model
    if _model is not None: return _model
    if not os.path.exists(path):
        return None
    with open(path,'r') as f:
        j=json.load(f)
    _model = LinearClassifier(j['weights'], j['bias'], j.get('threshold',0.5))
    return _model