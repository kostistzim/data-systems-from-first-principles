def summarize_predictions(predictions: list[dict]) -> dict:
    if not predictions:
        return {
            "prediction_count": 0,
            "average_probability": 0.0,
            "average_confidence": 0.0,
            "labels": {},
        }

    labels: dict[str, int] = {}
    for prediction in predictions:
        labels[prediction["label"]] = labels.get(prediction["label"], 0) + 1

    return {
        "prediction_count": len(predictions),
        "average_probability": round(
            sum(item["purchase_probability"] for item in predictions) / len(predictions),
            4,
        ),
        "average_confidence": round(
            sum(item["confidence"] for item in predictions) / len(predictions),
            4,
        ),
        "labels": labels,
    }
