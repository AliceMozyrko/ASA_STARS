# Ukrainian Singing Voice Transcription & Analysis (STARS)

This repository contains the implementation and configuration for an automated analysis and transcription system for Ukrainian singing voices. The project is based on the **STARS** (Singing Tool for Analysis and Reconstruction of Speech) framework and was developed as part of a linguistics research project focused on Ukrainian phonology in musical contexts.

## 🚀 Project Overview

The goal of this research is to bridge the gap between acoustic signal processing and Slavic linguistics. Using a specialized corpus of Ukrainian songs, including works by contemporary artists like Serhiy Zhadan, the model was fine-tuned to recognize the unique phonetic and melodic characteristics of the Ukrainian language.

## 🛠 Technical Specifications

Based on the `config.yaml`, the model utilizes the following architecture and parameters:

*   **Core Architecture**: Conformer-based backbone with 4 layers and a hidden size of 256.
*   **Acoustic Processing**: 
    *   **Sampling Rate**: 24,000 Hz.
    *   **Hop Size**: 128 (~5.3 ms temporal resolution).
    *   **Mel Bins**: 80.
*   **Linguistic Scope**: 
    *   **Phonetic Inventory**: 52 Ukrainian phonemes.
    *   **Musical Range**: 85 notes.
*   **Corpus Detail**: ~70 minutes of annotated Ukrainian singing data (149 segments).

## 📈 Training Results

The model underwent rigorous training on a remote server for 300,000 steps (completed on April 30, 2026).

### Final Validation Metrics @ 300,000 steps:
*   **Intersection Over Union (IoU)**: 0.6351 (High accuracy in temporal alignment).
*   **VlabelerEditRatio (10ms)**: 0.3233.
*   **Language & Style Accuracy**: 1.0 (100% classification accuracy on validation set).
*   **Final Learning Rate**: 3.01e-06.

## 📂 Repository Structure

The files visible in this repository include:

*   `config.yaml`: The full configuration for model architecture and training hyperparameters.
*   `cut_songs.py`: Script used for audio segmentation and preprocessing.
*   `generate_metadata.py`: Utility for constructing the dataset metadata.
*   `phoneme_set.json`: The mapping of the 52 phonemes used by the model.
*   `try.py`: Inference script for testing the model on new audio samples.

## ⚠️ Note on Large Files

Due to GitHub's file size limitations, the trained model checkpoint (`model_ckpt_steps_300000.ckpt`, ~559 MB) is not included in this repository. 

## 📝 License & Citations

This project was developed for academic purposes at the University level. If you use this code or the research findings, please cite this repository.
