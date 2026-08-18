# PILOT-02 Docker Verification Result

**Verdict:** NOT VERIFIED — PILOT-02 product smoke failed

- Workflow run: 32130216749
- Commit: 45ff4ab6380af42501492537e8ad252ced4e3aef
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
lrwxrwxrwx 1 root root 13 Aug 18 11:05 /dev/fd -> /proc/self/fd
process-substitution-ok
```

## Integrity log (tail)
```text
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
tests/repository/test_pilot02c3_runtime_import_closure.py: OK
tests/repository/test_prod01_runtime_spine.py: OK
tests/repository/test_required_files.py: OK
tests/repository/test_service_boundaries.py: OK
tests/repository/test_system_wide_corrective_closure.py: OK
tests/repository/test_version_consistency.py: OK
uv.lock: OK
```

## Product smoke log (tail)
```text
#6 [runtime build 1/9] FROM docker.io/library/python:3.12-slim@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a
#6 CACHED

#7 [runtime internal] load build context
#7 transferring context: 148.71kB 0.1s done
#7 DONE 0.1s

#8 [runtime build 2/9] COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /usr/local/bin/uv
#8 CACHED

#9 [runtime build 4/9] COPY pyproject.toml uv.lock ./
#9 CACHED

#10 [runtime build 6/9] COPY services ./services
#10 CACHED

#11 [runtime build 7/9] COPY contracts ./contracts
#11 CACHED

#12 [runtime build 5/9] COPY packages ./packages
#12 CACHED

#13 [runtime build 3/9] WORKDIR /srv/epd2
#13 CACHED

#14 [runtime build 8/9] COPY conftest.py ./
#14 CACHED

#15 [runtime runtime 2/4] RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin epd2
#15 0.182 useradd warning: epd2's uid 10001 is greater than SYS_UID_MAX 999
#15 DONE 0.2s

#16 [runtime build 9/9] RUN uv sync --frozen --no-dev --package epd2-runtime
#16 ...

#17 [runtime runtime 3/4] WORKDIR /srv/epd2
#17 DONE 0.0s

