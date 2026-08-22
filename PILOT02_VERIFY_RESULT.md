# PILOT-02 Docker Verification Result

**Verdict:** VERIFIED — PILOT-02 OUTCOME A CONFIRMED

- Workflow run: 32157529232
- Commit: d61b9fe6980ba02a66308d8f3b0b4f882cc28e5c
- Environment rc: 0
- Integrity rc: 0
- Smoke rc: 0
- Success-marker rc: 0

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
lrwxrwxrwx 1 root root 13 Aug 18 15:53 /dev/fd -> /proc/self/fd
process-substitution-ok
```

## Integrity log (tail)
```text
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
tests/docker/test_pilot02c4_frontend_container.py: OK
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
tests/repository/test_pilot02c4_frontend_production_image.py: OK
tests/repository/test_prod01_runtime_spine.py: OK
tests/repository/test_required_files.py: OK
tests/repository/test_service_boundaries.py: OK
tests/repository/test_system_wide_corrective_closure.py: OK
tests/repository/test_version_consistency.py: OK
uv.lock: OK
```

## Product smoke log (tail)
```text
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
 19a2a5ab27c1 Download complete 
 6a47e1b9b254 Pull complete 
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
 8225e2970a7f Downloading [==================>                                ]  3.501kB/9.673kB
 8225e2970a7f Downloading [==================================================>]  9.673kB/9.673kB
 8225e2970a7f Download complete 
 f0e7204f9584 Downloading [>                                                  ]  527.8kB/111.3MB
 be6f407f5414 Pull complete 
 48d0d8b0e136 Downloading [==================================================>]     129B/129B
 48d0d8b0e136 Verifying Checksum 
 48d0d8b0e136 Download complete 
 27d0ba4f668a Downloading [==================================================>]     169B/169B
 27d0ba4f668a Verifying Checksum 
 27d0ba4f668a Download complete 
 f0e7204f9584 Downloading [==>                                                ]  5.269MB/111.3MB
 7f5de3d007ea Download complete 
 b053c4426c4a Downloading [============================>                      ]  3.501kB/6.112kB
 b053c4426c4a Downloading [==================================================>]  6.112kB/6.112kB
 b053c4426c4a Verifying Checksum 
 b053c4426c4a Download complete 
 f0e7204f9584 Downloading [=====>                                             ]   13.2MB/111.3MB
 f0e7204f9584 Downloading [====================>                              ]  46.25MB/111.3MB
 f0e7204f9584 Downloading [===============================>                   ]   70.8MB/111.3MB
 f0e7204f9584 Downloading [===============================================>   ]  104.9MB/111.3MB
 f0e7204f9584 Verifying Checksum 
 f0e7204f9584 Download complete 
 f0e7204f9584 Extracting [>                                                  ]  557.1kB/111.3MB
 f0e7204f9584 Extracting [==>                                                ]  5.014MB/111.3MB
 f0e7204f9584 Extracting [======>                                            ]  14.48MB/111.3MB
 f0e7204f9584 Extracting [==========>                                        ]  23.95MB/111.3MB
 f0e7204f9584 Extracting [==============>                                    ]  32.87MB/111.3MB
 f0e7204f9584 Extracting [==================>                                ]  41.78MB/111.3MB
 f0e7204f9584 Extracting [======================>                            ]  50.69MB/111.3MB
 f0e7204f9584 Extracting [=========================>                         ]  56.82MB/111.3MB
 f0e7204f9584 Extracting [============================>                      ]  62.95MB/111.3MB
 f0e7204f9584 Extracting [================================>                  ]  71.86MB/111.3MB
 f0e7204f9584 Extracting [====================================>              ]  80.77MB/111.3MB
 f0e7204f9584 Extracting [====================================>              ]  81.33MB/111.3MB
 f0e7204f9584 Extracting [=====================================>             ]  82.44MB/111.3MB
 f0e7204f9584 Extracting [======================================>            ]  85.23MB/111.3MB
 f0e7204f9584 Extracting [========================================>          ]  89.69MB/111.3MB
 f0e7204f9584 Extracting [==========================================>        ]  93.59MB/111.3MB
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
  ok   frontend reachable
  ok   member runtime readiness is true
  ok   the voting boundary declares NON_BINDING_PILOT and E2E not activated

[3] public home
  ok   the public home page is the supplied EPD² home page
  ok   the home page carries the party's own description
  ok   the non-binding pilot status is on the public home page
  ok   the Bürger-Login entry point is in the masthead

[4] public navigation
  ok   every item in the site navigation answers 200
  ok   every item in the site footer answers 200
  ok   previous .html addresses answer with a permanent redirect, not a 404
  ok   an unknown route answers 404 rather than a blank page

[5] current-content regression
  ok   24 headings from six areas of the supplied package are served verbatim
  ok   no migrated area was replaced by placeholder copy
  ok   the Satzung is served as a document, not a summary
  ok   the Grundsatzprogramm is served as a document

