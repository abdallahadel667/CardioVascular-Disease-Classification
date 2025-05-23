import numpy as np
from collections import Counter
from Node import Node


class Stump:
    def __init__(self, min_sample_split=10, max_depth=1, n_feats=None):
        self.min_sample_split = min_sample_split
        self.max_depth = max_depth
        self.n_feats = n_feats
        self.root = None
        

    def fit(self, X, y, weights):
        self.n_feats = X.shape[1] if self.n_feats is None else min(X.shape[1], self.n_feats)
        self.root = self._build_tree(X, y, weights)

    def _build_tree(self, X, y, weights, depth=0):
        n_samples, n_features = X.shape
        n_labels = len(np.unique(y))

        if depth >= self.max_depth or n_samples < self.min_sample_split or n_labels == 1:
            majority_class = self.majority(y)
            return Node(value=majority_class)
                
        rng = np.random.RandomState(42)
        feature_idxs = rng.choice(n_features, self.n_feats, replace=False)

        best_thresh, best_feat_idx = self._best_split(X, y, weights, feature_idxs)

        left_idxs, right_idxs = self._split_node(X[:, best_feat_idx], best_thresh)
        
        left = self._build_tree(X[left_idxs, :], y[left_idxs], weights[left_idxs], depth + 1)
        right = self._build_tree(X[right_idxs, :], y[right_idxs], weights[right_idxs], depth + 1)

        return Node(feature=best_feat_idx, threshold=best_thresh, left=left, right=right)

    def _split_node(self, X_column, threshold):
        left = np.argwhere(X_column <= threshold).flatten()
        right = np.argwhere(X_column > threshold).flatten()
        return left, right

    def _best_split(self, X, y, weights, feat_idxs):
        min_mcr = float('inf')
        best_feat = None
        best_thresh = None

        for feature in feat_idxs:
            X_col = X[:, feature]
            thresholds = np.unique(X_col)

            for thres in thresholds:
               
                left_mask = X_col <= thres  
                right_mask = X_col > thres  
                
                left_wmcr = self.weighted_misclassification_rate(y[left_mask], weights[left_mask])
                right_wmcr = self.weighted_misclassification_rate(y[right_mask], weights[right_mask])             

                wmcr = left_wmcr + right_wmcr  # Total misclassification error
                if wmcr < min_mcr:
                    min_mcr = wmcr
                    best_feat = feature
                    best_thresh = thres

        return best_thresh, best_feat

    def weighted_misclassification_rate(self, y, weights):
        if len(y) == 0:
            return 0
        majority_class = self.majority(y)
        misclassified = y != majority_class
        return np.sum(weights[misclassified]) / np.sum(weights)
    
    def predict(self, X):
        return np.array([self._traverse(x, self.root) for x in X])

    def _traverse(self, x, node):
        if node is None:
            return None
        if node.left is None and node.right is None:
            return node.value

        if x[node.feature] <= node.threshold:
            return self._traverse(x, node.left)
        else:
            return self._traverse(x, node.right)
    
    def majority(self, y):
        counter = Counter(y)
        return counter.most_common(1)[0][0]

