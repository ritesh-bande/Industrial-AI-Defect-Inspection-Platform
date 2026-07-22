# Production Deployment Guide

This guide details instructions for packaging, containerizing, and deploying VisionInspect AI to AWS (Elastic Container Service / EKS) and Azure (Container Apps / AKS).

---

## 1. Local Containerized Run

Verify the system runs in containers before deploying to the cloud:
1. **Navigate to the docker folder**:
   ```bash
   cd docker
   ```
2. **Launch all services in detached mode**:
   ```bash
   docker-compose up --build -d
   ```
3. **Verify running containers**:
   ```bash
   docker-compose ps
   ```
   - **Frontend**: [http://localhost:3000](http://localhost:3000)
   - **Backend API**: [http://localhost:8000](http://localhost:8000)
   - **Nginx Proxy Gate**: [http://localhost:80](http://localhost:80)

---

## 2. AWS (Elastic Container Service) Deployment

We recommend using **AWS ECS Fargate** for serverless container workloads:

1. **Build and push images to AWS Elastic Container Registry (ECR)**:
   ```bash
   # Log in to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com

   # Tag and Push Backend
   docker build -t visioninspect-backend -f Dockerfile.backend ..
   docker tag visioninspect-backend:latest <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/visioninspect-backend:latest
   docker push <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/visioninspect-backend:latest

   # Tag and Push Frontend
   docker build -t visioninspect-frontend -f Dockerfile.frontend ../frontend
   docker tag visioninspect-frontend:latest <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/visioninspect-frontend:latest
   docker push <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/visioninspect-frontend:latest
   ```

2. **Create Database resources**:
   - Provision an **Amazon RDS PostgreSQL** instance.
   - Provision an **Amazon DocumentDB** (MongoDB compatible) cluster.
   - Inject Database Connection strings via **AWS Secrets Manager** to the ECS Task definition.

3. **Deploy Task Definitions**:
   - Configure memory (2GB RAM minimum for PyTorch classification inference) and CPU sizes.
   - Configure ALB (Application Load Balancer) to route Traffic to Next.js on port 3000 and FastAPI endpoints on port 8000.

---

## 3. Azure (Container Apps) Deployment

Azure Container Apps provide a serverless environment for running container microservices:

1. **Create Azure Container Registry (ACR)**:
   ```bash
   az acr create --resource-group visioninspect-rg --name visioninspectacr --sku Basic
   az acr login --name visioninspectacr
   ```

2. **Build and push images**:
   ```bash
   az acr build --registry visioninspectacr --image visioninspect-backend:latest -f Dockerfile.backend ..
   az acr build --registry visioninspectacr --image visioninspect-frontend:latest -f Dockerfile.frontend ../frontend
   ```

3. **Provision Databases**:
   - Create **Azure Database for PostgreSQL**.
   - Create **Azure Cosmos DB** (configured with MongoDB API).

4. **Deploy Containers**:
   - Set up Container App Environment linking backend and frontend with ingress enabled.