[6-17] product journey (login → … → public evidence)
  The block below is scripts/pilot/journey-check.sh, run unchanged from
  PILOT-01. It prints its own step numbers — [5] to [13] — because it is
  the same file PILOT-01's smoke runs and renumbering it here would give
  one script two numberings. They map onto PILOT-02 steps 6 to 17:

    journey [5]  login                  -> PILOT-02 [6]  login
    journey [6]  member dashboard       -> PILOT-02 [7]  dashboard
    journey [7]  create and submit      -> PILOT-02 [8][9]
    journey [8]  deliberation, election -> PILOT-02 [10][11]
    journey [9]  handoff                -> PILOT-02 [12]
    journey [10] cast, replay, revote   -> PILOT-02 [13][14]
    journey [11] closure                -> PILOT-02 [15]
    journey [12] result and evidence    -> PILOT-02 [16][17]
    journey [13] negative controls      -> interleaved throughout
[5] login
  ok   three sessions issued through the SEC-01 authentication path
  ok   a wrong secret is refused with 401
  ok   an unauthenticated member read is refused with 401
[6] member dashboard
  ok   membership reports MEMBERSHIP_ASSERTED_FOR_STAGING and is_governed=false
[7] create and submit an initiative
  ok   draft created in state DRAFT
  ok   author submitted their own draft: DRAFT -> SUBMITTED
[13] unauthorized authority actions are refused
  ok   pilot-member-2 cannot open deliberation (403)
  ok   pilot-member-2 cannot submit pilot-member-1's draft (403)
  ok   another member's unsubmitted draft is not readable (404)
  ok   an impossible transition is refused on shape (422)
[8] operator opens deliberation and the pilot election
  ok   operator opened deliberation: SUBMITTED -> OPEN_FOR_DELIBERATION
  ok   a member contributed to the deliberation and it persisted
  ok   the initiative detail carries the deliberation
  ok   operator opened a NON_BINDING_PILOT election with 4 eligible principals
  ok   pilot-member-2 cannot close the election (403)
[9] member voting handoff
  ok   a scoped one-time handoff into a separate origin was issued
[10] cast a ballot
  ok   pilot-member-1 cast a ballot and received a receipt with no selection in it
  ok   the one-time ticket is refused on replay (403)
  ok   a pre-closure revote replaced the earlier ballot
  ok   pilot-member-2 cast a ballot
  ok   a forged CSRF token at the voting origin is refused (403)
  ok   the ballot page is refused without a voting-origin session (401)
[11] operator closes the election
  ok   closed; 2 effective ballots counted, revote applied (YES=1 NO=1)
[12] public result and evidence
  ok   public result published without authentication: EPD2-PILOT-EVIDENCE-B3DCED882EC7A6F9
  ok   the published digest matches the voting boundary's own evidence package
  ok   evidence recomputes to its published digest, chain intact, no identity in it
  ok   the member area cannot report whether a ballot was cast
JOURNEY OK

[18] logout / access protection
  ok   an anonymous member read is refused with 401
  ok   a signed-in member read answers 200
  ok   sign-out accepted
  ok   the same cookie is refused with 401 after sign-out
  ok   /mitglied renders for anyone and depends on the runtime refusing its reads

[19] restart
 Container epd2-pilot-01-frontend-1  Stopping
 Container epd2-pilot-01-frontend-1  Stopped
 Container epd2-pilot-01-runtime-1  Stopping
 Container epd2-pilot-01-runtime-1  Stopped
 Container epd2-pilot-01-voting-1  Stopping
 Container epd2-pilot-01-voting-1  Stopped
 Container epd2-pilot-01-database-1  Running
 Container epd2-pilot-01-database-1  Waiting
 Container epd2-pilot-01-database-1  Healthy
 Container epd2-pilot-01-voting-1  Starting
 Container epd2-pilot-01-voting-1  Started
 Container epd2-pilot-01-voting-1  Waiting
 Container epd2-pilot-01-database-1  Waiting
 Container epd2-pilot-01-database-1  Healthy
 Container epd2-pilot-01-voting-1  Healthy
 Container epd2-pilot-01-runtime-1  Starting
 Container epd2-pilot-01-runtime-1  Started
 Container epd2-pilot-01-runtime-1  Waiting
 Container epd2-pilot-01-runtime-1  Healthy
 Container epd2-pilot-01-frontend-1  Starting
 Container epd2-pilot-01-frontend-1  Started
  ok   voting boundary is ready again
  ok   member runtime is ready again
  ok   frontend is reachable again
  ok   all services restarted without recreating their databases

[20] persistence
  ok   initiative, deliberation, ballots and result survived the restart
  ok   the tally is unchanged and the revote is still applied
  ok   the evidence digest is unchanged and the ballot chain is intact
  ok   the migrated public site is still served after the restart

[-] summary
  public site               45 migrated pages, one masthead, one footer
  compatibility             previous .html addresses answer permanently
  content gate              headings re-read from the supplied package each run
  member application        login -> dashboard -> initiative -> deliberation
                            -> handoff -> ballot -> revote -> closure
                            -> public result -> evidence
  voting origin             separate process, database and origin
  negative controls         anonymous read, unauthorized transition,
                            non-author submit, forged CSRF, replayed ticket,
                            session refused after sign-out
  binding status            NON_BINDING_PILOT throughout
  E2E verification          NOT activated, and said so on every surface

