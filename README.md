# Chat Application

This is a real-time chat application built with a Django backend, WebSocket communication, and Redis for message caching. The frontend is implemented using HTML templates. The project follows SOLID principles to ensure maintainability and scalability.

## Features
- **User Authentication**: Login and registration system for users.
- **Room Management**: Users can create or join chat rooms.
- **Real-Time Messaging**: WebSocket-based chat with message rate limiting (1 message per second, 10 messages per minute).
- **Message Caching**: Messages are stored in Redis for active rooms. When the first user joins a room, messages are fetched from the PostgreSQL database. Subsequent users retrieve messages from Redis. Messages are cleared from Redis when all users leave the room.

## Tech Stack
- **Backend**: Django with WebSocket support (via Django Channels)
- **Database**: PostgreSQL
- **Caching**: Redis
- **Frontend**: HTML templates
- **Containerization**: Docker

## Prerequisites
- Docker
- Docker Compose

## Setup and Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```
2. Create a .env file in the project root with the following configuration:
```
POSTGRES_DB_NAME=postgres
POSTGRES_DB_USER=postgres
POSTGRES_DB_PASSWORD=postgres
POSTGRES_DB_HOST=postgres
POSTGRES_DB_PORT=5432
DJANGO_SECRET_KEY=django-insecure-1!p(mrem9s2(bi9vu%24g+mr1!o7$v6*0^6l^421)0-6)&74r=
REDIS_URL=redis://redis:6379
HOST=http://127.0.0.1:8000/
DOMAIN=127.0.0.1:8000
```
3. Build and run the project using Docker Compose:
```bash
docker-compose build
docker-compose up
```

4. Access the application at:\
http://127.0.0.1:8000

## Usage

1. **Login/Register:** Create an account or log in to access the chat features.
2. **Room Selection/Creation:** Choose an existing room or create a new one.
3. **Chatting:** Send and receive messages in real-time within the selected room.

## Architecture

- **WebSocket Communication:** Real-time messaging is handled using Django Channels with WebSocket protocol.
- **Redis Caching:** Messages are cached in Redis for performance. When a room is empty, messages are cleared from Redis to free up memory.
- **Rate Limiting:** Implemented to prevent spam, allowing only 1 message per second and 10 messages per minute per user.
- **SOLID Principles:** The codebase adheres to SOLID principles for clean, maintainable, and scalable code.