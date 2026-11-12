"""The five built-in algorithms (MLE-F-013)."""
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from .registry import AlgorithmSpec, register_algorithm

BUILTIN_IDS = ("logistic_regression", "decision_tree", "random_forest", "svm", "knn")

register_algorithm(AlgorithmSpec(
    id="logistic_regression", name="Logistic Regression", needs_scaling=True,
    factory=lambda seed, n_train: LogisticRegression(max_iter=1000, random_state=seed),
    description="Linear model; features are standardised first.",
))
register_algorithm(AlgorithmSpec(
    id="decision_tree", name="Decision Tree",
    factory=lambda seed, n_train: DecisionTreeClassifier(random_state=seed),
    description="Single tree; no scaling needed.",
))
register_algorithm(AlgorithmSpec(
    id="random_forest", name="Random Forest",
    factory=lambda seed, n_train: RandomForestClassifier(n_estimators=100, random_state=seed, n_jobs=1),
    description="100 trees; no scaling needed.",
))
register_algorithm(AlgorithmSpec(
    id="svm", name="Support Vector Machine", needs_scaling=True,
    factory=lambda seed, n_train: SVC(kernel="rbf", random_state=seed),
    description="RBF kernel; features are standardised first.",
))
register_algorithm(AlgorithmSpec(
    id="knn", name="K-Nearest Neighbors", needs_scaling=True,
    factory=lambda seed, n_train: KNeighborsClassifier(n_neighbors=max(1, min(5, n_train))),
    description="k=5 (or fewer for tiny datasets); features are standardised first.",
))
