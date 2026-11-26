# Service foundation development

Branch base: contract commit `6eece93`. Implemented here: Order and Analysis
service skeletons, two health routes each, build tooling, Dockerfiles and a reserved
trace-context module. No orders, reservations, payments, broker clients, graph,
model calls, authentication, shared infrastructure or cloud deployment exist yet.
Other owners' services remain unimplemented. Team contract review remains pending.

## Toolchain

Use Java 21 (both `java -version` and `./mvnw --version` must show 21), Maven
3.9.11 via the generated wrapper, and Python 3.11. Runtime dependencies are pinned
by the Spring Boot 3.5.16 BOM and the Analysis requirements.lock. The Maven wrapper
3.3.4 distribution is checksum-pinned. No global runtime installation is scripted.
Dockerfiles use official versioned runtime images pinned by registry digest; container verification requires
a running Docker daemon. The host's Java 11/Maven Java 18 are insufficient.

Spring Boot's [Java compatibility](https://docs.spring.io/spring-boot/3.5/system-requirements.html),
the [official Maven wrapper](https://maven.apache.org/tools/wrapper/), and
[FastAPI container guidance](https://fastapi.tiangolo.com/deployment/docker/)
were checked when setting up these skeletons. Exact pins are implementation
selections for this branch, not evidence of approval from every service owner.

## Native setup and tests

Select a locally installed JDK 21 using your normal Java version manager. Check
JAVA_HOME points at that JDK; do not reuse the temporary validation path on another
machine. Then run from repository root:

```sh
./mvnw --version
./mvnw verify
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install setuptools==80.9.0 wheel==0.45.1
.venv/bin/python -m pip install --no-deps --no-build-isolation -e services/analysis-service
.venv/bin/python -m pytest tests/contracts services/analysis-service/tests -q
.venv/bin/python -m pip check
```

requirements.in lists direct runtime choices; requirements.lock contains their
resolved Python 3.11 dependencies plus pytest/test dependencies. Root dev
requirements include this lock so there is one consistent environment. Update
pins/lock together, validate resolution, and run the same checks after updates.
The setuptools/wheel pins above match pyproject.toml and allow offline editable
installation after dependency setup. First Maven/Python installs require network.

pytest uses importlib mode so future service test names do not collide. Contract
tests use explicit package imports. No database is needed for unit/contract tests.
Java HTTP tests use temporary loopback ports, mock successful database connections,
and check a real PostgreSQL driver against an unreachable local port with a bounded
readiness deadline. They do not prove successful PostgreSQL integration, bad-password
handling against a live database, or migration behavior.

## Run locally

In separate terminals, after setup:

```sh
java -jar services/order-service/target/order-service-0.1.0-SNAPSHOT.jar
```

```sh
.venv/bin/python -m agentmesh_analysis.main
```

Both bind to loopback by default. Order uses port 8081, Analysis 8001. Override
ORDER_PORT/ORDER_BIND_HOST and ANALYSIS_PORT/ANALYSIS_BIND_HOST as needed. The
.env.example file is a reference; processes do not automatically load it. Export
only the settings you need. Never commit a filled .env file or use credentials
in command-line arguments, fixtures or reports. Stop the native processes with
Ctrl-C; shutdown preserves external database state.

```sh
.venv/bin/python scripts/verify/service_health.py --expect-order-unready
```

The flag explicitly expects Order readiness HTTP 503 when the database is absent;
it is a skeleton startup check, not proof that Order can process business work.
Without the flag, the probe requires both services to be ready and fails otherwise.
Timeouts are bounded; --order-base-url/--analysis-base-url select alternate ports.

| Route | Order | Analysis |
| --- | --- | --- |
| /health/live | 200 while HTTP process responds; does not touch DB | 200 |
| /health/ready | 503 until a configured database accepts a bounded validation query | 200; no required dependencies in current skeleton |

To connect an existing dedicated Order PostgreSQL database, export
ORDER_DATABASE_ENABLED=true, ORDER_DATABASE_URL (JDBC PostgreSQL URL),
ORDER_DATABASE_USER and ORDER_DATABASE_PASSWORD. No default credentials are
supplied. The database owner provisions shared databases/users separately; the services
create none. The isolated check below provisions a disposable test database only. Missing configuration and connectivity errors return the shared
error envelope without driver exception text. Connection pool acquisition is 2 s,
validation 1 s, driver connect/socket 2 s. Model credentials are unused and cannot
prevent health startup. Flyway dependencies are present but migration execution
is disabled and no tables/migrations are supplied.

Order readiness currently checks only its database: broker readiness must be
added when broker choice/client integration is agreed. Analysis readiness does
not certify trace-query/model availability. Startup logs use JSON console output;
no request bodies or model keys are logged. Actuator web endpoints and interactive
Python API docs are disabled. These services have no privileged/business handlers
and are local development skeletons, not public releases.

## Container handoff

From repository root, with Docker running:

```sh
docker build -f services/order-service/Dockerfile -t agentmesh-order:dev .
docker build -f services/analysis-service/Dockerfile -t agentmesh-analysis:dev .
docker run --rm -p 127.0.0.1:8081:8081 agentmesh-order:dev
docker run --rm -p 127.0.0.1:8001:8001 agentmesh-analysis:dev
```

Run the two containers in separate terminals. Both run as numeric nonroot users;
Dockerfiles change binding to 0.0.0.0 inside the container only. Stop with Ctrl-C.
Database settings may be supplied through a private env file when available;
inside a container, localhost is that container, not the host database. Shared
Compose DNS, roles/databases, private ports, resource limits, healthchecks, broker,
collector, Jaeger/Prometheus/Loki and retention remain coordinated with their
owners. No Compose file, fake dependency, cloud resource or paid API is added here.

## Remaining acceptance work

The complete shared runtime foundation is not complete: shared stack choices,
other service skeletons, broker readiness, telemetry export/query and sanitized
backend fixtures still need integration. The Order/Analysis container builds,
PostgreSQL success/bad-credential checks and restart/reconnection checks have now
passed in isolation; see the November 26 record below. This does not prove shared
deployment or durable data recovery. Provider/hosting/auth choices remain open
and no teammate approval is implied by these skeletons.

## Verification recorded November 25, 2026

- Generated wrapper with Maven wrapper plugin 3.3.4; verified the Maven 3.9.11
  archive against its official SHA-512 and pinned its SHA-256 in wrapper properties.
- Verified downloaded Adoptium Java 21.0.13.1+2 archive checksum and used it under
  /tmp for verification, leaving global Java/Maven installations unchanged.
- Ran `./mvnw -o -B -Dmaven.repo.local=/tmp/agentmesh-m2 verify` with that JDK and
  a temporary MAVEN_USER_HOME: BUILD SUCCESS, 7 tests, no failures/errors/skips.
- Ran `.venv/bin/python -m pytest tests/contracts services/analysis-service/tests -q`:
  58 passed. One upstream Starlette/AnyIO test-client deprecation warning remains.
- Ran `.venv/bin/python -m pip check`: no broken requirements.
- Started both native processes on alternate loopback ports and ran
  scripts/verify/service_health.py with --expect-order-unready: all four expected
  health responses passed. Confirmed default probe exits 1 for unready Order.
  All temporary service processes were stopped afterward.
- `git diff --check` passed. No generated artifacts, personal files or credentials
  were staged; .DS_Store was present before this work and remains untouched.
- Network downloads and loopback server tests required sandbox permission retries.
  Docker builds, successful live PostgreSQL connectivity and telemetry were not run.

## Repeatable isolated container check

After building both images, run:

```sh
.venv/bin/python scripts/verify/container_health.py
```

This requires only a running local Docker engine and the two built images. It
pulls a digest-pinned official PostgreSQL 16 test image, creates a unique labelled
network and disposable database, generates temporary random passwords, and checks:

- Both service containers are alive and ready with a reachable database.
- Invalid database credentials produce Order readiness 503 while liveness stays 200.
- Restarting Order reconnects successfully.
- Database loss changes readiness to 503, while both HTTP processes remain alive.
- Returning the database restores Order readiness.
- Skeleton startup creates no application tables.

Only service HTTP ports are published, on loopback with dynamically allocated
host ports. The database publishes no host port. Password values are passed using
process environment variables rather than command-line arguments and are not
printed. Cleanup removes only the containers/network created by this invocation;
no global prune or shared-volume deletion is used. Database storage is tmpfs and
is discarded on stop: this check proves reconnection, not durable data recovery.
The PostgreSQL image version is test-only, not a shared deployment decision.

The Java image uses the ARM64/AMD64-compatible Temurin 21.0.13_9 manifests.
Its build stage installs unzip so Maven downloads the ZIP whose checksum is pinned
in wrapper properties; the wrapper's tar.gz fallback has a different checksum.


## Verification recorded November 26, 2026

- Started Docker Desktop and built both service images successfully with the
  documented docker build commands. The original Java tag lacked Linux ARM64;
  switched to verified ARM64/AMD64-compatible Java 21.0.13_9 pinned manifests.
- Fixed the build-stage missing-unzip issue without disabling Maven checksum
  validation. Wrapper ZIP checksum verification succeeded in the container build.
- Ran `.venv/bin/python scripts/verify/container_health.py`: passed both service
  readiness/liveness checks, invalid-password handling, Order restart, database
  loss/return, no application tables and cleanup. The probe rediscovers dynamic
  host ports after container restart. An earlier run exposed this probe issue;
  the corrected full run exited 0. No verification containers/network remain.
- Reran offline Maven verification using the temporary Java 21 kit: BUILD SUCCESS,
  7 tests, no failures/errors/skips.
- Reran Python/contract tests: 58 passed, one upstream test-client deprecation
  warning. pip check reported no broken requirements.
- Docker Desktop and the two local development images remain available. Disposable
  test state was removed. No cloud resources, business records or paid calls were
  created. Commits/pushes/PR creation still require explicit user approval.