#16 [runtime build 9/9] RUN uv sync --frozen --no-dev --package epd2-runtime
#16 0.342 Using CPython 3.12.14 interpreter at: /usr/local/bin/python3
#16 0.342 Creating virtual environment at: .venv
#16 0.358    Building epd2-deliberation-service @ file:///srv/epd2/services/deliberation-service
#16 0.359    Building epd2-runtime @ file:///srv/epd2/packages/python/epd2-runtime
#16 0.360    Building epd2-account-service @ file:///srv/epd2/services/account-service
#16 0.360    Building epd2-audit-core @ file:///srv/epd2/services/audit-core
#16 0.361    Building epd2-citizen-office-routing-service @ file:///srv/epd2/services/citizen-office-routing-service
#16 0.361    Building epd2-core @ file:///srv/epd2/packages/python/epd2-core
#16 0.362    Building epd2-membership-service @ file:///srv/epd2/services/membership-service
#16 0.454 Downloading psycopg-binary (4.9MiB)
#16 0.455 Downloading pydantic-core (2.0MiB)
#16 0.650  Downloading pydantic-core
#16 0.691  Downloading psycopg-binary
#16 2.425       Built epd2-account-service @ file:///srv/epd2/services/account-service
#16 2.722       Built epd2-runtime @ file:///srv/epd2/packages/python/epd2-runtime
#16 2.859       Built epd2-audit-core @ file:///srv/epd2/services/audit-core
#16 2.907       Built epd2-citizen-office-routing-service @ file:///srv/epd2/services/citizen-office-routing-service
#16 2.917       Built epd2-core @ file:///srv/epd2/packages/python/epd2-core
#16 3.061       Built epd2-membership-service @ file:///srv/epd2/services/membership-service
#16 3.085       Built epd2-deliberation-service @ file:///srv/epd2/services/deliberation-service
#16 3.086 Prepared 28 packages in 2.73s
#16 3.136 Installed 28 packages in 49ms
#16 3.702 Bytecode compiled 478 files in 566ms
#16 3.702  + annotated-doc==0.0.5
#16 3.702  + annotated-types==0.7.0
#16 3.702  + anyio==4.14.2
#16 3.702  + argon2-cffi==25.1.0
#16 3.702  + argon2-cffi-bindings==25.1.0
#16 3.703  + cffi==2.1.0
#16 3.703  + click==8.4.2
#16 3.703  + epd2-account-service==0.1.0 (from file:///srv/epd2/services/account-service)
#16 3.703  + epd2-audit-core==0.1.0 (from file:///srv/epd2/services/audit-core)
#16 3.703  + epd2-citizen-office-routing-service==0.1.0 (from file:///srv/epd2/services/citizen-office-routing-service)
#16 3.703  + epd2-core==0.1.0 (from file:///srv/epd2/packages/python/epd2-core)
#16 3.703  + epd2-deliberation-service==0.1.0 (from file:///srv/epd2/services/deliberation-service)
#16 3.703  + epd2-membership-service==0.1.0 (from file:///srv/epd2/services/membership-service)
#16 3.703  + epd2-runtime==0.1.0 (from file:///srv/epd2/packages/python/epd2-runtime)
#16 3.703  + fastapi==0.141.1
#16 3.703  + h11==0.16.0
#16 3.703  + idna==3.18
#16 3.703  + psycopg==3.3.4
#16 3.703  + psycopg-binary==3.3.4
#16 3.703  + psycopg-pool==3.3.1
#16 3.703  + pycparser==3.0
#16 3.703  + pydantic==2.13.4
#16 3.703  + pydantic-core==2.46.4
#16 3.703  + pyyaml==6.0.3
#16 3.704  + starlette==1.6.0
#16 3.704  + typing-extensions==4.16.0
#16 3.704  + typing-inspection==0.4.2
#16 3.704  + uvicorn==0.52.3
#16 DONE 3.8s

#18 [runtime runtime 4/4] COPY --from=build --chown=epd2:epd2 /srv/epd2 /srv/epd2
#18 DONE 0.4s