PILOT-02 PRODUCT SMOKE OK
```

## Docker diagnostics (tail)
```text
## docker compose ps -a
NAME                       IMAGE                        COMMAND                  SERVICE    CREATED          STATUS                            PORTS
epd2-pilot-01-database-1   postgres:16-alpine           "docker-entrypoint.s…"   database   37 seconds ago   Up 37 seconds (healthy)           5432/tcp
epd2-pilot-01-frontend-1   epd2-pilot/frontend:0.51.2   "docker-entrypoint.s…"   frontend   31 seconds ago   Up 2 seconds (health: starting)   0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
epd2-pilot-01-runtime-1    epd2-pilot/runtime:0.51.2    "python -m epd2_runt…"   runtime    31 seconds ago   Up 8 seconds (healthy)            0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
epd2-pilot-01-voting-1     epd2-pilot/voting:0.51.2     "python -m epd2_voti…"   voting     31 seconds ago   Up 13 seconds (healthy)           0.0.0.0:8100->8100/tcp, [::]:8100->8100/tcp

## runtime inspect
[
    {
        "Id": "473a446315ac9e7f7eef79b508e360d9cfa0db2eafb306cdd272f417b3d7f87d",
        "Created": "2026-08-18T15:58:26.792354221Z",
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
            "Pid": 5282,
            "ExitCode": 0,
            "Error": "",
            "StartedAt": "2026-08-18T15:58:49.514038809Z",
            "FinishedAt": "2026-08-18T15:58:42.863322777Z",
            "Health": {
                "Status": "healthy",
                "FailingStreak": 0,
                "Log": [
                    {
                        "Start": "2026-08-18T15:58:38.082786359Z",
                        "End": "2026-08-18T15:58:38.386257793Z",
                        "ExitCode": 0,
                        "Output": ""
                    },
                    {
                        "Start": "2026-08-18T15:58:54.636128346Z",
                        "End": "2026-08-18T15:58:54.928051998Z",
                        "ExitCode": 0,
                        "Output": ""
                    }
                ]
            }
        },
        "Image": "sha256:936b98b771d9b0a3f245c174ed5a756d15b061555f10ae82d9001f6d8ae44c85",
        "ResolvConfPath": "/var/lib/docker/containers/473a446315ac9e7f7eef79b508e360d9cfa0db2eafb306cdd272f417b3d7f87d/resolv.conf",
        "HostnamePath": "/var/lib/docker/containers/473a446315ac9e7f7eef79b508e360d9cfa0db2eafb306cdd272f417b3d7f87d/hostname",
        "HostsPath": "/var/lib/docker/containers/473a446315ac9e7f7eef79b508e360d9cfa0db2eafb306cdd272f417b3d7f87d/hosts",
        "LogPath": "/var/lib/docker/containers/473a446315ac9e7f7eef79b508e360d9cfa0db2eafb306cdd272f417b3d7f87d/473a446315ac9e7f7eef79b508e360d9cfa0db2eafb306cdd272f417b3d7f87d-json.log",
        "Name": "/epd2-pilot-01-runtime-1",
        "RestartCount": 0,
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
                "ID": "473a446315ac9e7f7eef79b508e360d9cfa0db2eafb306cdd272f417b3d7f87d",
                "LowerDir": "/var/lib/docker/overlay2/d224d70efdc5fee90652b75add304b6db349e6a75ceb71b32004a7da10e4524a-init/diff:/var/lib/docker/overlay2/ex7l55stifc70un7yjml79ggj/diff:/var/lib/docker/overlay2/6anjy7hr89j1scgr8i7nzq4zt/diff:/var/lib/docker/overlay2/z1almyf0xakkiyuqj225oqokl/diff:/var/lib/docker/overlay2/4bf0d677e2547bb82a048628642a15af664ec96ef6d19b199422abac4d0bd607/diff:/var/lib/docker/overlay2/5cdfb6cb69f77a8a06a5785a0b4c3e85ebbedffe438b5a85fbb38a2c3ccb7933/diff:/var/lib/docker/overlay2/1b5a50bde802ed7772ebef438d5fb4486f3cc70b54bd230ea22ec6e98b13e3e7/diff:/var/lib/docker/overlay2/b86dfae3c0698a07dae837b25a12c42cd791dd1591bbfbffdbf6885efd49f7c0/diff",
                "MergedDir": "/var/lib/docker/overlay2/d224d70efdc5fee90652b75add304b6db349e6a75ceb71b32004a7da10e4524a/merged",
                "UpperDir": "/var/lib/docker/overlay2/d224d70efdc5fee90652b75add304b6db349e6a75ceb71b32004a7da10e4524a/diff",
                "WorkDir": "/var/lib/docker/overlay2/d224d70efdc5fee90652b75add304b6db349e6a75ceb71b32004a7da10e4524a/work"
            },
            "Name": "overlay2"
        },
        "Mounts": [],
        "Config": {
            "Hostname": "473a446315ac",
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
                "EPD2_DATABASE_URL=postgresql://epd2_pilot:cd9ff9be50e1ee5be19b0d5498a551454da20bd79a06be1d@database:5432/epd2_pilot",
                "EPD2_VOTING_BOUNDARY_PUBLIC_URL=http://localhost:8100",
                "EPD2_PROFILE=DEVELOPMENT",
                "EPD2_BIND_HOST=0.0.0.0",
                "EPD2_SESSION_COOKIE_HTTPONLY=1",
                "EPD2_CSRF_PROTECTION=1",
                "EPD2_MIGRATE_ON_START=1",
                "EPD2_BIND_PORT=8000",
                "EPD2_AUTHENTICATION=LOCAL_SESSION",
                "EPD2_PERSISTENCE=POSTGRESQL",
                "EPD2_VOTING_SERVICE_TOKEN=7344e872bd4604763d66cc44f01126a4ce1dca1268acf7c7c58904d27c621d3e",
                "EPD2_LOG_LEVEL=INFO",
                "EPD2_AUDIT_REQUIRED=1",
                "EPD2_RATE_LIMIT_ENABLED=1",
                "EPD2_SESSION_COOKIE_SECURE=0",
                "EPD2_SESSION_COOKIE_SAMESITE=Lax",
                "EPD2_ALLOWED_ORIGINS=http://127.0.0.1:3000",
                "EPD2_PUBLIC_BASE_URL=http://127.0.0.1:8000",
                "EPD2_VOTING_BOUNDARY_URL=http://voting:8100",
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
            "Image": "epd2-pilot/runtime:0.51.2",
            "Volumes": null,
            "WorkingDir": "/srv/epd2",
            "Entrypoint": null,
            "OnBuild": null,
            "Labels": {
                "com.docker.compose.config-hash": "6e1919c99842c9e3e92922ff02aba5e532806aee86fb72ad585f002581ecd67a",
                "com.docker.compose.container-number": "1",
                "com.docker.compose.depends_on": "database:service_healthy:false,voting:service_healthy:false",
                "com.docker.compose.image": "sha256:936b98b771d9b0a3f245c174ed5a756d15b061555f10ae82d9001f6d8ae44c85",
                "com.docker.compose.oneoff": "False",
                "com.docker.compose.project": "epd2-pilot-01",
                "com.docker.compose.project.config_files": "/tmp/pilot02-candidate/EPD2_PILOT02_PUBLIC_SITE_INTEGRATION_AND_UNIFIED_PILOT_PRODUCT_CANDIDATE_0.51.2_C4/deploy/pilot/compose.yaml",
                "com.docker.compose.project.environment_file": "/tmp/pilot02-candidate/EPD2_PILOT02_PUBLIC_SITE_INTEGRATION_AND_UNIFIED_PILOT_PRODUCT_CANDIDATE_0.51.2_C4/deploy/pilot/.env",
                "com.docker.compose.project.working_dir": "/tmp/pilot02-candidate/EPD2_PILOT02_PUBLIC_SITE_INTEGRATION_AND_UNIFIED_PILOT_PRODUCT_CANDIDATE_0.51.2_C4/deploy/pilot",
                "com.docker.compose.service": "runtime",
                "com.docker.compose.version": "2.38.2"
            },
            "StopSignal": "SIGTERM",
            "StopTimeout": 30
        },
        "NetworkSettings": {
            "Bridge": "",
            "SandboxID": "a6a59f3e476045db8d0148535bfeaf58fc814257db698a0413b0e0f61d7a416a",
            "SandboxKey": "/var/run/docker/netns/a6a59f3e4760",
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
                    "MacAddress": "a6:14:10:ce:12:d1",
                    "DriverOpts": null,
                    "GwPriority": 0,
                    "NetworkID": "10ad10ffb9187991bf90694007e1aed53c27c1414e8557872b6fc90589ce7722",
                    "EndpointID": "1c1f6d299369d8fcf7c6b774271dd0522c3312e13a547bb8d63338eb32e09f3f",
                    "Gateway": "172.18.0.1",
                    "IPAddress": "172.18.0.4",
                    "IPPrefixLen": 16,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "DNSNames": [
                        "epd2-pilot-01-runtime-1",
                        "runtime",
                        "473a446315ac"
                    ]
                }
            }
        }
    }
]

