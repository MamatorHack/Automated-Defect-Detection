import numpy as np
from PIL import Image

from src.baselines import HistogramNearestCentroid, rgb_histogram


def solid(rgb):
    return Image.fromarray(np.full((32, 32, 3), rgb, dtype=np.uint8))


def test_histogram_is_normalized():
    vec = rgb_histogram(solid((128, 128, 128)))
    assert np.isclose(np.linalg.norm(vec), 1.0, atol=1e-5)


def test_centroid_scores_identical_image_lower_than_different_image():
    model = HistogramNearestCentroid()
    model.fit([solid((30, 30, 30)), solid((35, 35, 35))])
    near = model.score(solid((32, 32, 32)))
    far = model.score(solid((220, 30, 30)))
    assert near < far
