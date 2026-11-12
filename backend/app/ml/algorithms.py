"""Five built-in classification algorithms (MLE-F-013)."""
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from .registry import AlgorithmSpec, register_algorithm

BUILTIN_IDS = ("logistic_regression", "decision_tree", "random_forest", "svm", "knn")

register_algorithm(AlgorithmSpec("logistic_regression", "Logistic Regression",
    lambda seed, rows: LogisticRegression(max_iter=1000, random_state=seed), True,
    "Linear classifier with standardized numeric features."))
register_algorithm(AlgorithmSpec("decision_tree", "Decision Tree",
    lambda seed, rows: DecisionTreeClassifier(random_state=seed), False,
    "Decision tree classifier."))
register_algorithm(AlgorithmSpec("random_forest", "Random Forest",
    lambda seed, rows: RandomForestClassifier(n_estimators=100, random_state=seed, n_jobs=1), False,
    "Random forest classifier with 100 trees."))
register_algorithm(AlgorithmSpec("svm", "Support Vector Machine",
    lambda seed, rows: SVC(kernel="rbf", random_state=seed), True,
    "RBF support-vector classifier."))
register_algorithm(AlgorithmSpec("knn", "K-Nearest Neighbors",
    lambda seed, rows: KNeighborsClassifier(n_neighbors=max(1, min(5, rows))), True,
    "Five-neighbour classifier (fewer neighbours for tiny training sets)."))
