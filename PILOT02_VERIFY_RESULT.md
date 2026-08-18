# PILOT-02 Docker Verification Result

**Verdict:** NOT VERIFIED — PILOT-02 product smoke failed

- Workflow run: 32121752488
- Commit: 9541e94c99e70ebe12af839086ac47ec5540a59d
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
lrwxrwxrwx 1 root root 13 Aug 18 09:26 /dev/fd -> /proc/self/fd
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
#22 [voting] resolving provenance for metadata file
#22 DONE 0.0s
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
#3 DONE 0.0s

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

#8 [runtime build 3/9] WORKDIR /srv/epd2
#8 CACHED

#9 [runtime build 5/9] COPY packages ./packages
#9 CACHED

#10 [runtime build 6/9] COPY services ./services
#10 CACHED

#11 [runtime build 7/9] COPY contracts ./contracts
#11 CACHED

#12 [runtime build 4/9] COPY pyproject.toml uv.lock ./
#12 CACHED

#13 [runtime build 2/9] COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /usr/local/bin/uv
#13 CACHED

#14 [runtime build 8/9] COPY conftest.py ./
#14 CACHED

#15 [runtime runtime 2/4] RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin epd2
#15 0.173 useradd warning: epd2's uid 10001 is greater than SYS_UID_MAX 999
#15 DONE 0.2s

#16 [runtime runtime 3/4] WORKDIR /srv/epd2
#16 DONE 0.0s

#17 [runtime build 9/9] RUN uv sync --frozen --no-dev --package epd2-runtime
#17 0.317 Using CPython 3.12.14 interpreter at: /usr/local/bin/python3
#17 0.317 Creating virtual environment at: .venv
#17 0.333    Building epd2-runtime @ file:///srv/epd2/packages/python/epd2-runtime
#17 0.333    Building epd2-audit-core @ file:///srv/epd2/services/audit-core
#17 0.333    Building epd2-citizen-office-routing-service @ file:///srv/epd2/services/citizen-office-routing-service
#17 0.334    Building epd2-core @ file:///srv/epd2/packages/python/epd2-core
#17 0.359 Downloading psycopg-binary (4.9MiB)
#17 0.360 Downloading pydantic-core (2.0MiB)
#17 0.546  Downloading pydantic-core
#17 0.565  Downloading psycopg-binary
#17 1.916       Built epd2-core @ file:///srv/epd2/packages/python/epd2-core
#17 1.916       Built epd2-runtime @ file:///srv/epd2/packages/python/epd2-runtime
#17 1.918       Built epd2-citizen-office-routing-service @ file:///srv/epd2/services/citizen-office-routing-service
#17 1.925       Built epd2-audit-core @ file:///srv/epd2/services/audit-core
#17 1.926 Prepared 25 packages in 1.60s
#17 1.964 Installed 25 packages in 37ms
#17 2.557 Bytecode compiled 478 files in 592ms
#17 2.557  + annotated-doc==0.0.5
#17 2.557  + annotated-types==0.7.0
#17 2.557  + anyio==4.14.2
#17 2.557  + argon2-cffi==25.1.0
#17 2.557  + argon2-cffi-bindings==25.1.0
#17 2.557  + cffi==2.1.0
#17 2.557  + click==8.4.2
#17 2.557  + epd2-audit-core==0.1.0 (from file:///srv/epd2/services/audit-core)
#17 2.557  + epd2-citizen-office-routing-service==0.1.0 (from file:///srv/epd2/services/citizen-office-routing-service)
#17 2.557  + epd2-core==0.1.0 (from file:///srv/epd2/packages/python/epd2-core)
#17 2.557  + epd2-runtime==0.1.0 (from file:///srv/epd2/packages/python/epd2-runtime)
#17 2.557  + fastapi==0.141.1
#17 2.557  + h11==0.16.0
#17 2.557  + idna==3.18
#17 2.557  + psycopg==3.3.4
#17 2.557  + psycopg-binary==3.3.4
#17 2.557  + psycopg-pool==3.3.1
#17 2.557  + pycparser==3.0
#17 2.557  + pydantic==2.13.4
#17 2.557  + pydantic-core==2.46.4
#17 2.557  + pyyaml==6.0.3
#17 2.558  + starlette==1.6.0
#17 2.558  + typing-extensions==4.16.0
#17 2.558  + typing-inspection==0.4.2
#17 2.558  + uvicorn==0.52.3
#17 DONE 2.7s

#18 [runtime runtime 4/4] COPY --from=build --chown=epd2:epd2 /srv/epd2 /srv/epd2
#18 DONE 0.4s

