# Embodied Cybernetic Agency

A small research simulator for comparing rule-based agents under changing and unreliable conditions. Agents predict observations, track simulated resources, estimate risk, and change their behavior when risk increases.

This repository contains a FastAPI service, agent and battery simulations, a configurable GridWorld experiment runner, a standalone ROS 2 simulator bridge, and scripts for summarizing experiment results. The API container does not install or start ROS 2.

## What It Does

### GridWorld experiments

`src/run_experiments.py` runs agents through small grid tasks. A basic breadth-first-search policy navigates around obstacles while configured disturbances can add sensor noise, cause a sensor blackout, shift the goal, or weaken controls. Each run writes a step-by-step CSV file under `logs/raw/`.

The four conditions in `config/conditions.yaml` compare different agent components:

- **A:** reactive baseline without a world model, resource telemetry, or self-model.
- **B:** adds a prediction-based world model.
- **C:** adds simulated battery and temperature tracking.
- **D:** adds a self-model, risk-based regulation, and simulated substrate stress monitoring. A substrate freeze makes the agent shut down.

### Agent simulation

`app.py` contains a separate scalar-state simulation with noisy observations, world changes, and blackouts. Its agent tracks prediction error, uncertainty, risk, battery, and temperature. It also includes in-memory episodic memory, similarity matching, and a global workspace that selects the most salient signal.

Run it directly to print a 30-step trace:

```bash
python app.py
```

The FastAPI route `POST /agent/simulate` runs this simulation and returns a JSON summary and per-step trace.

### ROS 2 simulator bridge

`src/ros2_simulator_swarm_bridge.py` is a separate ROS 2 node for a two-drone simulator. It subscribes to `/simulator/current_telemetry` (`geometry_msgs/Twist`), publishes simulated velocity commands on `/sim/drone_alpha/cmd_vel` and `/sim/drone_beta/cmd_vel`, and publishes swarm status and diagnostics on `/swarm/network_comms_bus` and `/swarm/chatbot_diagnostics`. Its sensor input is currently hard-coded mock data and its battery state starts randomly; it is not deterministic experiment infrastructure or a physical-drone controller.