#19 [runtime] exporting to image
#19 exporting layers
#19 exporting layers 0.7s done
#19 writing image sha256:7a50b4de114371245df6d8efaa2adf461cd6658ba37a7ffff8028bf2b6c64059 done
#19 naming to docker.io/epd2-pilot/runtime:0.51.1 done
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
 19a2a5ab27c1 Downloading [>                                                  ]  15.79kB/900.3kB
 6a47e1b9b254 Downloading [==================================================>]     969B/969B
 6a47e1b9b254 Verifying Checksum 
 6a47e1b9b254 Download complete 
 6a47e1b9b254 Extracting [==================================================>]     969B/969B
 6a47e1b9b254 Extracting [==================================================>]     969B/969B
 6a47e1b9b254 Pull complete 
 19a2a5ab27c1 Downloading [==================================================>]  900.3kB/900.3kB
 19a2a5ab27c1 Verifying Checksum 
 19a2a5ab27c1 Download complete 
 19a2a5ab27c1 Extracting [=>                                                 ]  32.77kB/900.3kB
 19a2a5ab27c1 Extracting [==================================================>]  900.3kB/900.3kB
 19a2a5ab27c1 Extracting [==================================================>]  900.3kB/900.3kB
 19a2a5ab27c1 Pull complete 
 5e81018bec01 Extracting [==================================================>]     172B/172B
 5e81018bec01 Extracting [==================================================>]     172B/172B
 5e81018bec01 Pull complete 
 be6f407f5414 Downloading [==================================================>]     116B/116B
 be6f407f5414 Verifying Checksum 
 be6f407f5414 Download complete 
 be6f407f5414 Extracting [==================================================>]     116B/116B
 be6f407f5414 Extracting [==================================================>]     116B/116B
 be6f407f5414 Pull complete 
 f0e7204f9584 Downloading [>                                                  ]  534.1kB/111.3MB
 8225e2970a7f Verifying Checksum 
 8225e2970a7f Download complete 
 f0e7204f9584 Downloading [==>                                                ]  5.331MB/111.3MB
 48d0d8b0e136 Downloading [==================================================>]     129B/129B
 48d0d8b0e136 Verifying Checksum 
 48d0d8b0e136 Download complete 
 f0e7204f9584 Downloading [=============>                                     ]   29.9MB/111.3MB
 27d0ba4f668a Downloading [==================================================>]     169B/169B
 27d0ba4f668a Verifying Checksum 
 27d0ba4f668a Download complete 
 f0e7204f9584 Downloading [=============================>                     ]  64.62MB/111.3MB
 b053c4426c4a Downloading [============================>                      ]  3.502kB/6.112kB
 b053c4426c4a Downloading [==================================================>]  6.112kB/6.112kB
 b053c4426c4a Verifying Checksum 
 b053c4426c4a Download complete 
 f0e7204f9584 Downloading [============================================>      ]  99.73MB/111.3MB
 7f5de3d007ea Downloading [==================================================>]     185B/185B
 7f5de3d007ea Verifying Checksum 
 7f5de3d007ea Download complete 
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
 f0e7204f9584 Extracting [==============================>                    ]  66.85MB/111.3MB
 f0e7204f9584 Extracting [=================================>                 ]  74.65MB/111.3MB
 f0e7204f9584 Extracting [====================================>              ]  81.33MB/111.3MB
 f0e7204f9584 Extracting [=====================================>             ]  82.44MB/111.3MB
 f0e7204f9584 Extracting [======================================>            ]  85.23MB/111.3MB
 f0e7204f9584 Extracting [========================================>          ]  89.69MB/111.3MB
 f0e7204f9584 Extracting [==========================================>        ]  93.59MB/111.3MB
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
 Container epd2-pilot-01-runtime-1  Healthy
 Container epd2-pilot-01-frontend-1  Starting
 Container epd2-pilot-01-frontend-1  Started
pilot-member-1   created  role=member  account=93fae520-3707-5aca-a944-b9492d6dae1f
pilot-member-2   created  role=member  account=b8298540-11d9-5f8f-b086-2e7729e84dde
pilot-member-3   created  role=member  account=607f623b-3bc8-51ca-a8a0-651e05fc6954
pilot-operator   created  role=PILOT_OPERATOR  account=e5f5631b-1ee6-5815-bcb6-3b7302f7205d
PILOT FIXTURES OK
  ok   voting boundary reports ready
  ok   member runtime reports ready
  FAIL frontend reachable did not become available