#19 [runtime] exporting to image
#19 exporting layers
#19 exporting layers 0.7s done
#19 writing image sha256:aabf7e920ee40b52bffc37c3f0cfc04ad0e01e261a632dabd81552f1fd1776bf done
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
 f0e7204f9584 Waiting 
 8225e2970a7f Waiting 
 48d0d8b0e136 Waiting 
 27d0ba4f668a Waiting 
 b053c4426c4a Waiting 
 7f5de3d007ea Waiting 
 be6f407f5414 Waiting 
 19a2a5ab27c1 Downloading [>                                                  ]  15.79kB/900.3kB
 6a47e1b9b254 Downloading [==================================================>]     969B/969B
 6a47e1b9b254 Verifying Checksum 
 6a47e1b9b254 Download complete 
 6a47e1b9b254 Extracting [==================================================>]     969B/969B
 6a47e1b9b254 Extracting [==================================================>]     969B/969B
 5e81018bec01 Downloading [==================================================>]     172B/172B
 5e81018bec01 Verifying Checksum 
 5e81018bec01 Download complete 
 19a2a5ab27c1 Download complete 
 6a47e1b9b254 Pull complete 
 19a2a5ab27c1 Extracting [=>                                                 ]  32.77kB/900.3kB
 be6f407f5414 Downloading [==================================================>]     116B/116B
 be6f407f5414 Verifying Checksum 
 be6f407f5414 Download complete 
 8225e2970a7f Downloading [==================>                                ]  3.502kB/9.673kB
 8225e2970a7f Downloading [==================================================>]  9.673kB/9.673kB
 8225e2970a7f Verifying Checksum 
 8225e2970a7f Download complete 
 f0e7204f9584 Downloading [>                                                  ]  540.7kB/111.3MB
 19a2a5ab27c1 Extracting [==================================================>]  900.3kB/900.3kB
 48d0d8b0e136 Downloading [==================================================>]     129B/129B
 48d0d8b0e136 Verifying Checksum 
 48d0d8b0e136 Download complete 
 19a2a5ab27c1 Pull complete 
 5e81018bec01 Extracting [==================================================>]     172B/172B
 5e81018bec01 Extracting [==================================================>]     172B/172B
 27d0ba4f668a Downloading [==================================================>]     169B/169B
 27d0ba4f668a Verifying Checksum 
 27d0ba4f668a Download complete 
 5e81018bec01 Pull complete 
 be6f407f5414 Extracting [==================================================>]     116B/116B
 be6f407f5414 Extracting [==================================================>]     116B/116B
 b053c4426c4a Downloading [============================>                      ]  3.502kB/6.112kB
 b053c4426c4a Downloading [==================================================>]  6.112kB/6.112kB
 b053c4426c4a Verifying Checksum 
 b053c4426c4a Download complete 
 7f5de3d007ea Downloading [==================================================>]     185B/185B
 7f5de3d007ea Verifying Checksum 
 7f5de3d007ea Download complete 
 be6f407f5414 Pull complete 
 f0e7204f9584 Downloading [============>                                      ]  26.94MB/111.3MB
 f0e7204f9584 Downloading [==========================>                        ]  59.25MB/111.3MB
 f0e7204f9584 Downloading [========================================>          ]  91.02MB/111.3MB
 f0e7204f9584 Verifying Checksum 
 f0e7204f9584 Download complete 
 f0e7204f9584 Extracting [>                                                  ]  557.1kB/111.3MB
 f0e7204f9584 Extracting [==>                                                ]  5.014MB/111.3MB
 f0e7204f9584 Extracting [======>                                            ]  14.48MB/111.3MB
 f0e7204f9584 Extracting [==========>                                        ]  23.95MB/111.3MB
 f0e7204f9584 Extracting [===============>                                   ]  33.42MB/111.3MB
 f0e7204f9584 Extracting [===================>                               ]  42.89MB/111.3MB
 f0e7204f9584 Extracting [=======================>                           ]  52.36MB/111.3MB
 f0e7204f9584 Extracting [==========================>                        ]  57.93MB/111.3MB
 f0e7204f9584 Extracting [=============================>                     ]  65.18MB/111.3MB
 f0e7204f9584 Extracting [=================================>                 ]  74.09MB/111.3MB
 f0e7204f9584 Extracting [====================================>              ]  81.33MB/111.3MB
 f0e7204f9584 Extracting [=====================================>             ]  82.44MB/111.3MB
 f0e7204f9584 Extracting [======================================>            ]  85.23MB/111.3MB
 f0e7204f9584 Extracting [========================================>          ]  89.69MB/111.3MB
 f0e7204f9584 Extracting [==========================================>        ]  94.14MB/111.3MB
 f0e7204f9584 Extracting [============================================>      ]  98.04MB/111.3MB
 f0e7204f9584 Extracting [================================================>  ]  108.6MB/111.3MB
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
