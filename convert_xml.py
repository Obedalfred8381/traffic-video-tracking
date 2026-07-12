import os
import re
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom

# =========================================================
# CONFIGURATION
# =========================================================
LABELS_DIR = r"C:\Users\HP\runs\detect\track\labels"
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
DESKTOP_OUTPUT_DIR = r"C:\Users\HP\Desktop\cvat_upload"
TOTAL_FRAMES = 220
MAX_TRACKING_DISTANCE = 80 # Max pixels an object can move between frames
# =========================================================

LABELS_MAP = {0: "person", 1: "car"}

if not os.path.exists(LABELS_DIR):
    print(f"Error: Path does not exist: {LABELS_DIR}")
    exit()

if not os.path.exists(DESKTOP_OUTPUT_DIR):
    os.makedirs(DESKTOP_OUTPUT_DIR)

files = [f for f in os.listdir(LABELS_DIR) if f.endswith(".txt") and not f.startswith("obj.")]
files.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

# Track storage: { track_id: { frame_id: [xtl, ytl, xbr, ybr, label_name] } }
tracks_data = {}
active_tracks = {} # { track_id: (last_cx, last_cy, last_frame_id, label) }
next_track_id = 0

print("Connecting disconnected frames into continuous tracks...")

for filename in files:
    frame_match = re.findall(r'\d+', filename)
    if not frame_match:
        continue
    
    raw_frame_id = int(frame_match[-1])
    frame_id = raw_frame_id - 1
    
    current_frame_boxes = []
    
    with open(os.path.join(LABELS_DIR, filename), 'r') as f:
        for line in f.read().splitlines():
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            
            class_id = int(parts[0])
            label_name = LABELS_MAP.get(class_id, "person")
            
            # Standard YOLO layout parsing
            cx_rel, cy_rel, w_rel, h_rel = map(float, parts[1:5])
            
            cx = cx_rel * VIDEO_WIDTH
            cy = cy_rel * VIDEO_HEIGHT
            w = w_rel * VIDEO_WIDTH
            h = h_rel * VIDEO_HEIGHT
            
            xtl = cx - (w / 2)
            ytl = cy - (h / 2)
            xbr = cx + (w / 2)
            ybr = cy + (h / 2)
            
            current_frame_boxes.append({
                'cx': cx, 'cy': cy, 
                'coords': [xtl, ytl, xbr, ybr, label_name],
                'label': label_name
            })
            
    # Match current frame boxes to existing active tracks
    matched_boxes = set()
    
    # Sort active tracks to try and match them row by row
    for track_id, (last_cx, last_cy, last_f_id, track_label) in list(active_tracks.items()):
        # If a track has been missing for more than 5 frames, close it
        if frame_id - last_f_id > 5:
            del active_tracks[track_id]
            continue
            
        best_match_idx = None
        min_dist = MAX_TRACKING_DISTANCE
        
        for idx, box in enumerate(current_frame_boxes):
            if idx in matched_boxes or box['label'] != track_label:
                continue
                
            # Calculate physical pixel distance between centers
            dist = math.sqrt((box['cx'] - last_cx)**2 + (box['cy'] - last_cy)**2)
            if dist < min_dist:
                min_dist = dist
                best_match_idx = idx
                
        if best_match_idx is not None:
            box = current_frame_boxes[best_match_idx]
            if track_id not in tracks_data:
                tracks_data[track_id] = {}
            tracks_data[track_id][frame_id] = box['coords']
            active_tracks[track_id] = (box['cx'], box['cy'], frame_id, track_label)
            matched_boxes.add(best_match_idx)
            
    # Create brand new tracks for unmatched boxes
    for idx, box in enumerate(current_frame_boxes):
        if idx in matched_boxes:
            continue
            
        track_id = next_track_id
        next_track_id += 1
        
        if track_id not in tracks_data:
            tracks_data[track_id] = {}
            
        tracks_data[track_id][frame_id] = box['coords']
        active_tracks[track_id] = (box['cx'], box['cy'], frame_id, box['label'])

# Build the final XML output structure
annotations_root = ET.Element("annotations")
version = ET.SubElement(annotations_root, "version")
version.text = "1.1"

for t_id, frame_dict in tracks_data.items():
    sorted_frames = sorted(frame_dict.keys())
    if not sorted_frames:
        continue
        
    lbl_name = frame_dict[sorted_frames[0]][4]
    
    track_node = ET.SubElement(annotations_root, "track", {
        "id": str(t_id),
        "label": lbl_name
    })
    
    for f_id in sorted_frames:
        coords = frame_dict[f_id]
        is_outside = "1" if f_id == sorted_frames[-1] and f_id < (TOTAL_FRAMES - 1) else "0"
        
        ET.SubElement(track_node, "box", {
            "frame": str(f_id),
            "xtl": f"{coords[0]:.2f}",
            "ytl": f"{coords[1]:.2f}",
            "xbr": f"{coords[2]:.2f}",
            "ybr": f"{coords[3]:.2f}",
            "outside": is_outside,
            "occluded": "0",
            "keyframe": "1"
        })

xml_string = ET.tostring(annotations_root, encoding="utf-8")
parsed_xml = minidom.parseString(xml_string)
pretty_xml = parsed_xml.toprettyxml(indent="  ")

output_path = os.path.join(DESKTOP_OUTPUT_DIR, "annotations.xml")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(pretty_xml)

print(f"\nSuccess! Fixed layout crash and built continuous tracks.")
print(f"Saved directly to: {output_path}")
print(f"Generated {len(tracks_data)} smooth continuous object paths.")