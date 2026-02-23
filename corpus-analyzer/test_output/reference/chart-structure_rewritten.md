---
title: Helm Chart Structure Reference
source: kubernetes-operations/skills/helm-chart-scaffolding/references/chart-structure.md
---

# Helm Chart Structure: A Comprehensive Guide to Building Kubernetes Applications

This guide provides an in-depth look at the structure and best practices for creating Helm charts, which are used to package and deploy applications on Kubernetes.

## Table of Contents
1. [Introduction](#introduction)
2. [Chart Directory Structure](#chart-directory-structure)
3. [Chart Template Guide](#chart-template-guide)
4. [Best Practices](#best-practices)
5. [Declaring Dependencies](#declaring-dependencies)
6. [Managing Dependencies](#managing-dependencies)
7. [Chart.lock](#chartlock)
8. [.helmignore](#helmignore)
9. [Custom Resource Definitions (CRDs)](#custom-resource-definitions-crds)
10. [Chart Versioning](#chart-versioning)
11. [Chart Testing](#chart-testing)
12. [Hooks](#hooks)
13. [Best Practices](#best-practices-1)
14. [Chart Repository Structure](#chart-repository-structure)
15. [Creating Repository Index](#creating-repository-index)
16. [Related Resources](#related-resources)

<a name="introduction"></a>
## 1. Introduction
Helm is a package manager for Kubernetes that simplifies the deployment and management of applications on the platform. Helm charts are used to package these applications, making it easier to distribute and manage them across multiple clusters.

<a name="chart-directory-structure"></a>
## 2. Chart Directory Structure
A typical Helm chart consists of several key files and directories:

```bash
my-app/
├── Chart.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ...
├── values.yaml
├── NOTES.txt
└── crds/
    ├── my-app-crd.yaml
    └── another-crd.yaml
```

<a name="chart-template-guide"></a>
## 3. Chart Template Guide
The `templates` directory contains the Kubernetes manifests that will be generated when the chart is installed or upgraded. These templates use Go templates to dynamically generate the desired resources.

<a name="best-practices"></a>
## 4. Best Practices
Helm provides several best practices for creating charts, including:

1. Use helpers for repeated template logic
2. Quote strings in templates: `{{ .Values.name | quote }}`
3. Validate values with values.schema.json
4. Document all values in values.yaml
5. Use semantic versioning for chart versions
6. Pin dependency versions exactly
7. Include NOTES.txt with usage instructions
8. Add tests for critical functionality
9. Use hooks for database migrations
10. Keep charts focused - one application per chart

<a name="declaring-dependencies"></a>
## 5. Declaring Dependencies
Dependencies can be declared in the `Chart.yaml` file using the `dependencies` key:

```yaml
dependencies:
  - name: postgresql
    version: "12.0.0"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled  # Enable/disable via values
    tags:                          # Group dependencies
      - database
    import-values:                 # Import values from subchart
      - child: database
        parent: database
    alias: db                      # Reference as .Values.db
```

<a name="managing-dependencies"></a>
## 6. Managing Dependencies
Helm provides several commands for managing dependencies, including `helm dependency update`, `helm dependency list`, and `helm dependency build`.

<a name="chartlock"></a>
## 7. Chart.lock
The `Chart.lock` file is generated automatically by `helm dependency update` and contains the exact versions of all dependencies.

<a name="helmignore"></a>
## 8. .helmignore
`.helmignore` is used to exclude files from chart package. This can help reduce the size of the chart and make it easier to manage.

<a name="custom-resource-definitions-crds"></a>
## 9. Custom Resource Definitions (CRDs)
Custom Resource Definitions allow you to create new Kubernetes resources that can be managed using Helm charts. CRDs are placed in the `crds/` directory and are installed before any templates.

<a name="chart-versioning"></a>
## 10. Chart Versioning
Helm uses Semantic Versioning for chart versions, with major, minor, and patch versions indicating breaking changes, new features, and bug fixes respectively.

<a name="chart-testing"></a>
## 11. Chart Testing
Helm provides a testing framework that allows you to write tests for your charts. Tests are placed in the `templates/tests/` directory and can be run using the `helm test` command.

<a name="hooks"></a>
## 12. Hooks
Hooks allow you to execute additional Kubernetes resources at specific points during the installation, upgrade, or deletion of a chart.

<a name="best-practices-1"></a>
## 13. Best Practices (continued)
In addition to the practices mentioned earlier, it's also important to:

1. Use hooks for database migrations
2. Keep charts focused - one application per chart

<a name="chart-repository-structure"></a>
## 14. Chart Repository Structure
A Helm chart repository consists of a series of tarballs, each containing a single chart version. The repository index file (`index.yaml`) is used to list the available chart versions and their corresponding URLs.

<a name="creating-repository-index"></a>
## 15. Creating Repository Index
The repository index can be created using the `helm repo index` command, which generates an `index.yaml` file in the current directory.

<a name="related-resources"></a>
## 16. Related Resources
- [Helm Documentation](https://helm.sh/docs/)
- [Chart Template Guide](https://helm.sh/docs/chart_template_guide/)
- [Best Practices](https://helm.sh/docs/chart_best_practices/)

[source: kubernetes-operations/skills/helm-chart-scaffolding/references/chart-structure.md]