Run it only in an environment with ROS 2 and the `rclpy`, `geometry_msgs`, and `std_msgs` packages installed and sourced:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
python -m src.ros2_simulator_swarm_bridge
```

Connect it only to a simulator configured for these topics. ROS 2 dependencies are intentionally separate from `requirements.txt` and the API container.

### Self-healing battery pack

The merged battery module in `src/battery.py` simulates a four-cell pack with a
redundant-cell self-healing policy. Cell 2 is progressively degraded after step
20; any cell below 2.8 V is automatically marked as bypassed. The FastAPI route
`POST /battery/simulate?steps=30&seed=42` returns the pack trace and final
bypass state.

The experimental `POST /battery/autonomous?steps=30&seed=42` endpoint adds a
closed-loop controller. It maintains an operational self-model containing
health, risk, and confidence, chooses a recovery action, and applies hard
shutdown rules for dangerous temperature or voltage conditions. This is
self-monitoring autonomy, not a claim of consciousness or sentience.
The controller also forecasts the next minimum cell voltage and continuously
updates its estimated degradation rate from prediction error, making model
improvement measurable rather than assumed.
Both simulation endpoints accept `speed_multiplier=1..10`. At `10`, each
returned sample advances ten digital-twin steps; this accelerates experiments
only and never raises physical charging current.

The advanced chemistry screening model is available at
`POST /battery/chemistry/evaluate`. It estimates energy, SoH, and swelling
boundary risk from chemistry/specification assumptions. Its output is labeled
`screening_estimate`; it is not measured cell telemetry and must not be used as
a physical fast-charge authorization.

Android integration is available through `src/android_transport.py`. It reads
`/sys/class/power_supply/battery` telemetry when present and runs a preservation
policy that reduces current at high temperature or SoC and suspends charging at
critical temperature. The transport is read-only by default; physical sysfs
writes require an available target path and explicit `write_enabled=True`, and
must be validated against the device vendor's power-supply nodes first.

Recorded BMS data can be replayed through
`POST /battery/evaluate` with a JSON array of observations containing `time`,
four `cells`, `temperature`, `current`, and four `bypass` flags. The endpoint
returns mean and maximum prediction error plus every autonomous decision. A
CAN, UART, or hardware-in-the-loop adapter can provide the same observation
shape later.

For UART-style newline-delimited JSON, use
`.venv/bin/python scripts/replay_battery_telemetry.py telemetry.jsonl`, or pipe
the stream through stdin. Each line is validated before it reaches the
controller; hardware-specific CAN decoding should produce the same observation
dictionary before using this adapter.
The reference decoder in `src/can_telemetry.py` expects cell voltages on frame
`0x100` and temperature, current, bypass flags, and time on frame `0x101`.
These IDs and encodings are examples only and must be changed to match the
target BMS protocol before connecting physical hardware.

Autonomous and replay responses include a metrics scorecard with action counts,
fault events, bypass counts, safety overrides, risk, health change, and
prediction error. This makes experiments comparable across seeds and telemetry
files.

### Hardware boundary

The current repository is simulation and telemetry-replay software. Before
connecting a physical pack, add a hardware-specific decoder, independent
over-voltage and over-temperature cutoffs, contactor interlocks, watchdogs,
fuses, isolation monitoring, and a hardware-in-the-loop test campaign. The AI
controller must remain subordinate to those deterministic protections and must
not directly energize a pack without an independently verified actuator layer.
Every decision currently passes through `DryRunActuator`, which never energizes
hardware. The controller and actuator share `SafetyPolicy` limits for shutdown
voltage, shutdown temperature, and current-conservation voltage, preventing
configuration drift between reasoning and interlock layers.
The optional `GuardedHardwareActuator` additionally requires a recognized cable
profile, successful charger handshake, explicit `ARM_CHARGER` confirmation, a
valid current limit, and a healthy transport before enabling output. Unknown
cables, failed handshakes, faults, and unsafe measurements remain blocked.

### Audited substrate demo

`POST /simulate` runs two fixed sensor-distribution examples through an information-stress calculation. It reports simulated substrate temperatures and whether the stress checks pass. It is separate from both the GridWorld experiment and the `app.py` agent simulation.

## Install And Run

Python 3.10 or later is expected; the repository does not currently enforce a Python version through package metadata. Create an environment and install the dependencies:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Run the commands below from the repository root. The `Build.py` helper also
resolves project paths from its own location, so its commands remain usable
when invoked with an absolute path from another directory.

Start the API from the repository root:

```bash
.venv/bin/python -m uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.
Direct Uvicorn startup is for local development. It allows unauthenticated requests unless `API_AUTH_TOKEN` is set; use the Compose deployment below for production, where authentication is required and HTTPS is provided by Caddy.

Run all configured GridWorld experiments (4 conditions, 5 seeds, 3 tasks):

```bash
.venv/bin/python -m src.run_experiments
```

Summarize the CSV logs and regenerate the figures and table:

```bash
.venv/bin/python scripts/recompute_metrics.py
.venv/bin/python scripts/regenerate_figures.py
```

Run the pytest suite:

```bash
.venv/bin/python -m pytest -q
```

The equivalent project helper is `.venv/bin/python Build.py test`.

### Container deployment

The API and HTTPS proxy can be started with Docker Compose. First copy `.env.example` to `.env`, set `API_DOMAIN` to a public DNS name pointing at this host, and replace `API_AUTH_TOKEN` with a random secret (for example, generate one with `openssl rand -hex 32`). Open ports 80 and 443 on the host for Caddy's certificate challenge and HTTPS traffic.

```bash
cp .env.example .env
# Edit .env before continuing.
docker compose up --build -d
docker compose logs -f api caddy
```

