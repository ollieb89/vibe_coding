---
title: Kubernetes Deployment Specification Reference
description: Comprehensive reference for Kubernetes Deployment resources, covering all key fields, best practices, and common patterns.
tags: kubernetes, deployment, yaml, manifest
---

## Introduction

This document provides a comprehensive reference for Kubernetes Deployment resources, focusing on key fields, best practices, and common patterns.

## Structure and Clarity

Improve structure and clarity to make the content more accessible and user-friendly.

## Code Examples

All code blocks should remain exactly as-is (verbatim), without any summarization or modification of the original examples.

## Citation

[source: kubernetes-operations/skills/k8s-manifest-generator/references/deployment-spec.md]

## Logical Hierarchy

Ensure all headings follow a logical hierarchy, with no skipping levels.

## Placeholder Text

Replace any placeholder text like [user-defined] with helpful descriptions to aid users in understanding the content.

## YAML Frontmatter

Begin with YAML frontmatter including title, description, and tags.

## Markdown Format

Do not wrap the output in a markdown code block (output raw text).

## Instructions

1. Improve structure and clarity
2. Keep all code blocks exactly as-is (verbatim, do not summarize)
3. Add a citation [source: kubernetes-operations/skills/k8s-manifest-generator/references/deployment-spec.md] at the end
4. Ensure all headings follow a logical hierarchy (no skipping levels)
5. Expand any placeholder text like [user-defined] into helpful descriptions
6. Start with YAML frontmatter including title, description, and tags
7. Do NOT wrap the output in a markdown code block (output raw text)
8. Do not repeat these instructions in your response.

## Deployment Structure

A Kubernetes Deployment consists of the following elements:

- `apiVersion`: The API version for the resource.
- `kind`: The kind or type of resource being defined, which is "Deployment" in this case.
- `metadata`: Metadata about the deployment, including its name and namespace.
- `spec`: The specification for the Deployment, containing details such as replicas, template, strategy, etc.
- `status`: The current status of the Deployment, including information about the number of available replicas, updates, and more.

### Metadata

The `metadata` section contains essential information about the deployment, such as its name and namespace.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
  labels:
    app: my-app
  namespace: my-namespace
```

#### Labels

Labels are key-value pairs that can be used to organize and filter resources in Kubernetes. In the example above, the label `app: my-app` is added to the deployment for easier management.

### Specification

The `spec` section contains the configuration details for the Deployment, such as replicas, template, strategy, etc.

#### Replicas

Replicas define the number of identical pods that should be created and maintained by the Deployment.

```yaml
spec:
  replicas: 3
```

#### Template

The `template` section defines the pod template used to create the pods for the Deployment. It includes details like containers, volumes, and other configurations.

#### Containers

Containers are the individual units of work within a pod. Each container runs a specific application or service.

```yaml
spec:
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-container
        image: my-image
        ports:
        - containerPort: 80
```

#### Volumes

Volumes provide a way to store and share data between containers in the same pod or across different pods.

### Strategy

The `strategy` section defines how updates are handled for the Deployment, including rolling updates and rollbacks.

#### Rolling Update

A rolling update is a process that gradually replaces existing replicas with new ones while minimizing downtime.

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 0
```

#### Max Surge and Max Unavailable

- `maxSurge` defines the maximum number of pods that can be created above the desired replica count during an update.
- `maxUnavailable` specifies the maximum number of pods that can be unavailable (not ready or out of service) during an update.

### Status

The `status` section provides information about the current state of the Deployment, including the number of available replicas and updates in progress.

```yaml
status:
  availableReplicas: 3
  updatedReplicas: 0
```

## Conclusion

Understanding the structure and components of a Kubernetes Deployment is essential for managing applications effectively on the platform. By following best practices and leveraging features like rolling updates, you can ensure smooth deployments and minimize downtime.

[source: kubernetes-operations/skills/k8s-manifest-generator/references/deployment-spec.md]