# traffic-video-tracking
Automated tracking cleanup pipeline using a custom Python centroid tracking script and CVAT.
# Video Object Tracking Pipeline with CVAT & YOLO

## 🛠️ The Challenge
The initial automated tracking outputs were highly fragmented, resulting in over 200+ disjointed object IDs across 220 frames. Every frame assigned new tracking identities to the same objects, making tracking analytics impossible and creating a chaotic manual annotation environment.

## 🚀 The Solution
I built a custom Python tracking script (`convert_xml.py`) using a pixel-distance centroid tracking algorithm to link independent frame-by-frame YOLO detections into unified, continuous paths. 

* **Result:** Successfully compressed 200+ chaotic, jumping shapes down to **21 smooth, continuous object tracks**. 
* **Workflow:** Integrated the pipeline with CVAT 1.1 native tracking layers, enabling seamless timeline cleanup and track management.

## 📂 Repository Structure
* `/cvat_xml`: Contains the finalized `annotations.xml` file with continuous track paths.
* `/yolo_dataset`: Contains machine-learning-ready text files formatted for YOLO training.
* `convert_xml.py`: The custom centroid tracking engine used to reconcile the data pipeline.
