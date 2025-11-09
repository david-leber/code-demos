# Python execution environment with UV
FROM python:3.12-slim

# Install UV
RUN pip install uv

# Create a non-root user for security
RUN useradd -m -u 1000 student && \
    mkdir -p /home/student/workspace && \
    chown -R student:student /home/student

# Set working directory
WORKDIR /home/student/workspace

# Switch to non-root user
USER student

# Set UV to create venvs in the workspace
ENV UV_PROJECT_ENVIRONMENT=/home/student/workspace/.venv

# Default command
CMD ["/bin/bash"]
