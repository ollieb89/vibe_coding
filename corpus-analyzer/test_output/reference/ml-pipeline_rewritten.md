---
type: reference
---

# Machine Learning Pipeline - Multi-Agent MLOps Orchestration

Design and implement a complete ML pipeline for [user-defined]

## Overview

This workflow orchestrates multiple specialized agents to build a production-ready ML pipeline following modern MLOps best practices. The approach emphasizes:

- **Phase-based coordination**: Each phase builds upon previous outputs, with clear handoffs between agents
- **Modern tooling integration**: MLflow/W&B for experiments, Feast/Tecton for features, KServe/Seldon for serving
- **Production-first mindset**: Every component designed for scale, monitoring, and reliability
- **Reproducibility**: Version control for data, models, and infrastructure
- **Continuous improvement**: Automated retraining, A/B testing, and drift detection

The multi-agent approach ensures each aspect is handled by domain experts:
- Data engineers handle ingestion and quality
- Data scientists design features and experiments
- ML engineers implement training pipelines
- MLOps engineers handle production deployment
- Observability engineers ensure monitoring

## Configuration Options

- `experiment_tracking`: mlflow | wandb | neptune | clearml
- `feature_store`: feast | tecton | databricks | custom
- `serving_platform`: kserve | seldon | torchserve | triton
- `orchestration`: kubeflow | airflow | prefect | dagster
- `cloud_provider`: aws | azure | gcp | multi-cloud
- `deployment_mode`: realtime | batch | streaming | hybrid
- `monitoring_stack`: prometheus | datadog | newrelic | custom

## Phase 1: Data & Requirements Analysis

<Task>
subagent_type: data-engineer
prompt: |
  Analyze and design data pipeline for ML system with requirements: [user-defined]

  Deliverables:
  1. Data source audit and ingestion strategy:
     - Source systems and connection patterns
     - Schema validation using Pydantic/Great Expectations
     - Data versioning with DVC or lakeFS
     - Incremental loading and CDC strategies

  2. Data quality framework:
     - Profiling and statistics generation
     - Anomaly detection rules
     - Data lineage tracking
     - Quality gates and SLAs

  3. Storage architecture:
     - Raw/processed/feature layers
     - Partitioning strategy
     - Retention policies
     - Cost optimization

  Provide implementation code for critical components and integration patterns.
</Task>

<Task>
subagent_type: data-scientist
prompt: |
  Design feature engineering and model requirements for: [user-defined]
  Using data architecture from: {phase1.data-engineer.output}

  Deliverables:
  1. Feature engineering pipeline:
     - Transformation specifications
     - Feature store schema (Feast/Tecton)
     - Statistical validation rules
     - Handling strategies for missing data/outliers

  2. Model requirements:
     - Algorithm selection rationale
     - Performance metrics and baselines
     - Training data requirements
     - Evaluation criteria and thresholds

  3. Experiment design:
     - Hypothesis and success metrics
     - A/B testing methodology
     - Sample size calculations
     - Bias detection approach

  Include feature transformation code and statistical validation logic.
</Task>

## Phase 2: Model Development & Training

<Task>
subagent_type: ml-engineer
prompt: |
  Implement training pipeline based on requirements: {phase1.data-scientist.output}
  Using data pipeline: {phase1.data-engineer.output}

  Build comprehensive training system:
  1. Training pipeline implementation:
     - Modular training code with clear interfaces
     - Hyperparameter optimization (Optuna/Ray Tune)
     - Distributed training support (Horovod/PyTorch DDP)
     - Cross-validation and ensemble strategies

  2. Experiment tracking setup:
     - MLflow/Weights & Biases integration
     - Metric logging and visualization
     - Artifact management (models, plots, data)
     - Automated experiment evaluation

  3. Model validation and testing:
     - Unit tests for model components
     - Integration tests for end-to-end pipeline
     - Performance benchmarking

</Task>

## Phase 3: Model Deployment & Serving

<Task>
subagent_type: mlops-engineer
prompt: |
  Deploy and manage the trained model in production:
  1. Containerize the model with required dependencies
  2. Configure the serving platform (kserve, seldon, torchserve, or triton)
  3. Implement automated deployment workflows using orchestration tools (kubeflow, airflow, prefect, or dagster)
  4. Monitor and manage model performance in production
</Task>

## Phase 4: Monitoring & Continuous Improvement

<Task>
subagent_type: observability-engineer
prompt: |
  Implement comprehensive monitoring for ML system deployed in: {phase3.mlops-engineer.output}

  Monitoring framework:
  1. Model performance monitoring:
     - Prediction accuracy tracking
     - Latency and throughput metrics
     - Feature importance shifts
     - Business KPI correlation

  2. Data and model drift detection:
     - Statistical drift detection (KS test, PSI)
     - Concept drift monitoring
     - Feature distribution tracking
     - Automated drift alerts and reports

  3. System observability:
     - Prometheus metrics for all components
     - Grafana dashboards for visualization
     - Distributed tracing with Jaeger/Zipkin
     - Log aggregation with ELK/Loki

  4. Alerting and automation:
     - PagerDuty/Opsgenie integration
     - Automated retraining triggers
     - Performance degradation workflows
     - Incident response runbooks

  5. Cost tracking:
     - Resource utilization metrics
     - Cost allocation by model/experiment
     - Optimization recommendations
     - Budget alerts and controls

  Deliver monitoring configuration, dashboards, and alert rules.
</Task>

## Final Deliverables

Upon completion, the orchestrated pipeline will provide:
- End-to-end ML pipeline with full automation
- Comprehensive documentation and runbooks
- Production-ready infrastructure as code
- Complete monitoring and alerting system
- CI/CD pipelines for continuous improvement
- Cost optimization and scaling strategies
- Disaster recovery and rollback procedures

[source: machine-learning-ops/commands/ml-pipeline.md]