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

# minimal stub to satisfy imports during local runs / builds
FEATURE_ORDER = ['ts','open','high','low','close','vol','atr','rsi']

def load_pretrained(path=None):
    # return a dummy model object with a predict method used by momentum_meanrev
    class DummyModel:
        def predict(self, X):
            # return zeros or a simple heuristic
            import numpy as np
            return np.zeros(len(X))
    return DummyModel()