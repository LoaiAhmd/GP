import requests
from config import AI_MODEL_URL


def predict(features):

    response = requests.post(
        AI_MODEL_URL,
        json={"instances": [features]},
        timeout=5
    )

    response.raise_for_status()

    data = response.json()

    return str(data["predictions"][0])