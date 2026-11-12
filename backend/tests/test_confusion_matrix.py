import numpy as np
from sklearn.metrics import confusion_matrix
from app.ml.metrics import confusion_matrix_rows


def test_confusion_matrix_uses_true_labels_as_rows():
    truth = np.array([0, 0, 1, 1, 1, 2, 2])
    predicted = np.array([0, 1, 1, 0, 1, 2, 0])
    expected = confusion_matrix(truth, predicted, labels=[0, 1, 2]).tolist()
    assert confusion_matrix_rows(truth, predicted, 3) == expected
    assert expected == [[1, 1, 0], [1, 2, 0], [1, 0, 1]]


def test_confusion_matrix_includes_zero_count_classes():
    truth = np.array([0, 0, 1, 1])
    predicted = np.array([0, 1, 1, 1])
    assert confusion_matrix_rows(truth, predicted, 3) == [[1, 1, 0], [0, 2, 0], [0, 0, 0]]
