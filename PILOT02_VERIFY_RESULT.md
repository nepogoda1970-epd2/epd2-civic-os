# PILOT-02 Docker Verification Result

**Verdict:** NOT VERIFIED — PILOT-02 product smoke failed

- Workflow run: 32123366022
- Commit: 20d7355b5aa37746d4e59cb59791bd9bb405af5a
- Environment rc: 0
- Integrity rc: 0
- Smoke rc: 1
- Success-marker rc: 1

## Environment log
```text
## Environment
Linux runnervmzvulz 6.17.0-1022-azure #22-Ubuntu SMP Mon Jul 27 17:24:03 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
PRETTY_NAME="Ubuntu 24.04.4 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.4 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=noble
LOGO=ubuntu-logo
Docker version 28.0.4, build b8034c0
Docker Compose version v2.38.2
lrwxrwxrwx 1 root root 13 Aug 18 09:45 /dev/fd -> /proc/self/fd
process-substitution-ok
```

## Integrity log (tail)
```text
tests/contract/test_ct00_05_unsupported_event_version.py: OK
tests/contract/test_ct00_06_missing_permission.py: OK
tests/contract/test_ct00_07_audit_creation.py: OK
tests/contract/test_ct00_08_identity_leakage.py: OK
tests/contract/test_ct00_09_vote_linkability.py: OK
tests/contract/test_ct00_10_rule_freeze.py: OK
tests/contract/test_ct00_11_ai_human_control.py: OK
tests/contract/test_ct00_12_emergency_stop_not_applicable.py: OK
tests/contract/test_openapi_contract.py: OK
tests/contract/test_pack15_event_schemas.py: OK
tests/contract/test_property_based.py: OK
tests/contract/test_reason_codes_registry.py: OK
tests/contract/test_state_transitions.py: OK
tests/fixtures/.gitkeep: OK
tests/repository/_pack25_governance_fixtures.py: OK
tests/repository/test_archive_hygiene.py: OK
tests/repository/test_canon_0_8_0_amendment.py: OK
tests/repository/test_ctrl01_control_plane_governance.py: OK
tests/repository/test_forbidden_paths.py: OK
tests/repository/test_pack07_duplicated_logic_parity.py: OK
tests/repository/test_pack13_fir_matrix.py: OK
tests/repository/test_pack14_default_binding.py: OK
tests/repository/test_pack14_duplicated_logic_parity.py: OK
tests/repository/test_pack14_fir_matrix.py: OK
tests/repository/test_pack15_default_binding.py: OK
tests/repository/test_pack16d_prettier_allowlist.py: OK
tests/repository/test_pack16d_protected_notation.py: OK
tests/repository/test_pack16d_signature_dependency.py: OK
tests/repository/test_pack16d_voting_profile_packaging.py: OK
tests/repository/test_pack17a_local_ci_driver.py: OK
tests/repository/test_pack17a_specification.py: OK
tests/repository/test_pack17b_local_ci_stages.py: OK
tests/repository/test_pack17b_packaging.py: OK
tests/repository/test_pack17c_producer.py: OK
tests/repository/test_pack17cc1_verifier_runtime.py: OK
tests/repository/test_pack17cc2_windows_safety.py: OK
tests/repository/test_pack17cc3_archive_name_safety.py: OK
tests/repository/test_pack17d_incident_boundary.py: OK
tests/repository/test_pack18_frontend_governance.py: OK
tests/repository/test_pack19_candidacy_governance.py: OK
tests/repository/test_pack20_office_mandate_governance.py: OK
tests/repository/test_pack21_assembly_governance.py: OK
tests/repository/test_pack22_correspondence_governance.py: OK
tests/repository/test_pack22_local_ci_mypy_coverage.py: OK
tests/repository/test_pack23_casework_governance.py: OK
tests/repository/test_pack23_local_ci_mypy_coverage.py: OK
tests/repository/test_pack24_local_ci_mypy_coverage.py: OK
tests/repository/test_pack24_protected_reporting_governance.py: OK
tests/repository/test_pack25_local_ci_mypy_coverage.py: OK
tests/repository/test_pack25_procurement_governance.py: OK
tests/repository/test_pack25_register_freshness.py: OK
tests/repository/test_pack25c1_harness_integrity.py: OK
tests/repository/test_pack26_local_ci_mypy_coverage.py: OK
tests/repository/test_pack26_people_administration_governance.py: OK
tests/repository/test_pack27_conflict_recusal_governance.py: OK
tests/repository/test_pack28_local_ci_mypy_coverage.py: OK
tests/repository/test_pack28_transparency_publication_governance.py: OK
tests/repository/test_pack28c2_verifier_dependency_ownership.py: OK
tests/repository/test_pack29_local_ci_mypy_coverage.py: OK
tests/repository/test_pack29_representative_desk_governance.py: OK
tests/repository/test_pack30_emergency_governance_governance.py: OK
tests/repository/test_pack30_local_ci_mypy_coverage.py: OK
tests/repository/test_pack31_local_ci_mypy_coverage.py: OK
tests/repository/test_pack31_oversight_governance.py: OK
tests/repository/test_pack32_local_ci_mypy_coverage.py: OK
tests/repository/test_pack32_program_governance.py: OK
tests/repository/test_pack32_register_v14_vcrypto_gate.py: OK
tests/repository/test_pack33_local_ci_mypy_coverage.py: OK
tests/repository/test_pack33_routing_governance.py: OK
tests/repository/test_pack34_delegation_reputation_governance.py: OK
tests/repository/test_pack34_local_ci_mypy_coverage.py: OK
tests/repository/test_pack35_lobbying_disclosure_governance.py: OK
tests/repository/test_pilot01_docker_build_path.py: OK
tests/repository/test_pilot02_site_migration.py: OK
tests/repository/test_prod01_runtime_spine.py: OK
tests/repository/test_required_files.py: OK
tests/repository/test_service_boundaries.py: OK
tests/repository/test_system_wide_corrective_closure.py: OK
tests/repository/test_version_consistency.py: OK
uv.lock: OK
```

