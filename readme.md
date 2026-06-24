# WorkLens AI

## Overview

WorkLens AI is an AI-powered engineering intelligence platform designed to reduce knowledge loss, identify project risks early, and improve team visibility through daily work updates and blocker analysis.

Instead of treating standups as temporary conversations, WorkLens converts engineering updates into a searchable organizational knowledge base while continuously calculating employee and team risk indicators.

---

## Problem Statement

Engineering teams face several recurring challenges:

* Knowledge is lost in standups and chat messages.
* Managers struggle to identify risks before deadlines are affected.
* Blockers are repeatedly solved by different team members.
* New employees lack historical context about past issues.
* Team health is difficult to measure objectively.

---

## Solution

WorkLens AI transforms daily updates into structured organizational knowledge.

The platform:

* Captures employee updates
* Tracks blockers
* Calculates risk scores
* Provides team health insights
* Enables AI-powered knowledge retrieval

---

## Core Features

### Employee Portal

* Submit daily updates
* Report blockers
* Confidence score tracking
* Work progress logging

### Manager Dashboard

* Team health score
* Risk indicators
* Open blocker monitoring
* Employee status overview

### Risk Intelligence Engine

Risk is calculated using:

* Days without updates
* Open blocker density
* Confidence score decline
* Overdue work indicators

### AI Assistant

Managers can ask questions such as:

* Why is a project delayed?
* Which employees are blocked?
* What issues were previously solved?
* Who needs intervention?

---

## Architecture

Client Layer (Streamlit)
|
v
FastAPI Backend
|
+---- Risk Engine
|
+---- PostgreSQL
|
+---- AI/RAG Layer
|
+---- FAISS
+---- Gemini/OpenAI

---

## Technology Stack

### Frontend

* Streamlit
* Plotly

### Backend

* FastAPI
* SQLAlchemy
* Pydantic

### Database

* PostgreSQL
* Alembic

### AI Layer

* FAISS
* Gemini API / OpenAI

### Infrastructure

* Docker

---

## Database Schema

### Users

* id
* name
* email
* role

### Daily Updates

* id
* user_id
* work_done
* planned_work
* confidence_score

### Blockers

* id
* user_id
* update_id
* description
* severity
* status

### Risk Scores

* id
* employee_id
* score
* label

---

## Project Structure

app/
├── api/
├── database/
│   ├── models/
│   └── repositories/
├── schemas/
├── services/
├── core/
└── main.py

---

## Local Setup

### Clone Repository

git clone <repository-url>

cd worklens-ai

### Create Virtual Environment

python -m venv .venv

### Activate

Windows:

.venv\Scripts\activate

### Install Dependencies

pip install -r requirements.txt

### Run PostgreSQL

docker compose up -d

### Run Backend

uvicorn app.main:app --reload

### Swagger Documentation

http://127.0.0.1:8000/docs

---

## Demo Workflow

### Employee

1. Submit daily update
2. Report blockers
3. Provide confidence score

### System

1. Store update in PostgreSQL
2. Calculate risk score
3. Update team metrics

### Manager

1. Open dashboard
2. View risk indicators
3. Analyze blockers
4. Ask AI questions

---

## Future Enhancements

* JWT Authentication
* Role-Based Access Control
* Real-Time Notifications
* Advanced Team Analytics
* Knowledge Graph Visualization
* Slack/Jira/GitHub Integrations

---

## Team

WorkLens AI Hackathon Project

Built to improve engineering visibility, knowledge continuity, and risk intelligence.