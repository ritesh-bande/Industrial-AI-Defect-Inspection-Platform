# Production Deployment & Cloudflare Guide

This guide details instructions for packaging, containerizing, and deploying **VisionInspect AI** using Docker Compose, AWS/Azure, and Cloudflare Tunnels (`cloudflared`).

---

## 1. Local Containerized Run (Docker Compose)

Verify the system runs in containers before deploying:

1. **Copy Environment Template**:
   ```bash
   cp .env.example .env
   ```

2. **Launch all services**:
   ```bash
   docker compose build
   docker compose up -d
   ```

3. **Verify running containers**:
   ```bash
   docker compose ps
   ```
   - **Frontend Console**: [http://localhost:3000](http://localhost:3000)
   - **Backend API**: [http://localhost:8000](http://localhost:8000)
   - **OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 2. Cloudflare Tunnel + Docker Integration (`cloudflared`)

Cloudflare Tunnel securely connects your Docker containers directly to Cloudflare without opening public inbound router ports or configuring static public IP addresses.

### How to Configure:

1. **Create a Cloudflare Tunnel**:
   - Log into [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/).
   - Navigate to **Networks** -> **Tunnels** -> **Add a Tunnel**.
   - Choose **Cloudflared** as the connector type and name your tunnel (e.g., `visioninspect-factory-01`).

2. **Obtain your Tunnel Token**:
   - Copy the generated base64 `token` string provided in the Cloudflare command prompt.

3. **Set the Token in your `.env`**:
   ```env
   CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiZ...your_full_token_here...
   ```

4. **Map Public Hostnames in Cloudflare Dashboard**:
   - Add **Public Hostname**: `inspect.yourcompany.com` -> Service Type: `HTTP` -> URL: `frontend:3000`
   - Add **Public Hostname**: `api.yourcompany.com` -> Service Type: `HTTP` -> URL: `backend:8000`

5. **Start Docker with Cloudflare Service**:
   ```bash
   docker compose up -d cloudflared
   ```
   Your inspection dashboard is now accessible globally via `https://inspect.yourcompany.com` with enterprise SSL, DDoS protection, and Zero Trust access!

---

## 3. AWS (Elastic Container Service) Deployment

We recommend using **AWS ECS Fargate** for serverless container workloads:

1. **Build and push images to AWS Elastic Container Registry (ECR)**:
   ```bash
   # Log in to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com

   # Tag and Push Backend
   docker build -t visioninspect-backend -f backend/Dockerfile .
   docker tag visioninspect-backend:latest <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/visioninspect-backend:latest
   docker push <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/visioninspect-backend:latest

   # Tag and Push Frontend
   docker build -t visioninspect-frontend -f frontend/Dockerfile ./frontend
   docker tag visioninspect-frontend:latest <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/visioninspect-frontend:latest
   docker push <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/visioninspect-frontend:latest
   ```

2. **Database & Secret Resources**:
   - Provision **Amazon RDS PostgreSQL** & **Amazon DocumentDB** (MongoDB compatible).
   - Inject connection strings securely via **AWS Secrets Manager**.

---

## 4. Azure (Container Apps) Deployment

1. **Build and push images**:
   ```bash
   az acr build --registry visioninspectacr --image visioninspect-backend:latest -f backend/Dockerfile .
   az acr build --registry visioninspectacr --image visioninspect-frontend:latest -f frontend/Dockerfile ./frontend
   ```

2. **Provision Databases**:
   - Create **Azure Database for PostgreSQL** & **Azure Cosmos DB** (MongoDB API).
