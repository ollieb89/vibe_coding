---
title: Kubernetes Service Specification Reference
source: kubernetes-operations/skills/k8s-manifest-generator/references/service-spec.md
---

# Kubernetes Service Specification Guide

This guide provides an overview of creating and configuring Kubernetes services, focusing on best practices for service types, selectors, named ports, session affinity, traffic policies, load balancing, network policies, and a production checklist.

## Table of Contents
1. [Introduction](#introduction)
2. [Service Types](#service-types)
3. [Selectors](#selectors)
4. [Named Ports](#named-ports)
5. [Session Affinity](#session-affinity)
6. [External Traffic Policy](#external-traffic-policy)
7. [Load Balancer Annotations](#load-balancer-annotations)
8. [Source IP Restriction](#source-ip-restriction)
9. [Health Check Configuration](#health-check-configuration)
10. [Monitoring Annotations](#monitoring-annotations)
11. [Network Policies](#network-policies)
12. [Production Checklist](#production-checklist)
13. [Performa Instructions](#performance-instructions)

## Introduction
Kubernetes services are essential for exposing and managing pods within a cluster. This guide aims to help you create and configure Kubernetes services effectively, focusing on best practices and common patterns.

## Service Types
Choose the appropriate service type based on your exposure needs:
- **ClusterIP**: Internal service accessible only within the cluster
- **NodePort**: Exposes the service on each node's IP at a static port
- **LoadBalancer**: Provides an external load balancer to distribute traffic
- **ExternalName**: Maps a DNS name to an external service
- **Headless**: Returns pod IPs instead of a single virtual IP (for StatefulSets)

## Selectors
Use consistent labels and selectors across Deployments and Services for proper routing.

## Named Ports
Named ports provide clarity when defining multiple ports in a service, making it easier to reference them elsewhere.

## Session Affinity
Configure session affinity (stickiness) for stateful applications to ensure consistent user sessions.

## External Traffic Policy
Set the external traffic policy to `Local` to preserve IP addresses for better routing and observability.

## Load Balancer Annotations
Add load balancer annotations when using a `LoadBalancer` service type, such as AWS NLB or GCE LB.

## Source IP Restriction
Restrict source IP ranges for public services to enhance security.

## Health Check Configuration
Configure health checks to ensure the readiness and liveness of your services.

## Monitoring Annotations
Add monitoring annotations like Prometheus scrape configuration for observability.

## Network Policies
Implement network policies to control traffic to your services, enhancing security within your cluster.

## Production Checklist
- Service type appropriate for use case
- Selector matches pod labels
- Named ports used for clarity
- Session affinity configured if needed
- Traffic policy set appropriately
- Load balancer annotations configured (if applicable)
- Source IP ranges restricted (for public services)
- Health check configuration validated
- Monitoring annotations added
- Network policies defined

## Performance Instructions
1. Improve structure and clarity
2. Keep all code blocks exactly as-is (verbatim, do not summarize)
3. Add a citation [source: kubernetes-operations/skills/k8s-manifest-generator/references/service-spec.md] at the end
4. Ensure all headings follow a logical hierarchy (no skipping levels)
5. Expand any placeholder text like [user-defined] into helpful descriptions
6. Start with YAML frontmatter including title, description, and tags
7. Do NOT wrap the output in a markdown code block (output raw text)
8. Do not repeat these instructions in your response.

[source: kubernetes-operations/skills/k8s-manifest-generator/references/service-spec.md]