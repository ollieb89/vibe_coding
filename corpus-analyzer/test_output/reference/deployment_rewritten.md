---
title: Deployment Reference
source: skills/loki-mode/references/deployment.md
---

# Deployment Strategies and Implementations

This document provides an overview of various deployment strategies and their implementations for popular cloud platforms.

## AWS Elastic Beanstalk

### Cloud Formation Template (CFN)
```hcl
Resources:
  MyAppEnvironment:
    Type: 'AWS::ElasticBeanstalk::Environment'
    Properties:
      ApplicationName: my-app
      EnvironmentName: production
      SolutionStackName: '64bit Amazon Linux 2 v3.0.1 running Node.js'
      VersionLabel: 'prod-v1'
      OptionSettings:
        - PropertyName: 'AWSEBAutoScalingGroupMinSize'
          Value: '1'
        - PropertyName: 'AWSEBAutoScalingGroupMaxSize'
          Value: '3'
```

### Blue-Green Deployment (ALB)
```bash
# Deploy green
aws ecs update-service --cluster app --service app-green --task-definition app:NEW_VERSION

# Wait for stability
aws ecs wait services-stable --cluster app --services app-green

# Run smoke tests
curl -f https://green.app.example.com/health

# Switch traffic (update target group weights)
aws elbv2 modify-listener-rule \
  --rule-arn [user-defined] \
  --actions '[{"Type":"forward","TargetGroupArn":"'[user-defined]'",
```

## Google Cloud Platform (GCP)

### Cloud Run
```bash
# Create resource group
gcloud projects create my-project

# Deploy container
gcloud run deploy app --image gcr.io/my-project/app:latest
```

### Kubernetes (Helm Chart)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
        - name: app
          image: app:latest
          ports:
            - containerPort: 3000
          env:
            - name: NODE_ENV
              value: production
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
```

## Azure Kubernetes Service (AKS)

### Deployment YAML
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
        - name: app
          image: app:latest
          ports:
            - containerPort: 3000
          env:
            - name: NODE_ENV
              value: production
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
```

## References
- [source: skills/loki-mode/references/deployment.md](https://github.com/loki-mode/skills/blob/master/references/deployment.md)