## Product smoke log (tail)
```text
 voting  Built
  ok   voting image built
  ... building runtime
#0 building with "default" instance using docker driver

#1 [runtime internal] load build definition from runtime.Dockerfile
#1 transferring dockerfile: 2.40kB done
#1 DONE 0.0s

#2 [runtime internal] load metadata for docker.io/library/python:3.12-slim@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a
#2 DONE 0.0s

#3 [runtime internal] load metadata for ghcr.io/astral-sh/uv:0.8.17
#3 DONE 0.1s

#4 [runtime internal] load .dockerignore
#4 transferring context: 2.73kB done
#4 DONE 0.0s

#5 [runtime] FROM ghcr.io/astral-sh/uv:0.8.17@sha256:e4644cb5bd56fdc2c5ea3ee0525d9d21eed1603bccd6a21f887a938be7e85be1
#5 DONE 0.0s

#6 [runtime build 1/9] FROM docker.io/library/python:3.12-slim@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a
#6 CACHED

#7 [runtime internal] load build context
#7 transferring context: 148.71kB 0.1s done
#7 DONE 0.1s

#8 [runtime build 6/9] COPY services ./services
#8 CACHED

#9 [runtime build 2/9] COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /usr/local/bin/uv
#9 CACHED

#10 [runtime build 3/9] WORKDIR /srv/epd2
#10 CACHED

#11 [runtime build 7/9] COPY contracts ./contracts
#11 CACHED

#12 [runtime build 4/9] COPY pyproject.toml uv.lock ./
#12 CACHED

#13 [runtime build 5/9] COPY packages ./packages
#13 CACHED

#14 [runtime build 8/9] COPY conftest.py ./
#14 CACHED

#15 [runtime runtime 2/4] RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin epd2
#15 0.157 useradd warning: epd2's uid 10001 is greater than SYS_UID_MAX 999
#15 DONE 0.2s

#16 [runtime runtime 3/4] WORKDIR /srv/epd2
#16 DONE 0.0s

#17 [runtime build 9/9] RUN uv sync --frozen --no-dev --package epd2-runtime
#17 0.301 Using CPython 3.12.14 interpreter at: /usr/local/bin/python3
#17 0.301 Creating virtual environment at: .venv
#17 0.317    Building epd2-runtime @ file:///srv/epd2/packages/python/epd2-runtime
#17 0.317    Building epd2-audit-core @ file:///srv/epd2/services/audit-core
#17 0.317    Building epd2-citizen-office-routing-service @ file:///srv/epd2/services/citizen-office-routing-service
#17 0.318    Building epd2-core @ file:///srv/epd2/packages/python/epd2-core
#17 0.357 Downloading psycopg-binary (4.9MiB)
#17 0.358 Downloading pydantic-core (2.0MiB)
#17 0.488  Downloading pydantic-core
#17 0.526  Downloading psycopg-binary
#17 1.796       Built epd2-core @ file:///srv/epd2/packages/python/epd2-core
#17 1.798       Built epd2-runtime @ file:///srv/epd2/packages/python/epd2-runtime
#17 1.800       Built epd2-audit-core @ file:///srv/epd2/services/audit-core
#17 1.803       Built epd2-citizen-office-routing-service @ file:///srv/epd2/services/citizen-office-routing-service
#17 1.804 Prepared 25 packages in 1.49s
#17 1.851 Installed 25 packages in 46ms
#17 2.445 Bytecode compiled 478 files in 593ms
#17 2.445  + annotated-doc==0.0.5
#17 2.445  + annotated-types==0.7.0
#17 2.445  + anyio==4.14.2
#17 2.445  + argon2-cffi==25.1.0
#17 2.445  + argon2-cffi-bindings==25.1.0
#17 2.445  + cffi==2.1.0
#17 2.445  + click==8.4.2
#17 2.445  + epd2-audit-core==0.1.0 (from file:///srv/epd2/services/audit-core)
#17 2.445  + epd2-citizen-office-routing-service==0.1.0 (from file:///srv/epd2/services/citizen-office-routing-service)
#17 2.445  + epd2-core==0.1.0 (from file:///srv/epd2/packages/python/epd2-core)
#17 2.445  + epd2-runtime==0.1.0 (from file:///srv/epd2/packages/python/epd2-runtime)
#17 2.445  + fastapi==0.141.1
#17 2.445  + h11==0.16.0
#17 2.445  + idna==3.18
#17 2.445  + psycopg==3.3.4
#17 2.445  + psycopg-binary==3.3.4
#17 2.445  + psycopg-pool==3.3.1
#17 2.445  + pycparser==3.0
#17 2.446  + pydantic==2.13.4
#17 2.446  + pydantic-core==2.46.4
#17 2.446  + pyyaml==6.0.3
#17 2.446  + starlette==1.6.0
#17 2.446  + typing-extensions==4.16.0
#17 2.446  + typing-inspection==0.4.2
#17 2.446  + uvicorn==0.52.3
#17 DONE 2.5s

#18 [runtime runtime 4/4] COPY --from=build --chown=epd2:epd2 /srv/epd2 /srv/epd2
#18 DONE 0.4s

#19 [runtime] exporting to image
#19 exporting layers
#19 exporting layers 0.7s done
#19 writing image sha256:0d31cafe8076cd6ce117aca8e1f8e0dec594375dd99ec793e1ccf6bca7b32f0f done
#19 naming to docker.io/epd2-pilot/runtime:0.51.0 done
#19 DONE 0.7s

#20 [runtime] resolving provenance for metadata file
#20 DONE 0.0s
 runtime  Built
  ok   runtime image built
  ok   three images built sequentially: frontend voting runtime

[2] start PostgreSQL / runtime / frontend / voting
 database Pulling 
 55afa1ecc21d Already exists 
 6a47e1b9b254 Pulling fs layer 
 19a2a5ab27c1 Pulling fs layer 
 5e81018bec01 Pulling fs layer 
 be6f407f5414 Pulling fs layer 
 f0e7204f9584 Pulling fs layer 
 8225e2970a7f Pulling fs layer 
 48d0d8b0e136 Pulling fs layer 
 27d0ba4f668a Pulling fs layer 
 b053c4426c4a Pulling fs layer 
 7f5de3d007ea Pulling fs layer 
 be6f407f5414 Waiting 
 f0e7204f9584 Waiting 
 8225e2970a7f Waiting 
 48d0d8b0e136 Waiting 
 27d0ba4f668a Waiting 
 b053c4426c4a Waiting 
 7f5de3d007ea Waiting 
 5e81018bec01 Downloading [==================================================>]     172B/172B
 5e81018bec01 Verifying Checksum 
 5e81018bec01 Download complete 
 6a47e1b9b254 Downloading [==================================================>]     969B/969B
 6a47e1b9b254 Verifying Checksum 
 6a47e1b9b254 Download complete 
 6a47e1b9b254 Extracting [==================================================>]     969B/969B
 19a2a5ab27c1 Downloading [>                                                  ]  15.79kB/900.3kB
 6a47e1b9b254 Extracting [==================================================>]     969B/969B
 6a47e1b9b254 Pull complete 
 19a2a5ab27c1 Downloading [==================================================>]  900.3kB/900.3kB
 19a2a5ab27c1 Verifying Checksum 
 19a2a5ab27c1 Download complete 
 19a2a5ab27c1 Extracting [=>                                                 ]  32.77kB/900.3kB
 be6f407f5414 Downloading [==================================================>]     116B/116B
 be6f407f5414 Verifying Checksum 
 be6f407f5414 Download complete 
 19a2a5ab27c1 Extracting [==================================================>]  900.3kB/900.3kB
 19a2a5ab27c1 Extracting [==================================================>]  900.3kB/900.3kB
 19a2a5ab27c1 Pull complete 
 5e81018bec01 Extracting [==================================================>]     172B/172B
 5e81018bec01 Extracting [==================================================>]     172B/172B
 5e81018bec01 Pull complete 
 f0e7204f9584 Downloading [>                                                  ]  540.7kB/111.3MB
 be6f407f5414 Extracting [==================================================>]     116B/116B
 be6f407f5414 Extracting [==================================================>]     116B/116B
 be6f407f5414 Pull complete 
 8225e2970a7f Downloading [==================>                                ]  3.502kB/9.673kB
 8225e2970a7f Downloading [==================================================>]  9.673kB/9.673kB
 8225e2970a7f Verifying Checksum 
 8225e2970a7f Download complete 
 48d0d8b0e136 Downloading [==================================================>]     129B/129B
 48d0d8b0e136 Verifying Checksum 
 27d0ba4f668a Downloading [==================================================>]     169B/169B
 27d0ba4f668a Download complete 
 b053c4426c4a Downloading [============================>                      ]  3.502kB/6.112kB
 b053c4426c4a Downloading [==================================================>]  6.112kB/6.112kB
 b053c4426c4a Verifying Checksum 
 b053c4426c4a Download complete 
 f0e7204f9584 Downloading [============>                                      ]  28.01MB/111.3MB
 7f5de3d007ea Downloading [==================================================>]     185B/185B
 7f5de3d007ea Verifying Checksum 
 7f5de3d007ea Download complete 
 f0e7204f9584 Downloading [============================>                      ]  64.09MB/111.3MB
 f0e7204f9584 Downloading [=============================================>     ]  100.2MB/111.3MB
 f0e7204f9584 Verifying Checksum 
 f0e7204f9584 Download complete 
 f0e7204f9584 Extracting [>                                                  ]  557.1kB/111.3MB
 f0e7204f9584 Extracting [==>                                                ]  5.014MB/111.3MB
 f0e7204f9584 Extracting [======>                                            ]  13.37MB/111.3MB
 f0e7204f9584 Extracting [=========>                                         ]  21.73MB/111.3MB
 f0e7204f9584 Extracting [=============>                                     ]  30.08MB/111.3MB
 f0e7204f9584 Extracting [=================>                                 ]  38.44MB/111.3MB
 f0e7204f9584 Extracting [=====================>                             ]  46.79MB/111.3MB
 f0e7204f9584 Extracting [========================>                          ]  54.59MB/111.3MB
 f0e7204f9584 Extracting [==========================>                        ]   59.6MB/111.3MB
 f0e7204f9584 Extracting [==============================>                    ]   67.4MB/111.3MB
 f0e7204f9584 Extracting [=================================>                 ]   75.2MB/111.3MB
 f0e7204f9584 Extracting [====================================>              ]  81.33MB/111.3MB
 f0e7204f9584 Extracting [=====================================>             ]  82.44MB/111.3MB
 f0e7204f9584 Extracting [======================================>            ]  85.23MB/111.3MB
 f0e7204f9584 Extracting [========================================>          ]  89.69MB/111.3MB
 f0e7204f9584 Extracting [==========================================>        ]  94.14MB/111.3MB
 f0e7204f9584 Extracting [============================================>      ]  98.04MB/111.3MB
 f0e7204f9584 Extracting [================================================>  ]  108.1MB/111.3MB
 f0e7204f9584 Extracting [==================================================>]  111.3MB/111.3MB
 f0e7204f9584 Pull complete 
 8225e2970a7f Extracting [==================================================>]  9.673kB/9.673kB
 8225e2970a7f Extracting [==================================================>]  9.673kB/9.673kB
 8225e2970a7f Pull complete 
 48d0d8b0e136 Extracting [==================================================>]     129B/129B
 48d0d8b0e136 Extracting [==================================================>]     129B/129B
 48d0d8b0e136 Pull complete 
 27d0ba4f668a Extracting [==================================================>]     169B/169B
 27d0ba4f668a Extracting [==================================================>]     169B/169B
 27d0ba4f668a Pull complete 
 b053c4426c4a Extracting [==================================================>]  6.112kB/6.112kB
 b053c4426c4a Extracting [==================================================>]  6.112kB/6.112kB
 b053c4426c4a Pull complete 
 7f5de3d007ea Extracting [==================================================>]     185B/185B
 7f5de3d007ea Extracting [==================================================>]     185B/185B
 7f5de3d007ea Pull complete 
 database Pulled 
 Network epd2-pilot-01_default  Creating
 Network epd2-pilot-01_default  Created
 Volume "epd2-pilot-01_epd2-pilot-db"  Creating
 Volume "epd2-pilot-01_epd2-pilot-db"  Created
 Container epd2-pilot-01-database-1  Creating
 Container epd2-pilot-01-database-1  Created
 Container epd2-pilot-01-database-1  Starting
 Container epd2-pilot-01-database-1  Started
  ok   postgres reports healthy, both databases initialised
 Container epd2-pilot-01-database-1  Running
 Container epd2-pilot-01-voting-1  Creating
 Container epd2-pilot-01-voting-1  Created
 Container epd2-pilot-01-runtime-1  Creating
 Container epd2-pilot-01-runtime-1  Created
 Container epd2-pilot-01-frontend-1  Creating
 Container epd2-pilot-01-frontend-1  Created
 Container epd2-pilot-01-database-1  Waiting
 Container epd2-pilot-01-database-1  Healthy
 Container epd2-pilot-01-voting-1  Starting
 Container epd2-pilot-01-voting-1  Started
 Container epd2-pilot-01-database-1  Waiting
 Container epd2-pilot-01-voting-1  Waiting
 Container epd2-pilot-01-database-1  Healthy
 Container epd2-pilot-01-voting-1  Healthy
 Container epd2-pilot-01-runtime-1  Starting
 Container epd2-pilot-01-runtime-1  Started
 Container epd2-pilot-01-runtime-1  Waiting
 Container epd2-pilot-01-runtime-1  Error
dependency failed to start: container epd2-pilot-01-runtime-1 is unhealthy
```

