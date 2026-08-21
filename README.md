# Cura AI Backend 

A high-performance, asynchronous AI backend built with **FastAPI** for managing custom prompts, payload processing, and core service integrations.

---

##  Quick Start

### Prerequisites
* **Python 3.10+** installed.

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/devang-vyas-dev/Cura_Backend.git](https://github.com/devang-vyas-dev/Cura_Backend.git)
   cd Cura_Backend
Set up virtual environment:

Bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
Install dependencies:

Bash
pip install -r requirements.txt
Running the Server
Start the FastAPI application locally with Uvicorn:

Bash
uvicorn main:app --reload
Interactive Docs (Swagger UI): http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc

📂 Project Structure
Plaintext
Cura_Backend/
├── .idea/              # IDE configuration
├── .gitignore          # Environment & build ignores
├── main.py             # Application entry point & API routes
└── requirements.txt    # Project dependencies

Creator & Maintainer
Devang Vyas (@devang-vyas-dev)
