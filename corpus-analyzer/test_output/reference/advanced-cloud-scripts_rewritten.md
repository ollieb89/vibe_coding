---
title: Advanced Cloud Pentesting Scripts
source: skills/cloud-penetration-testing/references/advanced-cloud-scripts.md
---

# Advanced Cloud Scripts for Penetration Testing

This repository contains various scripts and tools that can be used during a cloud penetration test. The scripts are written in PowerShell, Python, and bash, and they target different cloud providers such as AWS, Azure, and GCP.

## Azure Post-Exploitation

### Password Spraying with Az PowerShell

This script is used for password spraying against Azure AD using the `Az` PowerShell module. The script reads two files: a list of usernames (`userlist.txt`) and a list of passwords (`passlist.txt`). It then attempts to log in as each user with their corresponding password, writing valid credentials to a file called `valid-creds.txt`.

```powershell
# ... (script code)
```

[source: skills/cloud-penetration-testing/references/advanced-cloud-scripts.md]

---

## Azure Attack Path

### Service Principal Attack Path

This script demonstrates how to reset a service principal's credential, log in as the service principal, create a new user in the tenant, and add the new user to Global Admin via MS Graph.

```bash
# ... (script code)
```

[source: skills/cloud-penetration-testing/references/advanced-cloud-scripts.md]

---

## AWS Enumeration and Exploitation

### MicroBurst

MicroBurst is an open-source tool used for performing an assessment of AWS security posture. It provides a comprehensive report on the state of various AWS services, including IAM policies, S3 buckets, EC2 instances, and more.

```bash
# ... (script code)
```

[source: skills/cloud-penetration-testing/references/advanced-cloud-scripts.md]

---

## Multi-Cloud Auditing

### ScoutSuite

ScoutSuite is a multi-cloud auditing tool that can be used to assess the security posture of AWS, Azure, and GCP environments. It provides reports on various aspects such as IAM policies, S3 buckets, EC2 instances, and more.

```bash
# ... (script code)
```

[source: skills/cloud-penetration-testing/references/advanced-cloud-scripts.md]

---

## Cloud IP Identification

### ip2Provider

ip2Provider is a simple tool that can be used to identify the cloud provider associated with an IP address.

```bash
# ... (script code)
```

[source: skills/cloud-penetration-testing/references/advanced-cloud-scripts.md]

---

## Additional Tools and References

Here are some additional tools and references that can be useful during cloud penetration testing:

### Tools

1. MicroBurst - github.com/NetSPI/MicroBurst
2. PowerZure - github.com/hausec/PowerZure
3. ROADTools - github.com/dirkjanm/ROADtools
4. Stormspotter - github.com/BloodHoundAD/AzureHound
5. MSOLSpray - github.com/dafthack
6. AzureHound - github.com/BloodHoundAD/AzureHound
7. WeirdAAL - github.com/carnal0wnage/weirdAAL
8. Pacu - github.com/RhinoSecurityLabs/pacu
9. ScoutSuite - github.com/nccgroup/ScoutSuite
10. cloud_enum - github.com/initstring/cloud_enum
11. GitLeaks - github.com/zricethezav/gitleaks
12. TruffleHog - github.com/dxa4481/truffleHog
13. FireProx - github.com/ustayready/fireprox

### Vulnerable Training Environments

1. CloudGoat - github.com/RhinoSecurityLabs/cloudgoat
2. SadCloud - github.com/nccgroup/sadcloud
3. Flaws Cloud - flaws.cloud
4. Thunder CTF - thunder-ctf.cloud

[source: skills/cloud-penetration-testing/references/advanced-cloud-scripts.md]