```

## Docker diagnostics (tail)
```text
frontend-1  | 2026-08-18T11:31:54.771190169Z npm notice
frontend-1  | 2026-08-18T11:31:54.771212251Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:31:54.771217529Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:31:54.771221996Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:31:54.771225731Z npm notice
frontend-1  | 2026-08-18T11:31:55.990111169Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:31:55.990302292Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:31:55.990352536Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:31:55.990484382Z 
frontend-1  | 2026-08-18T11:31:55.990506144Z  ✓ Starting...
frontend-1  | 2026-08-18T11:31:56.086303450Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:31:56.296083557Z 
frontend-1  | 2026-08-18T11:31:56.296116385Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:31:56.296145949Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:31:56.296371028Z 
frontend-1  | 2026-08-18T11:31:56.440762878Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:31:56.453088191Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:31:56.453109202Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:31:56.455241774Z info No lockfile found.
frontend-1  | 2026-08-18T11:31:56.470834971Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:31:59.510932552Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:32:12.323540642Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:32:12.324830354Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:32:12.355323692Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:32:12.355352380Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:32:12.393675663Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:32:12.393724376Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:32:12.393728912Z 
frontend-1  | 2026-08-18T11:32:12.393752537Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:32:12.393995968Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:32:12.404311976Z npm notice
frontend-1  | 2026-08-18T11:32:12.404333498Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:32:12.404338715Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:32:12.404342932Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:32:12.404346737Z npm notice
frontend-1  | 2026-08-18T11:32:13.639678735Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:32:13.639961314Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:32:13.639975425Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:32:13.640055294Z 
frontend-1  | 2026-08-18T11:32:13.640064547Z  ✓ Starting...
frontend-1  | 2026-08-18T11:32:13.736471299Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:32:13.956029311Z 
frontend-1  | 2026-08-18T11:32:13.956066005Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:32:13.956071914Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:32:13.956340583Z 
frontend-1  | 2026-08-18T11:32:14.092459044Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:32:14.104722943Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:32:14.104738306Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:32:14.106845903Z info No lockfile found.
frontend-1  | 2026-08-18T11:32:14.122413424Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:32:17.757280392Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:32:30.481718392Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:32:30.483079735Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:32:30.511798847Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:32:30.511798421Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:32:30.553348701Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:32:30.553387719Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:32:30.553393939Z 
frontend-1  | 2026-08-18T11:32:30.553416647Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:32:30.553643600Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:32:30.563947276Z npm notice
frontend-1  | 2026-08-18T11:32:30.563984712Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:32:30.563989890Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:32:30.563993946Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:32:30.563997831Z npm notice
frontend-1  | 2026-08-18T11:32:31.781246238Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:32:31.781418463Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:32:31.781429069Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:32:31.781579252Z 
frontend-1  | 2026-08-18T11:32:31.781590188Z  ✓ Starting...
frontend-1  | 2026-08-18T11:32:31.875913089Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:32:32.087928472Z 
frontend-1  | 2026-08-18T11:32:32.087959578Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:32:32.087985276Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:32:32.088201327Z 
frontend-1  | 2026-08-18T11:32:32.226930643Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:32:32.239244436Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:32:32.239260640Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:32:32.241338491Z info No lockfile found.
frontend-1  | 2026-08-18T11:32:32.256840758Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:32:35.523244583Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:32:48.131085357Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:32:48.132394980Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:32:48.162215558Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:32:48.162229545Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:32:48.203502247Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:32:48.203537750Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:32:48.203544289Z 
frontend-1  | 2026-08-18T11:32:48.203558581Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:32:48.203772708Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:32:48.214036705Z npm notice
frontend-1  | 2026-08-18T11:32:48.214065378Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:32:48.214070385Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:32:48.214074401Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:32:48.214081572Z npm notice
frontend-1  | 2026-08-18T11:32:49.441334407Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:32:49.441542405Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:32:49.441561574Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:32:49.441679278Z 
frontend-1  | 2026-08-18T11:32:49.441695202Z  ✓ Starting...
frontend-1  | 2026-08-18T11:32:49.537073145Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:32:49.751402301Z 
frontend-1  | 2026-08-18T11:32:49.751431955Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:32:49.751474278Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:32:49.751688055Z 
frontend-1  | 2026-08-18T11:32:49.897478099Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:32:49.912071869Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:32:49.912095835Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:32:49.914249099Z info No lockfile found.
frontend-1  | 2026-08-18T11:32:49.929781916Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:32:53.158288155Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:33:06.024259061Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:33:06.025538119Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:33:06.055128230Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:33:06.055128295Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:33:06.094631805Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:33:06.094663161Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:33:06.094667368Z 
frontend-1  | 2026-08-18T11:33:06.094675029Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:33:06.094914214Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:33:06.106631348Z npm notice
frontend-1  | 2026-08-18T11:33:06.106652810Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:33:06.106658168Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:33:06.106662274Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:33:06.106666270Z npm notice
frontend-1  | 2026-08-18T11:33:07.310398958Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:33:07.310601649Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:33:07.310613396Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:33:07.310757871Z 
frontend-1  | 2026-08-18T11:33:07.310798270Z  ✓ Starting...
frontend-1  | 2026-08-18T11:33:07.404445746Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:33:07.613399054Z 
frontend-1  | 2026-08-18T11:33:07.613440165Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:33:07.613458833Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:33:07.613717587Z 
frontend-1  | 2026-08-18T11:33:07.753492314Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:33:07.765675560Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:33:07.765688699Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:33:07.767856094Z info No lockfile found.
frontend-1  | 2026-08-18T11:33:07.783150777Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:33:11.448279987Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:33:24.244564186Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:33:24.245933798Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:33:24.278891176Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:33:24.278913384Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:33:24.318496470Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:33:24.318529179Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:33:24.318533525Z 
frontend-1  | 2026-08-18T11:33:24.319008685Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:33:24.319024288Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:33:24.328692008Z npm notice
frontend-1  | 2026-08-18T11:33:24.328716474Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:33:24.328721962Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:33:24.328726199Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:33:24.328729834Z npm notice
frontend-1  | 2026-08-18T11:33:25.580485622Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:33:25.580686120Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:33:25.580693952Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:33:25.580827269Z 
frontend-1  | 2026-08-18T11:33:25.580909702Z  ✓ Starting...
frontend-1  | 2026-08-18T11:33:25.676176187Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:33:25.889432554Z 
frontend-1  | 2026-08-18T11:33:25.889529177Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:33:25.889540814Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:33:25.889720221Z 
frontend-1  | 2026-08-18T11:33:26.040752960Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:33:26.053386681Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:33:26.053409635Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:33:26.055637011Z info No lockfile found.
frontend-1  | 2026-08-18T11:33:26.071738018Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:33:29.086839399Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:33:41.685943706Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:33:41.687255753Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:33:41.716977153Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:33:41.717003943Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:33:41.753544849Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:33:41.753571949Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:33:41.753577117Z 
frontend-1  | 2026-08-18T11:33:41.753629550Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:33:41.753837899Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:33:41.763736339Z npm notice
frontend-1  | 2026-08-18T11:33:41.763756810Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:33:41.763762057Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:33:41.763766204Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:33:41.763769669Z npm notice
frontend-1  | 2026-08-18T11:33:42.978336832Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:33:42.978455088Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:33:42.978465152Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:33:42.978635345Z 
frontend-1  | 2026-08-18T11:33:42.978645911Z  ✓ Starting...
frontend-1  | 2026-08-18T11:33:43.075564179Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:33:43.293075387Z 
frontend-1  | 2026-08-18T11:33:43.293141956Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:33:43.293147855Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:33:43.293463794Z 
frontend-1  | 2026-08-18T11:33:43.428056390Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:33:43.440352980Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:33:43.440372239Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:33:43.442500377Z info No lockfile found.
frontend-1  | 2026-08-18T11:33:43.457885871Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:33:47.234161278Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:33:59.964136484Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:33:59.965406057Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:33:59.995233031Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@img/sharp-libvips-linuxmusl-x64'
frontend-1  | 2026-08-18T11:33:59.995263320Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:34:00.035937207Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:34:00.035970737Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:34:00.035974963Z 
frontend-1  | 2026-08-18T11:34:00.035982524Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:34:00.036210913Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:34:00.047252094Z npm notice
frontend-1  | 2026-08-18T11:34:00.047281588Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:34:00.047287407Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:34:00.047290982Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:34:00.047294017Z npm notice
frontend-1  | 2026-08-18T11:34:01.267893570Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:34:01.268057753Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:34:01.268068670Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:34:01.268201777Z 
frontend-1  | 2026-08-18T11:34:01.268253098Z  ✓ Starting...
frontend-1  | 2026-08-18T11:34:01.366993746Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:34:01.582587741Z 
frontend-1  | 2026-08-18T11:34:01.582684875Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:34:01.582693318Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:34:01.582890460Z 
frontend-1  | 2026-08-18T11:34:01.728908047Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:34:01.741291269Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:34:01.741318039Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:34:01.743465415Z info No lockfile found.
frontend-1  | 2026-08-18T11:34:01.759376502Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:34:05.143334523Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:34:18.015549116Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:34:18.017497376Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:34:18.055252534Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:34:18.055252499Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:34:18.097245568Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:34:18.097280841Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:34:18.097286379Z 
frontend-1  | 2026-08-18T11:34:18.097353989Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:34:18.097546254Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:34:18.113596001Z npm notice
frontend-1  | 2026-08-18T11:34:18.113625134Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:34:18.113630262Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:34:18.113634268Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:34:18.113637833Z npm notice
frontend-1  | 2026-08-18T11:34:19.336803019Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:34:19.337016425Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:34:19.337025198Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:34:19.337155632Z 
frontend-1  | 2026-08-18T11:34:19.337204329Z  ✓ Starting...
frontend-1  | 2026-08-18T11:34:19.432815370Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:34:19.647633814Z 
frontend-1  | 2026-08-18T11:34:19.647666923Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:34:19.647672742Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:34:19.647678170Z 
frontend-1  | 2026-08-18T11:34:19.795717016Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:34:19.811083574Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:34:19.811241619Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:34:19.813734903Z info No lockfile found.
frontend-1  | 2026-08-18T11:34:19.829609654Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:34:23.840953635Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:34:36.784798635Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:34:36.786112514Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:34:36.817865037Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:34:36.817865032Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:34:36.861782156Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:34:36.861816356Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:34:36.861822365Z 
frontend-1  | 2026-08-18T11:34:36.861948027Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:34:36.862121344Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:34:36.873054935Z npm notice
frontend-1  | 2026-08-18T11:34:36.873087563Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:34:36.873095075Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:34:36.873101103Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:34:36.873119901Z npm notice
frontend-1  | 2026-08-18T11:34:38.129610549Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:34:38.129809116Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:34:38.129823783Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:34:38.129988570Z 
frontend-1  | 2026-08-18T11:34:38.130035706Z  ✓ Starting...
frontend-1  | 2026-08-18T11:34:38.228412122Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:34:38.467602096Z 
frontend-1  | 2026-08-18T11:34:38.467692023Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:34:38.467700353Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:34:38.467935043Z 
frontend-1  | 2026-08-18T11:34:38.620739028Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:34:38.634056655Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:34:38.634087602Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:34:38.636362274Z info No lockfile found.
frontend-1  | 2026-08-18T11:34:38.653130445Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:34:41.629815682Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:34:54.381439980Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:34:54.382786426Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:34:54.415848254Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:34:54.415904535Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:34:54.455739656Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:34:54.455773394Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:34:54.455778151Z 
frontend-1  | 2026-08-18T11:34:54.455935569Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:34:54.456052869Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:34:54.468564812Z npm notice
frontend-1  | 2026-08-18T11:34:54.468596037Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:34:54.468602497Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:34:54.468606673Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:34:54.468610378Z npm notice
frontend-1  | 2026-08-18T11:34:55.725455900Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:34:55.725648302Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:34:55.725659449Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:34:55.725820295Z 
frontend-1  | 2026-08-18T11:34:55.725830921Z  ✓ Starting...
frontend-1  | 2026-08-18T11:34:55.823691929Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:34:56.036670116Z 
frontend-1  | 2026-08-18T11:34:56.036701542Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:34:56.036730415Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:34:56.036979782Z 
frontend-1  | 2026-08-18T11:34:56.177132291Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:34:56.189513351Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:34:56.189535654Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:34:56.191650794Z info No lockfile found.
frontend-1  | 2026-08-18T11:34:56.207407006Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:34:59.287610454Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:35:12.173269355Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:35:12.174574937Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:35:12.203728100Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:35:12.203728970Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:35:12.243423422Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:35:12.243455539Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:35:12.243459935Z 
frontend-1  | 2026-08-18T11:35:12.243502453Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:35:12.243722392Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:35:12.253594124Z npm notice
frontend-1  | 2026-08-18T11:35:12.253626302Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:35:12.253631770Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:35:12.253635545Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:35:12.253639301Z npm notice
frontend-1  | 2026-08-18T11:35:13.468945670Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:35:13.469117032Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:35:13.469128309Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:35:13.469250989Z 
frontend-1  | 2026-08-18T11:35:13.469268074Z  ✓ Starting...
frontend-1  | 2026-08-18T11:35:13.564555482Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:35:13.778150878Z 
frontend-1  | 2026-08-18T11:35:13.778236949Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:35:13.778250459Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:35:13.778473903Z 
frontend-1  | 2026-08-18T11:35:13.919696031Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:35:13.931737541Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:35:13.931762949Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:35:13.933935666Z info No lockfile found.
frontend-1  | 2026-08-18T11:35:13.949180421Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:35:17.040142060Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:35:29.634589460Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:35:29.635946557Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:35:29.669094382Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:35:29.669136975Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:35:29.708382700Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:35:29.708415939Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:35:29.708421077Z 
frontend-1  | 2026-08-18T11:35:29.708456318Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:35:29.708692641Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:35:29.720495615Z npm notice
frontend-1  | 2026-08-18T11:35:29.720521213Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:35:29.720526611Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:35:29.720530757Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:35:29.720534542Z npm notice
frontend-1  | 2026-08-18T11:35:30.970339756Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:35:30.970507332Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:35:30.970518759Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:35:30.970644434Z 
frontend-1  | 2026-08-18T11:35:30.970661128Z  ✓ Starting...
frontend-1  | 2026-08-18T11:35:31.067664564Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:35:31.284993304Z 
frontend-1  | 2026-08-18T11:35:31.285024089Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:35:31.285029878Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:35:31.285035135Z 
frontend-1  | 2026-08-18T11:35:31.421441632Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:35:31.433895173Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:35:31.433911177Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:35:31.436081019Z info No lockfile found.
frontend-1  | 2026-08-18T11:35:31.451974490Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:35:34.600770085Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:35:47.666059225Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:35:47.667860899Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:35:47.705621068Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@img/sharp-libvips-linuxmusl-x64'
frontend-1  | 2026-08-18T11:35:47.705616887Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:35:47.746708603Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:35:47.746741642Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:35:47.746745858Z 
frontend-1  | 2026-08-18T11:35:47.746752848Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:35:47.747212175Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:35:47.759996284Z npm notice
frontend-1  | 2026-08-18T11:35:47.760022773Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:35:47.760027490Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:35:47.760031386Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:35:47.760034831Z npm notice
frontend-1  | 2026-08-18T11:35:48.975243556Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:35:48.975390142Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:35:48.975400978Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:35:48.975537879Z 
frontend-1  | 2026-08-18T11:35:48.975949611Z  ✓ Starting...
frontend-1  | 2026-08-18T11:35:49.071361888Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:35:49.282681958Z 
frontend-1  | 2026-08-18T11:35:49.282750509Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:35:49.282757279Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:35:49.282984063Z 
frontend-1  | 2026-08-18T11:35:49.423891922Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:35:49.436001553Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:35:49.436236194Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:35:49.438277946Z info No lockfile found.
frontend-1  | 2026-08-18T11:35:49.453494187Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:35:52.504204365Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:36:05.251897217Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:36:05.253268988Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:36:05.285863231Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:36:05.285894116Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:36:05.325419533Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:36:05.325462426Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:36:05.325467093Z 
frontend-1  | 2026-08-18T11:36:05.325501813Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:36:05.325755468Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:36:05.336946366Z npm notice
frontend-1  | 2026-08-18T11:36:05.336970882Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:36:05.336976270Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:36:05.336980276Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:36:05.336983851Z npm notice
frontend-1  | 2026-08-18T11:36:06.569046586Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:36:06.569232611Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:36:06.569276246Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:36:06.569424725Z 
frontend-1  | 2026-08-18T11:36:06.569480227Z  ✓ Starting...
frontend-1  | 2026-08-18T11:36:06.667574223Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:36:06.882674416Z 
frontend-1  | 2026-08-18T11:36:06.882707785Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:36:06.882738831Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:36:06.883116784Z 
frontend-1  | 2026-08-18T11:36:07.018906897Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:36:07.031313553Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:36:07.031331960Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:36:07.033407498Z info No lockfile found.
frontend-1  | 2026-08-18T11:36:07.048933635Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:36:10.329292028Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:36:22.837401511Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:36:22.838776356Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:36:22.868754511Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:36:22.868774040Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:36:22.910248056Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:36:22.910281956Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:36:22.910287624Z 
frontend-1  | 2026-08-18T11:36:22.910709899Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:36:22.910728647Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:36:22.921175845Z npm notice
frontend-1  | 2026-08-18T11:36:22.921201103Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:36:22.921222484Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:36:22.921226881Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:36:22.921230897Z npm notice
frontend-1  | 2026-08-18T11:36:24.148181305Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:36:24.148380450Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:36:24.148386800Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:36:24.148517002Z 
frontend-1  | 2026-08-18T11:36:24.148575850Z  ✓ Starting...
frontend-1  | 2026-08-18T11:36:24.243569335Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:36:24.454264792Z 
frontend-1  | 2026-08-18T11:36:24.454352547Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:36:24.454366177Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:36:24.454610734Z 
frontend-1  | 2026-08-18T11:36:24.602928516Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:36:24.615453450Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:36:24.615469293Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:36:24.617593859Z info No lockfile found.
frontend-1  | 2026-08-18T11:36:24.633434532Z [1/4] Resolving packages...
frontend-1  | 2026-08-18T11:36:27.875153956Z [2/4] Fetching packages...
frontend-1  | 2026-08-18T11:36:40.569764903Z [3/4] Linking dependencies...
frontend-1  | 2026-08-18T11:36:40.571135917Z warning " > @axe-core/playwright@4.13.0" has unmet peer dependency "playwright-core@>= 1.0.0".
frontend-1  | 2026-08-18T11:36:40.601935881Z error Error: EROFS: read-only file system, mkdir '/srv/pilot-web/node_modules/@axe-core/playwright'
frontend-1  | 2026-08-18T11:36:40.601954328Z info Visit https://yarnpkg.com/en/docs/cli/add for documentation about this command.
frontend-1  | 2026-08-18T11:36:40.641137596Z Failed to install TypeScript, please install it manually to continue:
frontend-1  | 2026-08-18T11:36:40.641174761Z yarn add --exact --dev typescript@5.8.2
frontend-1  | 2026-08-18T11:36:40.641180590Z 
frontend-1  | 2026-08-18T11:36:40.641189342Z  ⨯ Failed to load next.config.ts, see more info here https://nextjs.org/docs/messages/next-config-error
frontend-1  | 2026-08-18T11:36:40.641401741Z { command: 'yarn add --exact --dev typescript@5.8.2' }
frontend-1  | 2026-08-18T11:36:40.651624731Z npm notice
frontend-1  | 2026-08-18T11:36:40.651658411Z npm notice New major version of npm available! 10.9.8 -> 12.0.2
frontend-1  | 2026-08-18T11:36:40.651665551Z npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.0.2
frontend-1  | 2026-08-18T11:36:40.651671670Z npm notice To update run: npm install -g npm@12.0.2
frontend-1  | 2026-08-18T11:36:40.651676878Z npm notice
frontend-1  | 2026-08-18T11:36:41.900295629Z    ▲ Next.js 15.5.23
frontend-1  | 2026-08-18T11:36:41.900457368Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T11:36:41.900469736Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T11:36:41.900657042Z 
frontend-1  | 2026-08-18T11:36:41.900697662Z  ✓ Starting...
frontend-1  | 2026-08-18T11:36:41.997132014Z  ⚠ Installing TypeScript as it was not found while loading "next.config.ts".
frontend-1  | 2026-08-18T11:36:42.212151408Z 
frontend-1  | 2026-08-18T11:36:42.212239488Z Installing devDependencies (yarn):
frontend-1  | 2026-08-18T11:36:42.212245367Z - typescript@5.8.2
frontend-1  | 2026-08-18T11:36:42.212455938Z 
frontend-1  | 2026-08-18T11:36:42.355059023Z yarn add v1.22.22
frontend-1  | 2026-08-18T11:36:42.367411597Z warning Skipping preferred cache folder "/home/epd2web/.cache/yarn" because it is not writable.
frontend-1  | 2026-08-18T11:36:42.367431035Z warning Selected the next writable cache folder in the list, will be "/tmp/.yarn-cache-10003".
frontend-1  | 2026-08-18T11:36:42.369534901Z info No lockfile found.
frontend-1  | 2026-08-18T11:36:42.385582308Z [1/4] Resolving packages...
```