## Docker diagnostics (tail)
```text
## docker compose ps -a
NAME                       IMAGE                        COMMAND                  SERVICE    CREATED          STATUS                                  PORTS
epd2-pilot-01-database-1   postgres:16-alpine           "docker-entrypoint.s…"   database   14 seconds ago   Up 13 seconds (healthy)                 5432/tcp
epd2-pilot-01-frontend-1   epd2-pilot/frontend:0.51.0   "docker-entrypoint.s…"   frontend   7 seconds ago    Created                                 
epd2-pilot-01-runtime-1    epd2-pilot/runtime:0.51.0    "python -m epd2_runt…"   runtime    7 seconds ago    Restarting (1) Less than a second ago   
epd2-pilot-01-voting-1     epd2-pilot/voting:0.51.0     "python -m epd2_voti…"   voting     7 seconds ago    Up 6 seconds (healthy)                  0.0.0.0:8100->8100/tcp, [::]:8100->8100/tcp

## runtime inspect
[
    {
        "Id": "509c933f6dbd13c581edec6da343f2b5ab3646b7780d4df0588e601bc220e3f9",
        "Created": "2026-08-18T09:47:53.241830353Z",
        "Path": "python",
        "Args": [
            "-m",
            "epd2_runtime.pilot_server"
        ],
        "State": {
            "Status": "running",
            "Running": true,
            "Paused": false,
            "Restarting": false,
            "OOMKilled": false,
            "Dead": false,
            "Pid": 4346,
            "ExitCode": 0,
            "Error": "",
            "StartedAt": "2026-08-18T09:48:00.064058339Z",
            "FinishedAt": "2026-08-18T09:48:00.022170599Z",
            "Health": {
                "Status": "starting",
                "FailingStreak": 0,
                "Log": []
            }
        },
        "Image": "sha256:0d31cafe8076cd6ce117aca8e1f8e0dec594375dd99ec793e1ccf6bca7b32f0f",
        "ResolvConfPath": "/var/lib/docker/containers/509c933f6dbd13c581edec6da343f2b5ab3646b7780d4df0588e601bc220e3f9/resolv.conf",
        "HostnamePath": "/var/lib/docker/containers/509c933f6dbd13c581edec6da343f2b5ab3646b7780d4df0588e601bc220e3f9/hostname",
        "HostsPath": "/var/lib/docker/containers/509c933f6dbd13c581edec6da343f2b5ab3646b7780d4df0588e601bc220e3f9/hosts",
        "LogPath": "/var/lib/docker/containers/509c933f6dbd13c581edec6da343f2b5ab3646b7780d4df0588e601bc220e3f9/509c933f6dbd13c581edec6da343f2b5ab3646b7780d4df0588e601bc220e3f9-json.log",
        "Name": "/epd2-pilot-01-runtime-1",
        "RestartCount": 1,
        "Driver": "overlay2",
        "Platform": "linux",
        "MountLabel": "",
        "ProcessLabel": "",
        "AppArmorProfile": "docker-default",
        "ExecIDs": null,
        "HostConfig": {
            "Binds": null,
            "ContainerIDFile": "",
            "LogConfig": {
                "Type": "json-file",
                "Config": {}
            },
            "NetworkMode": "epd2-pilot-01_default",
            "PortBindings": {
                "8000/tcp": [
                    {
                        "HostIp": "",
                        "HostPort": "8000"
                    }
                ]
            },
            "RestartPolicy": {
                "Name": "unless-stopped",
                "MaximumRetryCount": 0
            },
            "AutoRemove": false,
            "VolumeDriver": "",
            "VolumesFrom": null,
            "ConsoleSize": [
                0,
                0
            ],
            "CapAdd": null,
            "CapDrop": [
                "ALL"
            ],
            "CgroupnsMode": "private",
            "Dns": null,
            "DnsOptions": null,
            "DnsSearch": null,
            "ExtraHosts": [],
            "GroupAdd": null,
            "IpcMode": "private",
            "Cgroup": "",
            "Links": null,
            "OomScoreAdj": 0,
            "PidMode": "",
            "Privileged": false,
            "PublishAllPorts": false,
            "ReadonlyRootfs": true,
            "SecurityOpt": [
                "no-new-privileges:true"
            ],
            "Tmpfs": {
                "/tmp": ""
            },
            "UTSMode": "",
            "UsernsMode": "",
            "ShmSize": 67108864,
            "Runtime": "runc",
            "Isolation": "",
            "CpuShares": 0,
            "Memory": 0,
            "NanoCpus": 0,
            "CgroupParent": "",
            "BlkioWeight": 0,
            "BlkioWeightDevice": null,
            "BlkioDeviceReadBps": null,
            "BlkioDeviceWriteBps": null,
            "BlkioDeviceReadIOps": null,
            "BlkioDeviceWriteIOps": null,
            "CpuPeriod": 0,
            "CpuQuota": 0,
            "CpuRealtimePeriod": 0,
            "CpuRealtimeRuntime": 0,
            "CpusetCpus": "",
            "CpusetMems": "",
            "Devices": null,
            "DeviceCgroupRules": null,
            "DeviceRequests": null,
            "MemoryReservation": 0,
            "MemorySwap": 0,
            "MemorySwappiness": null,
            "OomKillDisable": null,
            "PidsLimit": null,
            "Ulimits": null,
            "CpuCount": 0,
            "CpuPercent": 0,
            "IOMaximumIOps": 0,
            "IOMaximumBandwidth": 0,
            "MaskedPaths": [
                "/proc/asound",
                "/proc/acpi",
                "/proc/interrupts",
                "/proc/kcore",
                "/proc/keys",
                "/proc/latency_stats",
                "/proc/timer_list",
                "/proc/timer_stats",
                "/proc/sched_debug",
                "/proc/scsi",
                "/sys/firmware",
                "/sys/devices/virtual/powercap"
            ],
            "ReadonlyPaths": [
                "/proc/bus",
                "/proc/fs",
                "/proc/irq",
                "/proc/sys",
                "/proc/sysrq-trigger"
            ]
        },
        "GraphDriver": {
            "Data": {
                "ID": "509c933f6dbd13c581edec6da343f2b5ab3646b7780d4df0588e601bc220e3f9",
                "LowerDir": "/var/lib/docker/overlay2/5ddbe201d3e8364c196efc919c8f57403f2b211c37dee45389abbc3671378170-init/diff:/var/lib/docker/overlay2/01adnt39o67qqvg6s9r363fzv/diff:/var/lib/docker/overlay2/cq1kbxnn70m3fbgveoypsh7io/diff:/var/lib/docker/overlay2/y0y3zm0q8apwd4l4hdp92ttze/diff:/var/lib/docker/overlay2/ae19cd90000b976b89185f454f6859cbb4b1f732df486146dfdb0c13980e73d4/diff:/var/lib/docker/overlay2/971f3e95e2129ec8be2de58b39993580cd04d82acd8e4a7078b1bc48bc7b5bfb/diff:/var/lib/docker/overlay2/71d6b434e0cf6e826a12a62ed82b7a6a0224921d8f2bebcbe3c7792aacedfb91/diff:/var/lib/docker/overlay2/d30d4a1f162cab026e4aff28aa58f0d3b2f757d3ca4d34d4dd74f6e11c6d7625/diff",
                "MergedDir": "/var/lib/docker/overlay2/5ddbe201d3e8364c196efc919c8f57403f2b211c37dee45389abbc3671378170/merged",
                "UpperDir": "/var/lib/docker/overlay2/5ddbe201d3e8364c196efc919c8f57403f2b211c37dee45389abbc3671378170/diff",
                "WorkDir": "/var/lib/docker/overlay2/5ddbe201d3e8364c196efc919c8f57403f2b211c37dee45389abbc3671378170/work"
            },
            "Name": "overlay2"
        },
        "Mounts": [],
        "Config": {
            "Hostname": "509c933f6dbd",
            "Domainname": "",
            "User": "epd2",
            "AttachStdin": false,
            "AttachStdout": true,
            "AttachStderr": true,
            "ExposedPorts": {
                "8000/tcp": {}
            },
            "Tty": false,
            "OpenStdin": false,
            "StdinOnce": false,
            "Env": [
                "EPD2_SESSION_COOKIE_SAMESITE=Lax",
                "EPD2_BIND_HOST=0.0.0.0",
                "EPD2_PUBLIC_BASE_URL=http://127.0.0.1:8000",
                "EPD2_CSRF_PROTECTION=1",
                "EPD2_VOTING_SERVICE_TOKEN=aaf99ba144f8a2afc3b50d804e1f1ddc95d530d99e93bfab47c0ecfe8300fb08",
                "EPD2_SESSION_COOKIE_SECURE=0",
                "EPD2_ALLOWED_ORIGINS=http://127.0.0.1:3000",
                "EPD2_LOG_LEVEL=INFO",
                "EPD2_BIND_PORT=8000",
                "EPD2_SESSION_COOKIE_HTTPONLY=1",
                "EPD2_VOTING_BOUNDARY_PUBLIC_URL=http://localhost:8100",
                "EPD2_RATE_LIMIT_ENABLED=1",
                "EPD2_AUTHENTICATION=LOCAL_SESSION",
                "EPD2_PERSISTENCE=POSTGRESQL",
                "EPD2_VOTING_BOUNDARY_URL=http://voting:8100",
                "EPD2_MIGRATE_ON_START=1",
                "EPD2_PROFILE=DEVELOPMENT",
                "EPD2_AUDIT_REQUIRED=1",
                "EPD2_DATABASE_URL=postgresql://epd2_pilot:8706123ebfa87a8852d75becac6dbb97d62a94fbbb32f6f3@database:5432/epd2_pilot",
                "PATH=/srv/epd2/.venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "LANG=C.UTF-8",
                "GPG_KEY=7169605F62C751356D054A26A821E680E5FA6305",
                "PYTHON_VERSION=3.12.14",
                "PYTHON_SHA256=5c8462af5790baf43a321a1559dbe0db06d1be4300fb85fb53c40060668e548a",
                "PYTHONDONTWRITEBYTECODE=1",
                "PYTHONUNBUFFERED=1"
            ],
            "Cmd": [
                "python",
                "-m",
                "epd2_runtime.pilot_server"
            ],
            "Healthcheck": {
                "Test": [
                    "CMD-SHELL",
                    "python -c \"import sys,urllib.request;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/ready',timeout=4).status==200 else 1)\""
                ],
                "Interval": 10000000000,
                "Timeout": 5000000000,
                "StartPeriod": 40000000000,
                "Retries": 6
            },
            "Image": "epd2-pilot/runtime:0.51.0",
            "Volumes": null,
            "WorkingDir": "/srv/epd2",
            "Entrypoint": null,
            "OnBuild": null,
            "Labels": {
                "com.docker.compose.config-hash": "991ce882b817d74cb2fc1ead82ec806251bb1e97d7aec9a354d5c21883322478",
                "com.docker.compose.container-number": "1",
                "com.docker.compose.depends_on": "database:service_healthy:false,voting:service_healthy:false",
                "com.docker.compose.image": "sha256:0d31cafe8076cd6ce117aca8e1f8e0dec594375dd99ec793e1ccf6bca7b32f0f",
                "com.docker.compose.oneoff": "False",
                "com.docker.compose.project": "epd2-pilot-01",
                "com.docker.compose.project.config_files": "/tmp/pilot02-candidate/EPD2_PILOT-02_PUBLIC_SITE_INTEGRATION_AND_UNIFIED_PILOT_PRODUCT_CANDIDATE_0.51.0/deploy/pilot/compose.yaml",
                "com.docker.compose.project.environment_file": "/tmp/pilot02-candidate/EPD2_PILOT-02_PUBLIC_SITE_INTEGRATION_AND_UNIFIED_PILOT_PRODUCT_CANDIDATE_0.51.0/deploy/pilot/.env",
                "com.docker.compose.project.working_dir": "/tmp/pilot02-candidate/EPD2_PILOT-02_PUBLIC_SITE_INTEGRATION_AND_UNIFIED_PILOT_PRODUCT_CANDIDATE_0.51.0/deploy/pilot",
                "com.docker.compose.service": "runtime",
                "com.docker.compose.version": "2.38.2"
            },
            "StopSignal": "SIGTERM",
            "StopTimeout": 30
        },
        "NetworkSettings": {
            "Bridge": "",
            "SandboxID": "9cbefe3f4559fa7680c47987fe22e639057482541a353c04264975999f165aed",
            "SandboxKey": "/var/run/docker/netns/9cbefe3f4559",
            "Ports": {
                "8000/tcp": [
                    {
                        "HostIp": "0.0.0.0",
                        "HostPort": "8000"
                    },
                    {
                        "HostIp": "::",
                        "HostPort": "8000"
                    }
                ]
            },
            "HairpinMode": false,
            "LinkLocalIPv6Address": "",
            "LinkLocalIPv6PrefixLen": 0,
            "SecondaryIPAddresses": null,
            "SecondaryIPv6Addresses": null,
            "EndpointID": "",
            "Gateway": "",
            "GlobalIPv6Address": "",
            "GlobalIPv6PrefixLen": 0,
            "IPAddress": "",
            "IPPrefixLen": 0,
            "IPv6Gateway": "",
            "MacAddress": "",
            "Networks": {
                "epd2-pilot-01_default": {
                    "IPAMConfig": null,
                    "Links": null,
                    "Aliases": [
                        "epd2-pilot-01-runtime-1",
                        "runtime"
                    ],
                    "MacAddress": "d2:6b:6c:38:d7:9f",
                    "DriverOpts": null,
                    "GwPriority": 0,
                    "NetworkID": "c25383292c16948ed765acb2ea18259a259dfe1a811e1482e0e756594c949149",
                    "EndpointID": "42da063176207542d6240764d42ebaecee4606b69bf0cd4e08979f7abd326e38",
                    "Gateway": "172.18.0.1",
                    "IPAddress": "172.18.0.4",
                    "IPPrefixLen": 16,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "DNSNames": [
                        "epd2-pilot-01-runtime-1",
                        "runtime",
                        "509c933f6dbd"
                    ]
                }
            }
        }
    }
]

## runtime logs
runtime-1  | 2026-08-18T09:47:59.915763866Z Traceback (most recent call last):
runtime-1  | 2026-08-18T09:47:59.915816535Z   File "<frozen runpy>", line 198, in _run_module_as_main
runtime-1  | 2026-08-18T09:47:59.915822303Z   File "<frozen runpy>", line 88, in _run_code
runtime-1  | 2026-08-18T09:47:59.915826790Z   File "/srv/epd2/packages/python/epd2-runtime/src/epd2_runtime/pilot_server.py", line 24, in <module>
runtime-1  | 2026-08-18T09:47:59.915832458Z     from epd2_runtime.pilot.composition import build_pilot_runtime
runtime-1  | 2026-08-18T09:47:59.915835533Z   File "/srv/epd2/packages/python/epd2-runtime/src/epd2_runtime/pilot/composition.py", line 51, in <module>
runtime-1  | 2026-08-18T09:47:59.915939858Z     from epd2_runtime.pilot.stores import (
runtime-1  | 2026-08-18T09:47:59.915949742Z   File "/srv/epd2/packages/python/epd2-runtime/src/epd2_runtime/pilot/stores.py", line 21, in <module>
runtime-1  | 2026-08-18T09:47:59.916028234Z     from epd2_account_service.domain import Account
runtime-1  | 2026-08-18T09:47:59.916033562Z ModuleNotFoundError: No module named 'epd2_account_service'

## voting logs

## database logs (tail 200)
database-1  | 2026-08-18T09:47:46.873821512Z The files belonging to this database system will be owned by user "postgres".
database-1  | 2026-08-18T09:47:46.873900088Z This user must also own the server process.
database-1  | 2026-08-18T09:47:46.873905226Z 
database-1  | 2026-08-18T09:47:46.873909122Z The database cluster will be initialized with locale "en_US.utf8".
database-1  | 2026-08-18T09:47:46.873912898Z The default database encoding has accordingly been set to "UTF8".
database-1  | 2026-08-18T09:47:46.873916573Z The default text search configuration will be set to "english".
database-1  | 2026-08-18T09:47:46.873920188Z 
database-1  | 2026-08-18T09:47:46.873923423Z Data page checksums are disabled.
database-1  | 2026-08-18T09:47:46.873926828Z 
database-1  | 2026-08-18T09:47:46.873930394Z fixing permissions on existing directory /var/lib/postgresql/data ... ok
database-1  | 2026-08-18T09:47:46.873934199Z creating subdirectories ... ok
database-1  | 2026-08-18T09:47:46.873973237Z selecting dynamic shared memory implementation ... posix
database-1  | 2026-08-18T09:47:46.898999387Z selecting default max_connections ... 100
database-1  | 2026-08-18T09:47:46.925403088Z selecting default shared_buffers ... 128MB
database-1  | 2026-08-18T09:47:46.969097748Z selecting default time zone ... UTC
database-1  | 2026-08-18T09:47:46.969990405Z creating configuration files ... ok
database-1  | 2026-08-18T09:47:47.103438978Z running bootstrap script ... ok
database-1  | 2026-08-18T09:47:47.307158049Z sh: locale: not found
database-1  | 2026-08-18T09:47:47.307230362Z 2026-08-18 09:47:47.307 UTC [35] WARNING:  no usable system locales were found
database-1  | 2026-08-18T09:47:47.756602121Z performing post-bootstrap initialization ... ok
database-1  | 2026-08-18T09:47:47.787020860Z syncing data to disk ... ok
database-1  | 2026-08-18T09:47:47.787047580Z 
database-1  | 2026-08-18T09:47:47.787051906Z 
database-1  | 2026-08-18T09:47:47.787056072Z Success. You can now start the database server using:
database-1  | 2026-08-18T09:47:47.787060238Z 
database-1  | 2026-08-18T09:47:47.787063543Z     pg_ctl -D /var/lib/postgresql/data -l logfile start
database-1  | 2026-08-18T09:47:47.787066388Z 
database-1  | 2026-08-18T09:47:47.787025687Z initdb: warning: enabling "trust" authentication for local connections
database-1  | 2026-08-18T09:47:47.787073218Z initdb: hint: You can change this by editing pg_hba.conf or using the option -A, or --auth-local and --auth-host, the next time you run initdb.
database-1  | 2026-08-18T09:47:47.827564988Z waiting for server to start....2026-08-18 09:47:47.827 UTC [41] LOG:  starting PostgreSQL 16.15 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
database-1  | 2026-08-18T09:47:47.828048737Z 2026-08-18 09:47:47.827 UTC [41] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
database-1  | 2026-08-18T09:47:47.830268085Z 2026-08-18 09:47:47.830 UTC [44] LOG:  database system was shut down at 2026-08-18 09:47:47 UTC
database-1  | 2026-08-18T09:47:47.834185316Z 2026-08-18 09:47:47.834 UTC [41] LOG:  database system is ready to accept connections
database-1  | 2026-08-18T09:47:47.908727876Z  done
database-1  | 2026-08-18T09:47:47.908754937Z server started
database-1  | 2026-08-18T09:47:47.974173339Z CREATE DATABASE
database-1  | 2026-08-18T09:47:47.974683462Z 
database-1  | 2026-08-18T09:47:47.974834511Z 
database-1  | 2026-08-18T09:47:47.974884325Z /usr/local/bin/docker-entrypoint.sh: running /docker-entrypoint-initdb.d/01-voting-database.sh
database-1  | 2026-08-18T09:47:48.019525973Z CREATE DATABASE
database-1  | 2026-08-18T09:47:48.019982902Z created epd2_pilot_voting
database-1  | 2026-08-18T09:47:48.020070162Z 
database-1  | 2026-08-18T09:47:48.020921547Z waiting for server to shut down...2026-08-18 09:47:48.020 UTC [41] LOG:  received fast shutdown request
database-1  | 2026-08-18T09:47:48.021466377Z .2026-08-18 09:47:48.021 UTC [41] LOG:  aborting any active transactions
database-1  | 2026-08-18T09:47:48.025555279Z 2026-08-18 09:47:48.025 UTC [41] LOG:  background worker "logical replication launcher" (PID 47) exited with exit code 1
database-1  | 2026-08-18T09:47:48.026025713Z 2026-08-18 09:47:48.025 UTC [42] LOG:  shutting down
database-1  | 2026-08-18T09:47:48.026317857Z 2026-08-18 09:47:48.026 UTC [42] LOG:  checkpoint starting: shutdown immediate
database-1  | 2026-08-18T09:47:48.057845144Z 2026-08-18 09:47:48.057 UTC [42] LOG:  checkpoint complete: wrote 1846 buffers (11.3%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.029 s, sync=0.003 s, total=0.032 s; sync files=597, longest=0.001 s, average=0.001 s; distance=8565 kB, estimate=8565 kB; lsn=0/1D545D8, redo lsn=0/1D545D8
database-1  | 2026-08-18T09:47:48.066898159Z 2026-08-18 09:47:48.066 UTC [41] LOG:  database system is shut down
database-1  | 2026-08-18T09:47:48.121243576Z  done
database-1  | 2026-08-18T09:47:48.121264978Z server stopped
database-1  | 2026-08-18T09:47:48.122228080Z 
database-1  | 2026-08-18T09:47:48.122241029Z PostgreSQL init process complete; ready for start up.
database-1  | 2026-08-18T09:47:48.122245095Z 
database-1  | 2026-08-18T09:47:48.143782830Z 2026-08-18 09:47:48.143 UTC [1] LOG:  starting PostgreSQL 16.15 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
database-1  | 2026-08-18T09:47:48.143849389Z 2026-08-18 09:47:48.143 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
database-1  | 2026-08-18T09:47:48.143854677Z 2026-08-18 09:47:48.143 UTC [1] LOG:  listening on IPv6 address "::", port 5432
database-1  | 2026-08-18T09:47:48.144640660Z 2026-08-18 09:47:48.144 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
database-1  | 2026-08-18T09:47:48.147263573Z 2026-08-18 09:47:48.147 UTC [62] LOG:  database system was shut down at 2026-08-18 09:47:48 UTC
database-1  | 2026-08-18T09:47:48.159374393Z 2026-08-18 09:47:48.159 UTC [1] LOG:  database system is ready to accept connections

## frontend logs
```
