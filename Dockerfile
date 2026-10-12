FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Runner starts both services + proxy as local processes inside one container (no privileged netem needed)
CMD ["python", "-m", "chaos.runner", "experiments/latency_500ms.yml", "experiments/packet_drop_30.yml", "experiments/kill_inventory.yml", "--out", "results"]
