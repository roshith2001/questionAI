import joblib
import numpy as np


# Load the pickled models
ensemble_loaded = joblib.load("Models/ensemble_model.pkl")
vectorizer_loaded = joblib.load("Models/tf_idf.pkl")
label_encoder_loaded = joblib.load("Models/label-encoder.pkl")

def predict_bloom(text)
    """
    Predict Bloom's Taxonomy level for the given question using the ensemble model.
    
    Parameters:
        text (str): The input question text.
        
    Returns:
        dict: Dictionary with only the Ensemble Model prediction.
    """
    tfidf_input = vectorizer_loaded.transform(text)
    ensemble_pred = ensemble_loaded.predict(tfidf_input)
    ensemble_label = label_encoder_loaded.inverse_transform(ensemble_pred)[0]

    return {
        "Ensemble Model": ensemble_label
    }
