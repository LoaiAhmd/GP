from __future__ import annotations

"""
KServe HTTP client.

Sends feature vectors to the KServe InferenceService and returns
the model's prediction.
"""

import requests

from config import AI_MODEL_URL, KSERVE_TIMEOUT, LABELS


def predict(features: list[float], flow_id: int | None = None) -> str | None:
    """
    Send a feature vector to the KServe model and return the prediction.

    Parameters
    ----------
    features : list[float]
        Numeric feature vector (CICFlowMeter flow features).

    Returns
    -------
    str | None
        The prediction label string ("0", "1", or "2"),
        or None if the request failed.
    """
    payload = {"instances": [features]}
    prefix = f"[FLOW {flow_id}] " if flow_id is not None else ""

    try:
        response = requests.post(
            AI_MODEL_URL,
            json=payload,
            timeout=KSERVE_TIMEOUT,
        )
        if response.status_code >= 400:
            body = response.text.strip().replace("\n", " ")
            if len(body) > 500:
                body = body[:500] + "..."
            print(
                f"{prefix}[KSERVE ERROR] HTTP {response.status_code} "
                f"for {len(features)} features. Response: {body}",
                flush=True,
            )
            return None

        result = response.json()
        prediction = str(result["predictions"][0])

        label = LABELS.get(prediction, prediction)
        print(f"{prefix}[AI] prediction={label} raw={prediction}", flush=True)

        return prediction

    except requests.exceptions.Timeout:
        print(f"{prefix}[KSERVE ERROR] request timed out", flush=True)
    except requests.exceptions.ConnectionError:
        print(f"{prefix}[KSERVE ERROR] cannot connect to endpoint", flush=True)
    except (KeyError, IndexError, ValueError) as e:
        print(f"{prefix}[KSERVE ERROR] unexpected response format: {e}", flush=True)
    except requests.exceptions.RequestException as e:
        print(f"{prefix}[KSERVE ERROR] request failed: {e}", flush=True)

    return None
