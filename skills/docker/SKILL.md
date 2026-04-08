---
name: docker
description: "Docker container operations. Use when: (1) managing containers, (2) building images, (3) viewing logs, (4) cleaning up."
---

# Docker Skill

Use docker for container management.

## When to Use

- Managing containers (start, stop, restart)
- Building images
- Viewing container logs
- Cleaning up unused containers/images

## Common Commands

```bash
# List containers
docker ps -a

# Build image
docker build -t myapp:latest .

# Run container
docker run -d myapp:latest

# View logs
docker logs <container_id>

# Clean up
docker system prune -a
```