The API requires the configured bearer token on all routes except `/health`; the API container is not published directly to the host. Caddy obtains and renews TLS certificates. Experiment logs and TLS state are kept in named volumes. Stop the stack with `docker compose down`. The API container runs as a non-root user, has a health check, and does not mount host sensors, devices, or shared IPC. Keep `.env` private and rotate the API token when access must be revoked. This is single-token authentication, not per-user identity or role-based access control.

### Mobile app

The Expo SDK 57 client in `mobile/` targets iOS and Android. It can connect to the HTTPS API, store the bearer token in platform secure storage, and run the existing agent and battery simulations. The DJI Mavic 4 status remains disconnected; the app does not issue aircraft commands.

```bash
cd mobile
npm install
npm start
```

Store builds use Expo Application Services (EAS): configure the Apple and Google developer accounts and confirm the bundle/package identifier in `mobile/app.json`, then run `npx eas-cli@latest build --platform all --profile production`. EAS requires account credentials and signing configuration; this Linux workspace cannot produce a signed App Store submission by itself. The API endpoint entered in the app must be the HTTPS domain configured above.

See [report/USAGE.md](report/USAGE.md) for additional usage details.

## API Endpoints

- `GET /health` checks that the service is running.
- `GET /config` returns the configured conditions, tasks, and world.
- `GET /simulate` runs the audited substrate demo.
- `POST /agent/simulate?steps=30&seed=42` runs the `app.py` agent simulation. Steps must be between 1 and 500.
- `POST /battery/simulate?steps=30&seed=42` runs the self-healing battery simulation. Steps must be between 1 and 500.
- `POST /battery/autonomous?steps=30&seed=42` runs the self-modeling autonomous battery controller. Steps must be between 1 and 500.
- `POST /battery/evaluate` replays recorded BMS observations through the autonomous controller and reports forecast accuracy.
- `POST /battery/chemistry/evaluate` evaluates the advanced chemistry screening model.
- `POST /experiments/run?condition_id=D&seed=42&task_id=task_1` runs one GridWorld experiment. `condition_id` is required; seed and task have defaults.
- `GET /results` summarizes CSV files in `logs/raw/`.
- `GET /dashboard` serves a small HTML dashboard.

## Runtime And Support

- FastAPI application metadata version: **0.1.0**.
- The legacy Buildozer configuration is Android-only and unverified. The cross-platform iOS/Android client is the Expo project in `mobile/`.
- Python 3.10 or later is expected; package metadata does not enforce the minimum.
- Python runtime and test dependencies are listed in [requirements.txt](requirements.txt) using minimum-version constraints without a lockfile. The mobile app pins its JavaScript dependency tree in `mobile/package-lock.json`.
- Android packaging in `buildozer.spec` is a separate, unverified target. ROS 2 packages must be installed using the target ROS distribution.

## Production And Safety Limits

- This is a rule-based research prototype, not a trained language model or a production robot or battery controller.
- GridWorld movement and battery telemetry are simulated. The API container does not access physical sensors or hardware. The ROS 2 node publishes simulator command topics and must not be connected to physical actuators.
- The GridWorld runner uses a simple pathfinding policy. The experiments compare the configured risk and resource-monitoring behavior, not learned navigation.
- The scalar simulation in `app.py`, the audited `/simulate` demo, and the GridWorld runner are separate simulation paths; only the API exposes them together as routes.
- Battery chemistry results are screening estimates, and battery actuation is dry-run only. The optional Android sysfs transport is read-only by default; enabling writes is not a substitute for device-vendor validation or independent hardware interlocks.
- The Compose deployment enforces bearer-token authentication and Caddy TLS. Tokens are shared by all app installs; deployments needing individual accounts, roles, or revocation should use an identity provider. Add rate controls, monitoring, log retention/backup, and a reviewed dependency lock before public production use.
- No hardware-in-the-loop qualification, safety certification, availability target, or production security audit is provided. Keep deterministic hardware protections independent of these simulations and controllers.
