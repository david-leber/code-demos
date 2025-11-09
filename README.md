# 🐍 Coding Tutor IDE

An interactive IDE that teaches Python programming with integrated AI assistance. The IDE runs in a VM and executes student code in a separate, isolated VM for security.

## 🎯 Features

- **Interactive Code Editor**: Write Python code in a clean, web-based interface
- **AI-Powered Code Review**: Get instant feedback on your code from an AI assistant
- **Structured Lessons**: Progressive learning path with hands-on exercises
- **Safe Code Execution**: Student code runs in isolated Docker containers
- **Real-time Feedback**: See output immediately and get suggestions for improvement
- **Dual-VM Architecture**: IDE and code execution are completely isolated

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│       IDE VM (WSL/Linux)            │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Rust Web Server (Axum)     │  │
│  │   - Lesson Management        │  │
│  │   - AI Assistant Integration │  │
│  │   - Code Executor Client     │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Docker Containers          │  │
│  │   (Python Execution VMs)     │  │
│  │   - Isolated environment     │  │
│  │   - UV package manager       │  │
│  │   - Resource limits          │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## 📋 Prerequisites

- **Rust** (1.70+): [Install Rust](https://rustup.rs/)
- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **WSL** (Windows users): The IDE runs in WSL
- **UV** (optional): For local Python development

## 🚀 Quick Start

### 1. Build the Python Execution Docker Image

```bash
docker build -t coding-tutor-python:latest -f docker/Dockerfile .
```

### 2. Run the Application

```bash
# Optional: Set your Anthropic API key for AI features
export ANTHROPIC_API_KEY="your-api-key-here"

# Build and run
cargo run --release
```

### 3. Open the IDE

Navigate to `http://localhost:3000/static/index.html` in your browser.

## 🔧 Configuration

### Environment Variables

- `ANTHROPIC_API_KEY` - (Optional) API key for Claude AI integration
- `PORT` - (Optional) Server port (default: 3000)

### Adding Lessons

Create YAML files in `lessons_content/` directory:

```yaml
id: "lesson_id"
title: "Lesson Title"
description: "What students will learn"
objectives:
  - "Learning objective 1"
  - "Learning objective 2"
starter_code: |
  # Starter code here
  print("Hello!")
hints:
  - "Helpful hint 1"
  - "Helpful hint 2"
exercises:
  - id: "ex1"
    description: "Exercise description"
    test_code: |
      # Python code to test the student's solution
      print("✓ Test passed!")
    solution_example: |
      # Example solution
```

## 🏃 Development

### Project Structure

```
coding-tutor-ide/
├── src/
│   ├── main.rs              # Application entry point
│   ├── models/              # Data structures
│   ├── executor/            # Docker-based code execution
│   ├── lessons/             # Lesson management
│   ├── ai_assistant/        # AI integration
│   └── web/                 # Web server & API
├── static/                  # Frontend files
│   ├── index.html
│   ├── style.css
│   └── app.js
├── lessons_content/         # Lesson definitions
├── docker/                  # Docker configuration
└── Cargo.toml              # Rust dependencies
```

### Building

```bash
# Debug build
cargo build

# Release build
cargo build --release

# Run tests
cargo test
```

### Docker Image Management

```bash
# Build image
docker build -t coding-tutor-python:latest -f docker/Dockerfile .

# Test the image
docker run --rm -it coding-tutor-python:latest python3 -c "print('Hello from Docker!')"

# Clean up containers
docker ps -a | grep student-code | awk '{print $1}' | xargs docker rm -f
```

## 🔒 Security Features

1. **Isolated Execution**: Each code execution runs in a fresh Docker container
2. **Resource Limits**: Containers have CPU and memory limits
3. **Network Isolation**: Execution containers have no network access
4. **Non-root User**: Code runs as a non-privileged user
5. **Timeout Protection**: Executions are time-limited
6. **Automatic Cleanup**: Containers are removed after execution

## 🤖 AI Assistant

The AI assistant can work in two modes:

1. **Claude API Mode** (recommended): Set `ANTHROPIC_API_KEY` for intelligent code review
2. **Simple Mode**: Basic rule-based feedback without API key

The assistant provides:
- Code quality assessment
- Specific improvement suggestions
- Verification against lesson objectives
- Encouraging, educational feedback

## 📚 Lesson Design

Each lesson should:
1. Introduce one concept at a time
2. Provide clear learning objectives
3. Include starter code to guide students
4. Have practical exercises with automated tests
5. Offer hints without giving away the solution

## 🐛 Troubleshooting

### Docker Connection Failed
- Ensure Docker is running: `docker ps`
- Check Docker socket permissions
- On WSL: Make sure Docker Desktop has WSL integration enabled

### Port Already in Use
- Change port: `PORT=3001 cargo run`
- Kill existing process: `lsof -ti:3000 | xargs kill -9`

### Lessons Not Loading
- Check `lessons_content/` directory exists
- Verify YAML syntax in lesson files
- Check server logs for parsing errors

### AI Assistant Not Working
- Verify `ANTHROPIC_API_KEY` is set correctly
- Check API key has sufficient credits
- Simple mode still works without API key

## 🛠️ Future Enhancements

- [ ] WebAssembly-based code execution (no Docker required)
- [ ] Multi-language support (JavaScript, Rust, Go)
- [ ] User authentication and progress tracking
- [ ] Collaborative coding features
- [ ] Code playground with shareable links
- [ ] Mobile-responsive design improvements
- [ ] Syntax highlighting with Monaco Editor
- [ ] Integrated debugger
- [ ] Achievement system and badges

## 📝 License

MIT License - feel free to use this for educational purposes!

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Add new lessons
- Improve the AI feedback system
- Enhance the UI/UX
- Fix bugs
- Add tests

## 🙏 Acknowledgments

- Built with Rust and Axum
- Code execution via Docker/Bollard
- AI assistance powered by Anthropic Claude
- Inspired by interactive coding platforms like Codecademy and FreeCodeCamp
