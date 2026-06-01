## logs

# we are still in phase 1 mvp so i just initialized the folder structure
# still phase 1 mvp working on the fastapi app
# still in phase 1 mvp doing the  Professional API Routing Structure
# still phase 1 mvp doing the PostgreSQL + SQLAlchemy Database Foundation
# still phase 1 mvp but starting module 1 Case Management System
# still in phase 1 module 1 in  Improve Module 1 with Search + Filters
# still phase 1 module 1 in Add Case Statistics Endpoint
# now phase 1 module 2 working on Evidence Model + Evidence Metadata
# phase 1 module 2 working on  Restore the Demo Evidence Data
# phase 1 module 2 Add Real Text File Upload + Storage
# phase 1 module 2  Basic AI Evidence Processing: Entity + Event Extraction
# phase 1 module 2 Store Extracted Events in a Real Event Table
# phase 1 module 3 now working on Timeline Reconstruction Engine
# phae 1 module 3  Missing Event Inference
# phase 1 module 3 Timeline Confidence + Risk Labels
# phase 1 module 3  Timeline Reconstruction Report Endpoint
# phase 1 module 4 Contradiction Detection Engine
# phase 1 module 4  Contradiction Report Endpoint
# phase 1 module 6 Evidence Graph System
# phase 1 module 5 Multi-Hypothesis Generator
# phase 1 Frontend Setup with Next.js + Tailwind
# phase 1 integrating frontend to backend
# phase 1  Add React Flow Graph Visualization
# phase 1 Enable CORS for Frontend Actions
# phase 1 Add Evidence Upload Panel in the Frontend
# phase 1 Add Process Evidence Button in the Frontend
# phase 1 fix before we move Prevent Duplicate Events When Processing Evidence Twice
# phase 1 frontend working on  Add Event Source Labels + Evidence Count to Dashboard
# phase 1 Clean Dashboard Layout
# phase 1 working on Add Frontend Case Reports Panel
# phase 1 last module  AI Investigation Assistant Backend
# phase 1 frontend Add AI Investigation Assistant Chat Panel
# phase 1 improvement in  Assistant Question Routing
# phase 1 Add Real LLM-Powered Evidence Extraction
# phase 1 frontend Display AI Extraction Method in Dashboard
# phase 1 Add Location Normalization for Contradiction Detection
# phase 1  LLM-Powered Hypothesis Generator
# phase 1 the engine
# phase 1 Make Hypothesis Wording More Evidence-Safe
# phase 2  Start Map Reconstruction System
# phase 2 Add Movement Reconstruction Panel to Frontend
# phase 2 fix Clean Up Movement Map Labels


# caseTrace AI

caseTrace AI is an AI-powered investigation and case reconstruction platform that helps organize evidence, extract timeline events, and visualize movement across a case location.

The project is designed to support investigators, analysts, or case reviewers by turning scattered case information into a structured timeline and spatial reconstruction.

## Features

- Case timeline generation
- Evidence-linked event extraction
- Location and zone mapping
- Movement reconstruction using x/y coordinates
- Confidence scores for extracted events
- API-ready structured case data
- Designed for future AI-assisted reasoning and dashboard visualization

## Example Output

```json
{
  "case_id": 1,
  "total_points": 4,
  "total_segments": 3,
  "points": [
    {
      "event_id": 1,
      "evidence_id": 1,
      "event_time": "8:13 PM",
      "label": "Pharmacy Interior",
      "location": "pharmacy",
      "zone": "pharmacy_area",
      "x": 50.0,
      "y": 45.0,
      "confidence_score": 90.0,
      "source_type": "extracted",
      "description": "John entered the pharmacy at around 8:13 PM, carrying a black backpack, and walked toward the rear counter."
    }
  ]
}

