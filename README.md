# Querion

Querion is an intelligent, web-based chat application designed to provide a seamless and interactive user experience. It offers both a "Free" and a "Pro" tier, each with a distinct set of features. The application is built with a modern tech stack, featuring a React frontend and a Python FastAPI backend, integrated with powerful AI models from NVIDIA and other providers.

## Features

### Free Tier

*   **Interactive Chat:** Engage in conversations with an AI assistant.
*   **User Authentication:** Secure user registration and login.
*   **Chat History:** Your conversations are saved and can be revisited at any time.

### Pro Tier

*   **All Free Tier Features:** Includes everything from the Free tier.
*   **Advanced AI Models:** Access to more powerful and specialized language models.
*   **Model Selection:** Choose the AI model that best suits your needs for a specific task.
*   **Agent Mode:** An intelligent agent that automatically selects the most appropriate AI model for your query.
*   **File Upload:** Upload documents (PDFs and text files) to provide context for your conversations, enabling Retrieval-Augmented Generation (RAG).

## Tech Stack

### Frontend

*   **Framework:** React
*   **Styling:** CSS, with separate styles for the Free and Pro versions.
*   **State Management:** A custom React hook (`useChat`) for managing chat state and interactions.

### Backend

*   **Framework:** FastAPI
*   **Database:**
    *   **PostgreSQL:** For user authentication and data.
    *   **ChromaDB:** For storing and retrieving document embeddings for RAG.
*   **AI/LLM:**
    *   `langchain-nvidia-ai-endpoints`: For integrating with NVIDIA's AI models.
    *   Various models from NVIDIA, Meta, and other providers.
*   **Authentication:** Passlib for password hashing and JWT for session management.

## Architecture

The application follows a client-server architecture:

*   **Frontend:** A single-page application (SPA) built with React that provides the user interface.
*   **Backend:** A FastAPI server that exposes a RESTful API for handling user authentication, chat functionality, and file uploads.

When a user sends a message, the frontend sends a request to the backend. The backend then uses the selected AI model (or the agent mode in the Pro version) to generate a response. If a user has uploaded files, the backend uses ChromaDB to retrieve relevant document chunks and provide them as context to the AI model.

## Getting Started

### Prerequisites

*   Node.js and npm
*   Python 3.7+ and pip
*   PostgreSQL

### Backend Setup

1.  Navigate to the `backend` directory.
2.  Create a virtual environment: `python -m venv venv`
3.  Activate the virtual environment: `source venv/bin/activate` (on Linux/macOS) or `venv\Scripts\activate` (on Windows).
4.  Install the required packages: `pip install -r requirements.txt`
5.  Create a `.env` file and add the necessary environment variables (see the Configuration section).
6.  Start the backend server: `uvicorn main:app --reload`

### Frontend Setup

1.  Navigate to the `frontend` directory.
2.  Install the required packages: `npm install`
3.  Start the frontend development server: `npm start`

## Configuration

The backend requires the following environment variables to be set in a `.env` file in the `backend` directory:

*   `CHROMA_API_KEY`: Your ChromaDB API key.
*   `CHROMA_TENANT`: Your ChromaDB tenant.
*   `CHROMA_DATABASE`: Your ChromaDB database.
*   `NVIDIA_API_KEY`: Your NVIDIA AI Endpoints API key.

## API Endpoints

*   `POST /register/`: Register a new user.
*   `POST /login/`: Log in a user.
*   `POST /uploadfile/`: Upload a file for RAG (Pro tier).
*   `POST /query/`: Send a query to the AI model.
*   `POST /query/stream/`: Send a query and stream the response.
*   `POST /delete_chat/`: Delete a chat and its associated data.
*   `POST /logout/`: Log out a user.