## runtime logs
runtime-1  | 2026-08-18T15:58:38.375175715Z {"context":"epd2-runtime","correlation_id":"d4b6b02d-ab8b-4a8c-8566-935fe884fbca","duration_ms":31,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/health/ready","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:39.972927045Z {"context":"epd2-runtime","correlation_id":"c783ee10-b950-4e4e-a1d0-fec700afebc4","duration_ms":9,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/health/ready","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:40.020209437Z {"context":"epd2-runtime","correlation_id":"7bb05701-b0d0-4511-8833-afcea40fd151","duration_ms":5,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/health/ready","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:40.511208711Z {"context":"epd2-runtime","correlation_id":"91a98cc2-e462-43d5-a789-1b42858f840f","duration_ms":40,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/session","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:40.582311777Z {"context":"epd2-runtime","correlation_id":"52cf83ec-f5fa-4cc4-8c74-e336d73e3ca4","duration_ms":33,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/session","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:40.650381244Z {"context":"epd2-runtime","correlation_id":"7dee4388-c6c5-4c01-8caa-e60f1edf995f","duration_ms":37,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/session","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:40.716846546Z {"correlation_id":"c82ef39a-76a7-4c7a-8bf6-893c5e44cf75","environment":"DEVELOPMENT","error_class":"AUTHENTICATION_REQUIRED","event":"request_failed","exception":"AuthenticationFailed","path":"/api/v1/session","service":"citizen-office-routing-service"}
runtime-1  | 2026-08-18T15:58:40.717135247Z {"context":"epd2-runtime","correlation_id":"c82ef39a-76a7-4c7a-8bf6-893c5e44cf75","duration_ms":34,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/session","result":"refused","service":"citizen-office-routing-service","status":401}
runtime-1  | 2026-08-18T15:58:40.725635909Z {"correlation_id":"6fae191c-2ed8-46ae-a5ad-2dbbec91ce50","environment":"DEVELOPMENT","error_class":"AUTHENTICATION_REQUIRED","event":"request_failed","exception":"_AuthenticationRequired","path":"/api/v1/initiatives","service":"citizen-office-routing-service"}
runtime-1  | 2026-08-18T15:58:40.725836395Z {"context":"pilot-initiative-service","correlation_id":"6fae191c-2ed8-46ae-a5ad-2dbbec91ce50","duration_ms":1,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/initiatives","result":"refused","service":"citizen-office-routing-service","status":401}
runtime-1  | 2026-08-18T15:58:40.743736206Z {"context":"account-service","correlation_id":"6165be48-d36c-4684-8b5d-14001bdfca2c","duration_ms":11,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/account/me","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:40.765480755Z {"context":"membership-service","correlation_id":"8b8e2d6f-2bf6-44d2-83c4-23a850dead42","duration_ms":6,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/membership/me","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:40.788096463Z {"context":"membership-service","correlation_id":"ff7b8541-a056-4490-8230-9d310d6a6c7d","duration_ms":4,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/membership/me","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:40.885573569Z {"context":"pilot-initiative-service","correlation_id":"2100935a-1bd9-4854-a7f4-b2688304f2e8","duration_ms":13,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/initiatives","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:40.948162825Z {"context":"pilot-initiative-service","correlation_id":"58dfdac6-8d49-40a8-ae78-fc98c77439d5","duration_ms":8,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/initiatives/e813d1b5-3939-401f-b9c1-a72f876be7de/submission","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:41.049296764Z {"context":"pilot-initiative-service","correlation_id":"2ac760fc-1e48-4d9f-b06d-f7f30f09e376","environment":"DEVELOPMENT","event":"authorization_denied","operation":"open_deliberation","reason":"PILOT_OPERATOR_ROLE_REQUIRED","service":"citizen-office-routing-service"}
runtime-1  | 2026-08-18T15:58:41.049774226Z {"correlation_id":"2ac760fc-1e48-4d9f-b06d-f7f30f09e376","environment":"DEVELOPMENT","error_class":"AUTHORIZATION_DENIED","event":"request_failed","exception":"PermissionError","path":"/api/v1/initiatives/e813d1b5-3939-401f-b9c1-a72f876be7de/deliberation","service":"citizen-office-routing-service"}
runtime-1  | 2026-08-18T15:58:41.050636140Z {"context":"pilot-initiative-service","correlation_id":"2ac760fc-1e48-4d9f-b06d-f7f30f09e376","duration_ms":7,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/initiatives/e813d1b5-3939-401f-b9c1-a72f876be7de/deliberation","result":"refused","service":"citizen-office-routing-service","status":403}
runtime-1  | 2026-08-18T15:58:41.132575072Z {"context":"pilot-initiative-service","correlation_id":"2647598c-4420-4327-b105-2a68765032d2","duration_ms":8,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/initiatives","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:41.168548612Z {"correlation_id":"c6450f6e-fe6e-48e3-b02c-dc38dc0e649e","environment":"DEVELOPMENT","error_class":"AUTHORIZATION_DENIED","event":"request_failed","exception":"TransitionAuthorityRequired","path":"/api/v1/initiatives/07b86646-c498-4070-bcf4-ca61df0201ea/submission","service":"citizen-office-routing-service"}
runtime-1  | 2026-08-18T15:58:41.169402061Z {"context":"pilot-initiative-service","correlation_id":"c6450f6e-fe6e-48e3-b02c-dc38dc0e649e","duration_ms":6,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/initiatives/07b86646-c498-4070-bcf4-ca61df0201ea/submission","result":"refused","service":"citizen-office-routing-service","status":403}
runtime-1  | 2026-08-18T15:58:41.180077581Z {"correlation_id":"95d42fe1-193e-4d9e-9bf7-0c1da5d7de63","environment":"DEVELOPMENT","error_class":"NOT_FOUND","event":"request_failed","exception":"LookupError","path":"/api/v1/initiatives/07b86646-c498-4070-bcf4-ca61df0201ea","service":"citizen-office-routing-service"}
runtime-1  | 2026-08-18T15:58:41.180303865Z {"context":"pilot-initiative-service","correlation_id":"95d42fe1-193e-4d9e-9bf7-0c1da5d7de63","duration_ms":4,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/initiatives/07b86646-c498-4070-bcf4-ca61df0201ea","result":"refused","service":"citizen-office-routing-service","status":404}
runtime-1  | 2026-08-18T15:58:41.214479853Z {"correlation_id":"32632e91-d73c-4264-86b4-ad8cb00c90ee","environment":"DEVELOPMENT","error_class":"VALIDATION_ERROR","event":"request_failed","exception":"ForbiddenPilotTransition","path":"/api/v1/initiatives/e813d1b5-3939-401f-b9c1-a72f876be7de/submission","service":"citizen-office-routing-service"}
runtime-1  | 2026-08-18T15:58:41.214693263Z {"context":"pilot-initiative-service","correlation_id":"32632e91-d73c-4264-86b4-ad8cb00c90ee","duration_ms":5,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/initiatives/e813d1b5-3939-401f-b9c1-a72f876be7de/submission","result":"refused","service":"citizen-office-routing-service","status":422}
runtime-1  | 2026-08-18T15:58:41.255712724Z {"context":"pilot-initiative-service","correlation_id":"a8087836-8d3c-4c30-8f49-133564471006","duration_ms":11,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/initiatives/e813d1b5-3939-401f-b9c1-a72f876be7de/deliberation","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:41.339453328Z {"context":"deliberation-service","correlation_id":"9b5dae53-4970-4e09-929f-6a63d1689e76","duration_ms":9,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/deliberation/discussions/e6e1883e-eee7-4b24-a01b-e58331988be1/contributions","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:41.376297459Z {"context":"pilot-initiative-service","correlation_id":"9ea4ab11-f9d5-4de3-a396-f0295f13fdcf","duration_ms":5,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/initiatives/e813d1b5-3939-401f-b9c1-a72f876be7de","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:41.482558320Z {"context":"pilot-initiative-service","correlation_id":"5e5512c0-9054-4b3b-bd51-d254fa378ed0","duration_ms":33,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/initiatives/e813d1b5-3939-401f-b9c1-a72f876be7de/pilot-election","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:41.586510616Z {"context":"pilot-election-service","correlation_id":"ea29a1d4-d936-4fd6-aaf4-3f90cf4c964a","environment":"DEVELOPMENT","event":"authorization_denied","operation":"close_pilot_vote","reason":"PILOT_OPERATOR_ROLE_REQUIRED","service":"citizen-office-routing-service"}
runtime-1  | 2026-08-18T15:58:41.587001381Z {"correlation_id":"ea29a1d4-d936-4fd6-aaf4-3f90cf4c964a","environment":"DEVELOPMENT","error_class":"AUTHORIZATION_DENIED","event":"request_failed","exception":"PermissionError","path":"/api/v1/initiatives/e813d1b5-3939-401f-b9c1-a72f876be7de/closure","service":"citizen-office-routing-service"}
runtime-1  | 2026-08-18T15:58:41.587853497Z {"context":"pilot-initiative-service","correlation_id":"ea29a1d4-d936-4fd6-aaf4-3f90cf4c964a","duration_ms":6,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/initiatives/e813d1b5-3939-401f-b9c1-a72f876be7de/closure","result":"refused","service":"citizen-office-routing-service","status":403}
runtime-1  | 2026-08-18T15:58:41.633990514Z {"context":"pilot-election-service","correlation_id":"4500d2b6-69e3-4e88-ba6c-cc31af9964b7","duration_ms":16,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/pilot-vote/handoff","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:41.801449982Z {"context":"pilot-election-service","correlation_id":"87aeb125-2f0c-43c4-9635-ca57e5c99f7e","duration_ms":13,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/pilot-vote/handoff","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:41.914990621Z {"context":"pilot-election-service","correlation_id":"9d9513b4-1bff-4f9e-a235-c73bce41419a","duration_ms":13,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/pilot-vote/handoff","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:42.048792309Z {"context":"pilot-initiative-service","correlation_id":"1f268710-33bb-43f6-b36c-127e7aa38c45","duration_ms":23,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/initiatives/e813d1b5-3939-401f-b9c1-a72f876be7de/closure","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:42.153214243Z {"context":"transparency-service","correlation_id":"0a4d0751-21f8-4996-b965-752a1bbb8f94","duration_ms":3,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/transparency/pilot-elections/97c39e7c-5fec-42ac-a45d-e02b751e839c","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:42.361131190Z {"context":"pilot-election-service","correlation_id":"ed1e6c7c-ac18-4c15-9f20-e4c8ff934ab4","duration_ms":5,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/pilot-election/97c39e7c-5fec-42ac-a45d-e02b751e839c/eligibility","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:42.394624464Z {"correlation_id":"4bb902a4-8331-4812-9b19-87d7bfd0c3f9","environment":"DEVELOPMENT","error_class":"AUTHENTICATION_REQUIRED","event":"request_failed","exception":"_AuthenticationRequired","path":"/api/v1/account/me","service":"citizen-office-routing-service"}
runtime-1  | 2026-08-18T15:58:42.394811464Z {"context":"account-service","correlation_id":"4bb902a4-8331-4812-9b19-87d7bfd0c3f9","duration_ms":0,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/account/me","result":"refused","service":"citizen-office-routing-service","status":401}
runtime-1  | 2026-08-18T15:58:42.437033748Z {"context":"epd2-runtime","correlation_id":"152f3770-78f1-456d-8c9d-99d42efaa5c7","duration_ms":35,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"POST","path":"/api/v1/session","result":"ok","service":"citizen-office-routing-service","status":201}
runtime-1  | 2026-08-18T15:58:42.455135353Z {"context":"account-service","correlation_id":"56de1c16-e940-4216-b9a0-5a4c427b3440","duration_ms":4,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/account/me","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:42.463876366Z {"context":"epd2-runtime","correlation_id":"29031eea-8f5e-4990-a0f9-4e06b5a2fb8b","duration_ms":2,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"DELETE","path":"/api/v1/session","result":"ok","service":"citizen-office-routing-service","status":204}
runtime-1  | 2026-08-18T15:58:42.471638705Z {"correlation_id":"4ea6589d-dff0-4f94-9801-397ee52d4cb6","environment":"DEVELOPMENT","error_class":"AUTHENTICATION_REQUIRED","event":"request_failed","exception":"_AuthenticationRequired","path":"/api/v1/account/me","service":"citizen-office-routing-service"}
runtime-1  | 2026-08-18T15:58:42.471834211Z {"context":"account-service","correlation_id":"4ea6589d-dff0-4f94-9801-397ee52d4cb6","duration_ms":0,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/account/me","result":"refused","service":"citizen-office-routing-service","status":401}
runtime-1  | 2026-08-18T15:58:54.916577931Z {"context":"epd2-runtime","correlation_id":"2571ea9e-7d7d-4fdc-9cbc-70ba1cec1d7b","duration_ms":19,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/health/ready","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:55.301138397Z {"context":"epd2-runtime","correlation_id":"f9dd03a5-369e-4286-a0f4-b9d4ad2fa25f","duration_ms":10,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/health/ready","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:57.420507798Z {"context":"transparency-service","correlation_id":"a4bae271-e108-4dcc-9955-fc10646826d8","duration_ms":6,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/transparency/pilot-elections","result":"ok","service":"citizen-office-routing-service","status":200}
runtime-1  | 2026-08-18T15:58:57.425632784Z {"context":"transparency-service","correlation_id":"3fb011ce-41da-4e8e-8049-3ac3b1918f10","duration_ms":3,"environment":"DEVELOPMENT","error_class":null,"event":"http_request","event_class":"http","method":"GET","path":"/api/v1/transparency/pilot-elections/97c39e7c-5fec-42ac-a45d-e02b751e839c","result":"ok","service":"citizen-office-routing-service","status":200}

## voting logs

## database logs (tail 200)
database-1  | 2026-08-18T15:58:20.418980344Z The files belonging to this database system will be owned by user "postgres".
database-1  | 2026-08-18T15:58:20.419035287Z This user must also own the server process.
database-1  | 2026-08-18T15:58:20.419040277Z 
database-1  | 2026-08-18T15:58:20.419043934Z The database cluster will be initialized with locale "en_US.utf8".
database-1  | 2026-08-18T15:58:20.419047340Z The default database encoding has accordingly been set to "UTF8".
database-1  | 2026-08-18T15:58:20.419050836Z The default text search configuration will be set to "english".
database-1  | 2026-08-18T15:58:20.419054022Z 
database-1  | 2026-08-18T15:58:20.419057058Z Data page checksums are disabled.
database-1  | 2026-08-18T15:58:20.419060134Z 
database-1  | 2026-08-18T15:58:20.419063139Z fixing permissions on existing directory /var/lib/postgresql/data ... ok
database-1  | 2026-08-18T15:58:20.419066636Z creating subdirectories ... ok
database-1  | 2026-08-18T15:58:20.419069922Z selecting dynamic shared memory implementation ... posix
database-1  | 2026-08-18T15:58:20.444590738Z selecting default max_connections ... 100
database-1  | 2026-08-18T15:58:20.464704820Z selecting default shared_buffers ... 128MB
database-1  | 2026-08-18T15:58:20.508584612Z selecting default time zone ... UTC
database-1  | 2026-08-18T15:58:20.509444493Z creating configuration files ... ok
database-1  | 2026-08-18T15:58:20.637726092Z running bootstrap script ... ok
database-1  | 2026-08-18T15:58:20.832924587Z sh: locale: not found
database-1  | 2026-08-18T15:58:20.833022892Z 2026-08-18 15:58:20.832 UTC [35] WARNING:  no usable system locales were found
database-1  | 2026-08-18T15:58:21.303037945Z performing post-bootstrap initialization ... ok
database-1  | 2026-08-18T15:58:21.348939570Z initdb: warning: enabling "trust" authentication for local connections
database-1  | 2026-08-18T15:58:21.348956953Z initdb: hint: You can change this by editing pg_hba.conf or using the option -A, or --auth-local and --auth-host, the next time you run initdb.
database-1  | 2026-08-18T15:58:21.348938834Z syncing data to disk ... ok
database-1  | 2026-08-18T15:58:21.348963916Z 
database-1  | 2026-08-18T15:58:21.348966260Z 
database-1  | 2026-08-18T15:58:21.348968645Z Success. You can now start the database server using:
database-1  | 2026-08-18T15:58:21.348971019Z 
database-1  | 2026-08-18T15:58:21.348973063Z     pg_ctl -D /var/lib/postgresql/data -l logfile start
database-1  | 2026-08-18T15:58:21.348975087Z 
database-1  | 2026-08-18T15:58:21.386046980Z waiting for server to start....2026-08-18 15:58:21.385 UTC [41] LOG:  starting PostgreSQL 16.15 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
database-1  | 2026-08-18T15:58:21.389196069Z 2026-08-18 15:58:21.389 UTC [41] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
database-1  | 2026-08-18T15:58:21.391937634Z 2026-08-18 15:58:21.391 UTC [44] LOG:  database system was shut down at 2026-08-18 15:58:21 UTC
database-1  | 2026-08-18T15:58:21.395854113Z 2026-08-18 15:58:21.395 UTC [41] LOG:  database system is ready to accept connections
database-1  | 2026-08-18T15:58:21.468675053Z  done
database-1  | 2026-08-18T15:58:21.468697876Z server started
database-1  | 2026-08-18T15:58:21.532244921Z CREATE DATABASE
database-1  | 2026-08-18T15:58:21.532962984Z 
database-1  | 2026-08-18T15:58:21.532976659Z 
database-1  | 2026-08-18T15:58:21.532980477Z /usr/local/bin/docker-entrypoint.sh: running /docker-entrypoint-initdb.d/01-voting-database.sh
database-1  | 2026-08-18T15:58:21.577595404Z CREATE DATABASE
database-1  | 2026-08-18T15:58:21.578008227Z created epd2_pilot_voting
database-1  | 2026-08-18T15:58:21.578202884Z 
database-1  | 2026-08-18T15:58:21.579185114Z waiting for server to shut down....2026-08-18 15:58:21.579 UTC [41] LOG:  received fast shutdown request
database-1  | 2026-08-18T15:58:21.579686320Z 2026-08-18 15:58:21.579 UTC [41] LOG:  aborting any active transactions
database-1  | 2026-08-18T15:58:21.582814395Z 2026-08-18 15:58:21.582 UTC [41] LOG:  background worker "logical replication launcher" (PID 47) exited with exit code 1
database-1  | 2026-08-18T15:58:21.583605647Z 2026-08-18 15:58:21.583 UTC [42] LOG:  shutting down
database-1  | 2026-08-18T15:58:21.584076679Z 2026-08-18 15:58:21.584 UTC [42] LOG:  checkpoint starting: shutdown immediate
database-1  | 2026-08-18T15:58:21.616600430Z 2026-08-18 15:58:21.616 UTC [42] LOG:  checkpoint complete: wrote 1846 buffers (11.3%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.027 s, sync=0.004 s, total=0.033 s; sync files=597, longest=0.002 s, average=0.001 s; distance=8565 kB, estimate=8565 kB; lsn=0/1D545D8, redo lsn=0/1D545D8
database-1  | 2026-08-18T15:58:21.625136399Z 2026-08-18 15:58:21.625 UTC [41] LOG:  database system is shut down
database-1  | 2026-08-18T15:58:21.679306265Z  done
database-1  | 2026-08-18T15:58:21.679324839Z server stopped
database-1  | 2026-08-18T15:58:21.680250896Z 
database-1  | 2026-08-18T15:58:21.680262518Z PostgreSQL init process complete; ready for start up.
database-1  | 2026-08-18T15:58:21.680267517Z 
database-1  | 2026-08-18T15:58:21.700961665Z 2026-08-18 15:58:21.700 UTC [1] LOG:  starting PostgreSQL 16.15 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
database-1  | 2026-08-18T15:58:21.700980220Z 2026-08-18 15:58:21.700 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
database-1  | 2026-08-18T15:58:21.700984869Z 2026-08-18 15:58:21.700 UTC [1] LOG:  listening on IPv6 address "::", port 5432
database-1  | 2026-08-18T15:58:21.702603345Z 2026-08-18 15:58:21.702 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
database-1  | 2026-08-18T15:58:21.705766368Z 2026-08-18 15:58:21.705 UTC [62] LOG:  database system was shut down at 2026-08-18 15:58:21 UTC
database-1  | 2026-08-18T15:58:21.722049408Z 2026-08-18 15:58:21.721 UTC [1] LOG:  database system is ready to accept connections

## frontend logs
frontend-1  | 2026-08-18T15:58:38.950229875Z    ▲ Next.js 15.5.21
frontend-1  | 2026-08-18T15:58:38.950592474Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T15:58:38.950630806Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T15:58:38.950767171Z 
frontend-1  | 2026-08-18T15:58:38.950854194Z  ✓ Starting...
frontend-1  | 2026-08-18T15:58:39.082821955Z  ✓ Ready in 143ms
frontend-1  | 2026-08-18T15:58:40.305470242Z Failed to update prerender cache for /diese-seite-gibt-es-nicht [Error: EROFS: read-only file system, open '/srv/pilot-web/.next/server/app/diese-seite-gibt-es-nicht.html'] {
frontend-1  | 2026-08-18T15:58:40.305510447Z   errno: -30,
frontend-1  | 2026-08-18T15:58:40.305515787Z   code: 'EROFS',
frontend-1  | 2026-08-18T15:58:40.305526317Z   syscall: 'open',
frontend-1  | 2026-08-18T15:58:40.305533010Z   path: '/srv/pilot-web/.next/server/app/diese-seite-gibt-es-nicht.html'
frontend-1  | 2026-08-18T15:58:40.305539241Z }
frontend-1  | 2026-08-18T15:58:55.457264885Z    ▲ Next.js 15.5.21
frontend-1  | 2026-08-18T15:58:55.457488173Z    - Local:        http://localhost:3000
frontend-1  | 2026-08-18T15:58:55.457500105Z    - Network:      http://0.0.0.0:3000
frontend-1  | 2026-08-18T15:58:55.457624078Z 
frontend-1  | 2026-08-18T15:58:55.457658632Z  ✓ Starting...
frontend-1  | 2026-08-18T15:58:55.561519360Z  ✓ Ready in 111ms
```
